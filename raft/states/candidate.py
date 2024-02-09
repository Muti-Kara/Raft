from concurrent.futures import ThreadPoolExecutor
import rpyc

from .rpc_models import AppendEntry, RequestVote, RequestVoteResponse
from .state import State
import config


class Candidate(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.MIN_ELECTION_TIMEOUT, config.MAX_ELECTION_TIMEOUT)

        self._node.data.current_term += 1
        self._node.data.voted_for = self._node.id
        self.voters = set([self._node.id])
        self.vote_target = (len(self._node.peers) // 2) + 1

        with ThreadPoolExecutor() as executor:
            for peer_id, peer_addr in self._node.peers.items():
                executor.submit(self.broadcast_rpc, peer_id, peer_addr)

    def on_expire(self):
        self._change_state(Candidate)

    def on_append_entry(self, ae: AppendEntry):
        if self._node.data.current_term > ae.term:
            return False
        self.become_follower()
        return self._node.state.on_append_entry(ae)

    def on_request_vote(self, rv: RequestVote):
        if self._node.data.current_term >= rv.term:
            return False
        self.become_follower(rv.term)
        return True

    def on_request_vote_callback(self, res: RequestVoteResponse):
        if self._node.data.current_term < res.term:
            self.become_follower(res.term)
        elif res.vote_granted:
            self.voters.add(res.id)
            if len(self.voters) >= self.vote_target:
                self.become_leader()

    def broadcast_rpc(self, peer_id, peer_addr):
        import pickle
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