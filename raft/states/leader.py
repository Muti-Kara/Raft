from concurrent.futures import ThreadPoolExecutor
import pickle
import rpyc

from .rpc_models import AppendEntry, RequestVote, AppendEntryResponse
from .state import State
import config


class Leader(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.HEARTBEAT_INTERVAL, config.HEARTBEAT_INTERVAL)
        self.next_idx = {id: len(self._node.data.logs.logs) for id, _ in self._node.peers.items()}
        self.match_idx = {id: 0 for id, _ in self._node.peers.items()}
        self._node.current_leader["id"] = self._node.id

    def on_expire(self):
        self._timer.reset()
        with ThreadPoolExecutor() as executor:
            for peer_id, peer_addr in self._node.peers.items():
                executor.submit(self.broadcast_rpc, peer_id, peer_addr)

    def on_append_entry(self, ae: AppendEntry):
        if self._node.data.current_term >= ae.term:
            return False
        self.become_follower(ae.term)
        return True

    def on_append_entry_callback(self, res: AppendEntryResponse):
        if res.success != -2:
            self.next_idx[res.id] = res.success + 1
            self.match_idx[res.id] = max(res.success, self.match_idx[res.id])
            sorted_match_index = sorted(self.match_idx.values())
            self._node.commit_index = max(
                self._node.commit_index,
                sorted_match_index[len(sorted_match_index)//2]
            )
            self._node.apply_commands()
        else:
            if self._node.data.current_term < res.term:
                return self.become_follower(res.term)
            else:
                self.next_idx[res.id] = 1
                self.match_idx[res.id] = 1

    def on_request_vote(self, rv: RequestVote):
        if self._node.data.current_term >= rv.term:
            return False
        self.become_follower(rv.term)
        return True

    def broadcast_rpc(self, peer_id, peer_addr):
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