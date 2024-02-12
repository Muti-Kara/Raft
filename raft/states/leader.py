import pickle
import rpyc

from raft.utils.models import AppendEntry, RequestVote, AppendEntryResponse
from .state import State


class Leader(State):
    """
    The Leader state represents the leader node in the Raft consensus algorithm.

    As a Leader, the node is responsible for managing the replication of log entries across the cluster.
    It sends periodic AppendEntries messages to followers to maintain its leadership status.

    Attributes:
        node (RaftNode): The Raft node associated with the state.
        next_idx (dict): A dictionary containing the index of the next log entry to send to each follower.
        match_idx (dict): A dictionary containing the index of the highest log entry known to be replicated on each follower.
    """

    def __init__(self, node) -> None:
        """
        Initialize the Leader state.

        Args:
            node (RaftNode): The Raft node associated with the state.
        """
        super().__init__(node, node.cluster.heartbeat_interval, node.cluster.heartbeat_interval)
        
        # Initialize dictionaries to keep track of next and match indexes for each peer.
        self.next_idx = {peer.id: len(self._node.data.logs.logs) for peer in self._node.peers.values()}
        self.match_idx = {peer.id: 0 for peer in self._node.peers.values()}
        
        # Set the current node as the leader.
        self._node.current_leader = self._node.id

    def on_expire(self):
        """
        Handle timeout expiration.

        When the heartbeat timeout expires, the leader sends AppendEntries messages to followers to maintain its status.
        """
        self._timer.reset()
        self.broadcast_rpc()

    def on_append_entry(self, ae: AppendEntry):
        """
        Handle an AppendEntries request received from a Leader.

        Args:
            ae (AppendEntry): The AppendEntries request received from a Leader.

        Returns:
            bool: False, indicating that the request was rejected since the Leader cannot receive AppendEntries.
        """
        # If the leader receives an AppendEntries request with a higher term, it reverts to being a follower.
        if self._node.data.current_term < ae.term:
            self.become_follower(ae.term, ae.term)
            return self._node.state.on_append_entry(ae)

        # Otherwise, the AppendEntries request is ignored since the current leader is still valid.
        return False

    def on_append_entry_callback(self, res: AppendEntryResponse):
        """
        Handle the response to an AppendEntries RPC.

        Args:
            res (AppendEntryResponse): The response to the AppendEntries RPC.

        If the response acknowledges the log entry, update next and match indexes accordingly.
        Update the commit index and apply commands if necessary.
        """
        # If the response indicates failure due to a higher term, the leader reverts to being a follower.
        if res.acknowledge is False:
            if self._node.data.current_term < res.term:
                return self.become_follower(res.term)
            else:
                # Decrement the next index for the follower to retry the failed AppendEntries RPC.
                self.next_idx[res.id] -= 1
        else:
            # Update next and match indexes based on the acknowledgment from the follower.
            self.next_idx[res.id] = res.acknowledge + 1
            self.match_idx[res.id] = max(res.acknowledge, self.match_idx[res.id])
            
            # Calculate the commit index based on the majority of match indexes.
            sorted_match_index = sorted(self.match_idx.values())
            self._node.commit_index = max(
                self._node.commit_index,
                sorted_match_index[len(sorted_match_index)//2]
            )
            
            # Apply commands to the state machine up to the commit index.
            self._node.apply_commands()

    def on_request_vote(self, rv: RequestVote):
        """
        Handle a RequestVote RPC received from a Candidate.

        Args:
            rv (RequestVote): The RequestVote RPC received from a Candidate.

        Returns:
            bool: True, indicating that the vote is granted since the Leader does not participate in elections.
        """
        # If the Leader receives a RequestVote RPC with a higher term, it reverts to being a follower.
        if self._node.data.current_term < rv.term:
            self.become_follower(rv.term)
            return self._node.state.on_request_vote(rv)
        
        # Otherwise, the vote is not granted since the Leader does not participate in elections.
        return False

    def call_rpc(self, peer_id, peer_addr):
        """
        Send an AppendEntries RPC to a follower node.

        Args:
            peer_id (str): The ID of the follower node.
            peer_addr (tuple): The address of the follower node.

        Returns:
            None
        """
        try:
            rpyc.connect(*peer_addr).root.append_entry(
                pickle.dumps(AppendEntry(
                    term=self._node.data.current_term,
                    leader=self._node.id,
                    previous_log_index=self.next_idx[peer_id] - 1,
                    previous_log_term=self._node.data.logs.logs[self.next_idx[peer_id] - 1].term,
                    leader_commit=self._node.commit_index,
                    entries=self._node.data.logs.logs[self.next_idx[peer_id]:]
                )),
                self._node.append_entry_callback
            )
        except:
            return