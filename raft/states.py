import threading
import random
import time

from raft.data import AppendEntry, RequestVote
import raft.config as rc


class State():
    def __init__(self, node) -> None:
        self.node = node
        self._set_timer()

    def _set_timer(self, interval: int = 150):
        self.timer = threading.Timer(random.randint(interval, 2 * interval) / 100, self.on_expire)
        self.timer.start()

    def on_expire(self):
        raise NotImplementedError

    def on_append_entry(self, append_entry):
        raise NotImplementedError

    def on_request_vote(self, request_vote):
        raise NotImplementedError


class Follower(State):
    def __init__(self, node) -> None:
        super().__init__(node)
        print(f"Node {rc.NODE_ID} has entered Follower State", flush=True)

    def on_expire(self):
        self.node.state = Candidate(self.node)

    def on_append_entry(self, append_entry):
        self.timer.cancel()
        self._set_timer()

    def on_request_vote(self, request_vote):
        return 1


class Candidate(State):
    def __init__(self, node) -> None:
        super().__init__(node)
        self.vote_count = 1
        self.vote_target = (len(rc.PEERS) / 2) + 1
        print(f"Node {rc.NODE_ID} has entered Candidate State", flush=True)

        for id, peer in self.node.get_peers():
            rv = peer.request_vote(RequestVote(peer=rc.NODE_ID))
            if rv == 1:
                print(f"Node {id} has voted Node {rc.NODE_ID}", flush=True)
                self.vote_count += 1
                if self.vote_count > self.vote_target:
                    self.timer.cancel()
                    self.node.state = Leader(self.node)
            else:
                print(f"Node {id} hasn't vote Node {rc.NODE_ID}", flush=True)

    def on_expire(self):
        self.node.state = Candidate(self.node)

    def on_append_entry(self, append_entry):
        self.timer.cancel()
        self.node.state = Follower(self.node)

    def on_request_vote(self, request_vote):
        return 0


class Leader(State):
    def __init__(self, node) -> None:
        self.node = node
        self._set_timer(interval=15)
        print(f"Node {rc.NODE_ID} has entered Leader State", flush=True)

    def on_expire(self):
        for id, peer in self.node.get_peers():
            peer.append_entry(AppendEntry(leader=rc.NODE_ID))
        self._set_timer(interval=15)

    def on_append_entry(self, append_entry):
        return

    def on_request_vote(self, request_vote):
        return 0