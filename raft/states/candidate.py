import pickle
import rpyc

from raft.utils.models import AppendEntry, RequestVote, RequestVoteResponse
from .state import State


class Candidate(State):
    """
    Represents the Candidate state in the Raft consensus algorithm.
    Inherits from the State base class.
    """
    def __init__(self, node) -> None:
        """
        Initializes a Candidate instance.

        Args:
            node: The Raft node associated with this state.
        """
        super().__init__(node, node.cluster.min_election_timeout, node.cluster.max_election_timeout)

        # Increment current term and vote for self
        self._node.data.current_term += 1
        self._node.data.voted_for = self._node.id
        # Keep track of voters and calculate vote target
        self.voters = set([self._node.id])
        # Broadcast RequestVote RPCs to peers
        self.broadcast_rpc()

    def on_expire(self):
        """
        Callback method triggered upon state transition timeout.
        Transitions back to candidate state.
        """
        self.become_candidate()

    def on_append_entry(self, ae: AppendEntry):
        """
        Handles incoming AppendEntry RPC messages.

        Args:
            ae (AppendEntry): The AppendEntry message.

        Returns:
            bool or int: Returns False if the message is rejected, otherwise delegates to follower's on_append_entry method.
        """
        # Candidate becomes follower if it receives a valid AppendEntry message
        if self._node.data.current_term > ae.term:
            return False
        self.become_follower()
        return self._node.state.on_append_entry(ae)

    def on_request_vote(self, rv: RequestVote):
        """
        Handles incoming RequestVote RPC messages.

        Args:
            rv (RequestVote): The RequestVote message.

        Returns:
            bool: True if the vote is granted, False otherwise.
        """
        # Candidate becomes follower if it receives a valid RequestVote message with higher term
        if self._node.data.current_term >= rv.term:
            return False
        self.become_follower(rv.term)
        return True

    def on_request_vote_callback(self, res: RequestVoteResponse):
        """
        Handles responses to RequestVote RPC messages.

        Args:
            res (RequestVoteResponse): The RequestVote response.

        Checks if the vote is granted and if the candidate has received enough votes to become a leader.
        """
        # Candidate becomes follower if it receives a response with a higher term
        if self._node.data.current_term < res.term:
            self.become_follower(res.term)
        elif res.vote_granted:
            # Add voter to set and become leader if enough votes are received
            self.voters.add(res.id)
            if len(self.voters) >= self._node.cluster.vote_target:
                self.become_leader()

    def call_rpc(self, peer_id, peer_addr):
        """
        Broadcasts RequestVote RPCs to peers.

        Args:
            peer_id: The ID of the peer.
            peer_addr: The address of the peer.
        """
        try:
            # Attempt RPC connection and request vote
            rpyc.connect(*peer_addr).root.request_vote(
                pickle.dumps(RequestVote(
                    term=self._node.data.current_term,
                    candidate_id=self._node.id,
                    last_log_index=len(self._node.data.logs.logs) - 1,
                    last_log_term=self._node.data.logs.logs[-1].term,
                )),
                self._node.request_vote_callback
            )
        except:
            return
