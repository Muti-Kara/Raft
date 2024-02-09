from .rpc_models import AppendEntry, RequestVote
from raft.utils.logs import LogList
from .state import State
import config


class Follower(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.MIN_ELECTION_TIMEOUT, config.MAX_ELECTION_TIMEOUT)

    def on_expire(self):
        self.become_candidate()

    def on_append_entry(self, ae: AppendEntry):
        if self._node.data.current_term > ae.term:
            return -2

        self._timer.reset()
        self._node.set_leader(ae.leader)

        if self._node.data.current_term < ae.term:
            self._node.data.current_term = ae.term

        if ae.previous_log_index >= len(self._node.data.logs.logs):
            return -2
        if self._node.data.logs.logs[ae.previous_log_index].term != ae.previous_log_term:
            return -2
        return self.accept_logs(ae)

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

    def accept_logs(self, ae: AppendEntry):
        if ae.entries:
            self._node.data.logs.add_logs(
                ae.previous_log_index + 1,
                LogList(logs=ae.entries)
            )
            self._node.commit_index = ae.leader_commit
            self._node.apply_commands()
        return len(self._node.data.logs.logs) - 1