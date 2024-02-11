from raft.utils.models import AppendEntry, RequestVote, LogList
from .state import State


class Follower(State):
    def __init__(self, node) -> None:
        super().__init__(node, node.cluster.min_election_timeout, node.cluster.max_election_timeout)

    def on_expire(self):
        self.become_candidate()

    def on_append_entry(self, ae: AppendEntry):
        if self._node.data.current_term > ae.term:
            return False
        self._timer.reset()
        self._node.set_leader(ae.leader)
        if self._node.data.current_term < ae.term:
            self._node.data.current_term = ae.term
        if ae.previous_log_index >= len(self._node.data.logs.logs):
            return False
        if self._node.data.logs.logs[ae.previous_log_index].term != ae.previous_log_term:
            return False

        if ae.entries:
            self._node.data.logs.add_logs(ae.previous_log_index + 1, LogList(logs=ae.entries))
        if self._node.commit_index < ae.leader_commit:
            self._node.commit_index = ae.leader_commit
            self._node.apply_commands()
        return len(self._node.data.logs.logs) - 1

    def on_request_vote(self, rv: RequestVote):
        if self._node.data.current_term < rv.term:
            self._node.data.current_term = rv.term
            self._node.data.voted_for = -1
        if self._node.data.current_term > rv.term:
            return False
        if self._node.data.logs.logs[-1].term > rv.last_log_term:
            return False
        if len(self._node.data.logs.logs) - 1 > rv.last_log_index:
            return False
        if self._node.data.voted_for != -1:
            return False
        self._node.data.voted_for = rv.candidate_id
        self._timer.reset()
        return True