from .rpc_models import AppendEntry, RequestVote
from raft.utils.logs import LogList
from .state import State
import config


class Follower(State):
    """
    Represents the Follower state in the Raft consensus algorithm.
    Inherits from the State base class.
    """
    def __init__(self, node) -> None:
        """
        Initializes a Follower instance.

        Args:
            node: The Raft node associated with this state.
        """
        super().__init__(node, config.MIN_ELECTION_TIMEOUT, config.MAX_ELECTION_TIMEOUT)

    def on_expire(self):
        """
        Callback method triggered upon state transition timeout.
        Transitions to candidate state.
        """
        self.become_candidate()

    def on_append_entry(self, ae: AppendEntry):
        """
        Handles incoming AppendEntry RPC messages.

        Args:
            ae (AppendEntry): The AppendEntry message.

        Returns:
            bool or int: Returns False if the message is rejected, otherwise returns the log index.
        """
        # Follower rejects if leader's term is less than ours
        if self._node.data.current_term > ae.term:
            return False

        # Reset timer upon receiving a valid AppendEntry message
        self._timer.reset()
        
        # Set leader information
        self._node.set_leader(ae.leader)
        # Update current term if necessary
        if self._node.data.current_term < ae.term:
            self._node.data.current_term = ae.term

        # Check if previous log entry matches leader's log
        if ae.previous_log_index >= len(self._node.data.logs.logs):
            return False
        if self._node.data.logs.logs[ae.previous_log_index].term != ae.previous_log_term:
            return False

        # Add new log entries and update commit index
        if ae.entries:
            self._node.data.logs.add_logs(ae.previous_log_index + 1, LogList(logs=ae.entries))
            self._node.commit_index = ae.leader_commit
            self._node.apply_commands()
        return len(self._node.data.logs.logs) - 1

    def on_request_vote(self, rv: RequestVote):
        """
        Handles incoming RequestVote RPC messages.

        Args:
            rv (RequestVote): The RequestVote message.

        Returns:
            bool: True if the vote is granted, False otherwise.
        """
        # Update current term and reset voted for candidate if necessary
        if self._node.data.current_term < rv.term:
            self._node.data.current_term = rv.term
            self._node.data.voted_for = -1

        # Follower rejects if candidate's term is less than ours
        if self._node.data.current_term > rv.term:
            return False
        # Follower rejects if candidate's last log term is outdated
        if self._node.data.logs.logs[-1].term > rv.last_log_term:
            return False
        # Follower rejects if candidate's last log index is behind ours
        if len(self._node.data.logs.logs) - 1 > rv.last_log_index:
            return False
        # Follower rejects if it already voted for another candidate
        if self._node.data.voted_for != -1:
            return False

        # Grant vote and reset timer
        self._node.data.voted_for = rv.candidate_id
        self._timer.reset()
        return True