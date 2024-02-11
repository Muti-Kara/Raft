import pickle
import rpyc

from raft.utils.models import AppendEntry, RequestVote, AppendEntryResponse
from .state import State


class Leader(State):
    def __init__(self, node) -> None:
        super().__init__(node, node.cluster.heartbeat_interval, node.cluster.heartbeat_interval)
        self.next_idx = {peer.id: len(self._node.data.logs.logs) for peer in self._node.peers.values()}
        self.match_idx = {peer.id: 0 for peer in self._node.peers.values()}
        self._node.current_leader["id"] = self._node.id

    def on_expire(self):
        self._timer.reset()
        self.broadcast_rpc()

    def on_append_entry(self, ae: AppendEntry):
        if self._node.data.current_term >= ae.term:
            return False
        self.become_follower(ae.term)
        return self._node.state.on_append_entry(ae)

    def on_append_entry_callback(self, res: AppendEntryResponse):
        if res.acknowledge is False:
            if self._node.data.current_term < res.term:
                return self.become_follower(res.term)
            else:
                self.next_idx[res.id] -= 1
        else:
            self.next_idx[res.id] = res.acknowledge + 1
            self.match_idx[res.id] = max(res.acknowledge, self.match_idx[res.id])
            sorted_match_index = sorted(self.match_idx.values())
            self._node.commit_index = max(
                self._node.commit_index,
                sorted_match_index[len(sorted_match_index)//2]
            )
            self._node.apply_commands()

    def on_request_vote(self, rv: RequestVote):
        if self._node.data.current_term >= rv.term:
            return False
        self.become_follower(rv.term)
        return True

    def call_rpc(self, peer_id, peer_addr):
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