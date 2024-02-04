import threading
import random

import raft.config as rc


class State():
    def __init__(self, node) -> None:
        self.node = node
        self.interval = 150
        self.timer = threading.Timer(random.randint(self.interval, 2 * self.interval) / 100, self.on_expire)
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
        print(f"Leader {append_entry['leader']} sent append entry", flush=True)
        self.timer.cancel()
        self.timer = threading.Timer(random.randint(self.interval, 2 * self.interval) / 100, self.on_expire)
        self.timer.start()

    def on_request_vote(self, request_vote):
        print(f"Node {request_vote['peer']} requested vote: Positive", flush=True)
        return 1


class Candidate(State):
    def __init__(self, node) -> None:
        super().__init__(node)
        self.vote_count = 1
        self.vote_target = (len(rc.PEERS) / 2) + 1
        print(f"Node {rc.NODE_ID} has entered Candidate State", flush=True)

        for peer in self.node.get_peers():
            self.vote_count += peer.request_vote(self.node.request_vote_dict())
            if self.vote_count > self.vote_target:
                self.timer.cancel()
                self.node.state = Leader(self.node)

    def on_expire(self):
        self.node.state = Candidate(self.node)

    def on_append_entry(self, append_entry):
        print(f"Leader {append_entry['leader']} sent append entry", flush=True)
        self.timer.cancel()
        self.node.state = Follower(self.node)

    def on_request_vote(self, request_vote):
        print(f"Node {request_vote['peer']} requested vote: Negative", flush=True)
        return 0


class Leader(State):
    def __init__(self, node) -> None:
        self.node = node
        self.interval = 15
        self.timer = threading.Timer(random.randint(self.interval, 2 * self.interval) / 100, self.on_expire)
        self.timer.start()        
        print(f"Node {rc.NODE_ID} has entered Leader State", flush=True)

    def on_expire(self):
        for peer in self.node.get_peers():
            peer.append_entry(self.node.append_entry_dict())
        self.timer = threading.Timer(random.randint(self.interval, 2 * self.interval) / 100, self.on_expire)
        self.timer.start()

    def on_append_entry(self, append_entry):
        return

    def on_request_vote(self, request_vote):
        print(f"Node {request_vote['peer']} requested vote: Negative", flush=True)
        return 0