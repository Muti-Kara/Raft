import pickle
import rpyc

from raft.utils.models import AppendEntry, RequestVote, RequestVoteResponse
from .state import State


class Candidate(State):
    """
    The Candidate state represents a candidate node in the Raft consensus algorithm.

    As a Candidate, the node transitions to this state when it believes it may be the Leader.
    It starts a new election by requesting votes from other nodes in the cluster.
    If it receives votes from a majority of nodes, it transitions to the Leader state.
    Otherwise, it reverts back to the Follower state.

    Attributes:
        node (RaftNode): The Raft node associated with the state.
        voters (set): A set containing the IDs of the nodes that have voted for the candidate.
    """

    def __init__(self, node) -> None:
        """
        Initialize the Candidate state.

        Args:
            node (RaftNode): The Raft node associated with the state.
        """
        super().__init__(node, node.cluster.min_election_timeout, node.cluster.max_election_timeout)
        
        # Increment the current term and vote for self as a candidate.
        self._node.data.current_term += 1
        self._node.data.voted_for = self._node.id
        
        # Initialize a set to store the IDs of nodes that have voted for the candidate.
        self.voters = set([self._node.id])
        
        # Send request vote RPCs to other nodes in the cluster.
        self.broadcast_rpc()

    def on_expire(self):
        """
        Handle timeout expiration.

        When the election timeout expires, the candidate starts a new election by becoming a candidate again.
        """
        self.become_candidate()

    def on_append_entry(self, ae: AppendEntry):
        """
        Handle an AppendEntries request received from the Leader.

        Args:
            ae (AppendEntry): The AppendEntries request received from the Leader.

        Returns:
            bool: False, indicating that the request was rejected since the candidate is not the Leader.
        """
        if self._node.data.current_term > ae.term:
            return False

        # Transition to the Follower state since a valid AppendEntries request was received from the Leader.
        self.become_follower()
        return self._node.state.on_append_entry(ae)

    def on_request_vote(self, rv: RequestVote):
        """
        Handle a RequestVote RPC received from a Candidate.

        Args:
            rv (RequestVote): The RequestVote RPC received from a Candidate.

        Returns:
            bool: True if the vote is granted, False otherwise.
        """
        if self._node.data.current_term >= rv.term:
            return False

        # Transition to the Follower state and grant the vote since the candidate's term is outdated.
        self.become_follower(rv.term)
        return True

    def on_request_vote_callback(self, res: RequestVoteResponse):
        """
        Handle the response to a RequestVote RPC.

        Args:
            res (RequestVoteResponse): The response to the RequestVote RPC.

        """
        
        # If the candidate's term is less than the response term, it transitions to the Follower state.
        if self._node.data.current_term < res.term:
            self.become_follower(res.term)
        
        # If the vote is granted, it adds the voter to the set of voters.
        elif res.vote_granted:
            self.voters.add(res.id)
            
            # If the candidate receives votes from a majority of nodes, it transitions to the Leader state.
            if len(self.voters) >= self._node.cluster.vote_target:
                self.become_leader()

    def call_rpc(self, peer_id, peer_addr):
        """
        Send a RequestVote RPC to a peer node.

        Args:
            peer_id (str): The ID of the peer node.
            peer_addr (tuple): The address of the peer node.

        Returns:
            None
        """
        try:
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