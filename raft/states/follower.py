from raft.utils.models import AppendEntry, RequestVote, LogList
from .state import State


class Follower(State):
    """
    The Follower state represents a follower node in the Raft consensus algorithm.

    As a Follower, the node listens for communication from the Leader. It stays in this state
    as long as it receives valid AppendEntries or RequestVote messages from the current Leader.
    If it does not hear from the Leader within a certain time (election timeout), it transitions
    to the Candidate state and starts a new election.

    Attributes:
        node (RaftNode): The Raft node associated with the state.
    """

    def __init__(self, node) -> None:
        """
        Initialize the Follower state.

        Args:
            node (RaftNode): The Raft node associated with the state.
        """
        super().__init__(node, node.cluster.min_election_timeout, node.cluster.max_election_timeout)

    def on_expire(self):
        """
        Handle timeout expiration.

        When the election timeout expires, the Follower becomes a Candidate and starts a new election.
        """
        self.become_candidate()

    def on_append_entry(self, ae: AppendEntry):
        """
        Handle an AppendEntries request received from the Leader.

        Args:
            ae (AppendEntry): The AppendEntries request received from the Leader.

        Returns:
            int | bool: The index of the last log entry if the entry is successfully appended, 
                        False otherwise.
        """
        # If the term of the received AppendEntries is less than the current term, reject the request.
        if self._node.data.current_term > ae.term:
            return False

        # Reset the election timeout timer since valid communication is received from the Leader.
        self._timer.reset()

        # Set the Leader of the node based on the AppendEntries request.
        self._node.set_leader(ae.leader)

        # Update the current term if the received term is greater than the current term.
        if self._node.data.current_term < ae.term:
            self._node.data.current_term = ae.term

        # Check if the previous log entry exists in the log.
        if ae.previous_log_index >= len(self._node.data.logs.logs):
            return False

        # Check if the previous log entry's term matches the term provided in the AppendEntries request.
        if self._node.data.logs.logs[ae.previous_log_index].term != ae.previous_log_term:
            return False

        # Append new log entries to the log.
        if ae.entries:
            self._node.data.logs.add_logs(ae.previous_log_index + 1, LogList(logs=ae.entries))

        # Update the commit index if necessary and apply any newly committed commands.
        if self._node.commit_index < ae.leader_commit:
            self._node.commit_index = ae.leader_commit
            self._node.apply_commands()

        # Return the index of the last log entry.
        return len(self._node.data.logs.logs) - 1

    def on_request_vote(self, rv: RequestVote):
        """
        Handle a RequestVote RPC received from a Candidate.

        Args:
            rv (RequestVote): The RequestVote RPC received from a Candidate.

        Returns:
            bool: True if the vote is granted, False otherwise.
        """
        # If the term of the received RequestVote is greater than the current term, update the current term.
        if self._node.data.current_term < rv.term:
            self._node.data.current_term = rv.term
            self._node.data.voted_for = -1

        # If the term of the received RequestVote is less than the current term, reject the request.
        if self._node.data.current_term > rv.term:
            return False

        # If the term of the last log entry in the log is greater than the term provided in the RequestVote,
        # reject the request.
        if self._node.data.logs.logs[-1].term > rv.last_log_term:
            return False

        # If the index of the last log entry in the log is greater than the last log index provided in the RequestVote,
        # reject the request.
        if len(self._node.data.logs.logs) - 1 > rv.last_log_index:
            return False

        # If the node has already voted in this term, reject the request.
        if self._node.data.voted_for != -1:
            return False

        # Grant the vote, reset the election timeout timer, and record the vote.
        self._node.data.voted_for = rv.candidate_id
        self._timer.reset()
        return True