from concurrent.futures import ThreadPoolExecutor

from raft.utils.models import AppendEntry, RequestVote, AppendEntryResponse, RequestVoteResponse
from raft.utils.timer import FunctionTimer


class State:
    def __init__(self, node, min_timeout, max_timeout) -> None:
        from raft.node import RaftNode
        print(self.__class__.__name__, flush=True)
        self._node: RaftNode = node
        self._node.state = self
        self._timer = FunctionTimer(min_timeout, max_timeout, self.on_expire)

    def _change_state(self, NewState: 'State', new_term: int | None = None):
        if isinstance(self._node.state, NewState):
            return
        if new_term:
            self._node.data.current_term = new_term
        self._timer.stop()
        NewState(self._node)

    def become_follower(self, new_term: int | None = None):
        from .follower import Follower
        self._change_state(Follower, new_term)

    def become_candidate(self, new_term: int | None = None):
        from .candidate import Candidate
        self._change_state(Candidate, new_term)

    def become_leader(self, new_term: int | None = None):
        from .leader import Leader
        self._change_state(Leader, new_term)

    def on_expire(self):
        raise NotImplementedError

    def on_append_entry(self, ae: AppendEntry):
        raise NotImplementedError

    def on_append_entry_callback(self, res: AppendEntryResponse):
        return

    def on_request_vote(self, rv: RequestVote):
        raise NotImplementedError

    def on_request_vote_callback(self, res: RequestVoteResponse):
        return

    def broadcast_rpc(self):
        with ThreadPoolExecutor() as executor:
            for peer in self._node.peers.values():
                executor.submit(self.call_rpc, peer.id, peer.rpc_address)

    def call_rpc(self, peer_id, peer_addr):
        return