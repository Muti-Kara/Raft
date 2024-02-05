import threading
import random

import raft.config as rc


class State():
    def __init__(self, node) -> None:
        self.node = node
        self.interval = rc.ELECTION_TIMEOUT
        self._set_timer()

    def _set_timer(self):
        self.timer = threading.Timer(random.randint(self.interval, 2 * self.interval) / 1000, self.on_expire)
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

    def on_append_entry(self, current_term, append_entry):
        if current_term > append_entry["term"]:
            return {"term": current_term, "success": False}
        if current_term < append_entry["term"]:
            self.node.db.update_node(append_entry["term"])
        if self.node.db.get_logs()[append_entry['previousLogIndex']][0] == append_entry['previousLogTerm']:
            self.timer.cancel()
            self._set_timer()
            return {"term": current_term, "success": True}
        return {"term": current_term, "success": False}

    def on_request_vote(self, current_term, voted_for, request_vote):
        if current_term > request_vote["term"] or voted_for != -1:
            return {"term": current_term, "voteGranted": False}
        self.node.db.update_node(current_term, request_vote['candidateId'])
        self.timer.cancel()
        self._set_timer()
        return {"term": current_term, "voteGranted": True}


class Candidate(State):
    def __init__(self, node) -> None:
        super().__init__(node)
        self.node.db.update_node(current_term = self.node.db.get_state()[0] + 1)
        self.vote_count = 1
        self.vote_target = (len(rc.PEERS) / 2) + 1
        print(f"Node {rc.NODE_ID} has entered Candidate State", flush=True)

        for _, peer in self.node.get_peers():
            self.vote_count += peer.request_vote(self.node.request_vote_dict())
            if self.vote_count > self.vote_target:
                self.timer.cancel()
                self.node.state = Leader(self.node)

    def on_expire(self):
        self.node.state = Candidate(self.node)

    def on_append_entry(self, current_term, append_entry):
        if current_term > append_entry["term"]:
            return {"term": current_term, "success": False}
        self.timer.cancel()
        self.node.state = Follower(self.node)
        return {"term": current_term, "success": True}

    def on_request_vote(self, current_term, voted_for, request_vote):
        if current_term < request_vote["term"]:
            self.timer.cancel()
            self.node.state = Follower(self.node)
            return {"term": current_term, "voteGranted": True}
        return {"term": current_term, "voteGranted": False}


class Leader(State):
    def __init__(self, node) -> None:
        self.node = node
        self.interval = rc.HEARTBEAT_INTERVAL
        self._set_timer()
        self.next_idx = {id: len(self.node.db.get_logs()) for id, _ in self.node.get_peers()}
        self.match_idx = {id: 0 for id, _ in self.node.get_peers()}

    def append_entry_dict(self, peer_id, state, logs):
        return {
            "term": state[0],
            "leader": rc.NODE_ID,
            "previousLogIndex": self.next_idx[peer_id] - 1,
            "previousLogTerm": logs[self.next_idx[peer_id] - 1][0],
            "leaderCommit": self.commit_index
        }

    def on_expire(self):
        state = self.node.db.get_state()
        logs = self.node.db.get_logs()
        for id, peer in self.node.get_peers():
            response = peer.append_entry(self.append_entry_dict(id, state, logs))
            while not response['success']:
                if state[0] < response["term"]:
                    self.timer.cancel()
                    self.node.state = Follower(self.node)
                    return
                self.next_idx[id] -= 1
                response = peer.append_entry(self.append_entry_dict(id, state, logs))
        self._set_timer()

    def on_append_entry(self, current_term, append_entry):
        if current_term < append_entry["term"]:
            self.timer.cancel()
            self.node.state = Follower(self.node)
            return self.node.state.on_append_entry(current_term, append_entry)
        return {"term": current_term, "success": False}

    def on_request_vote(self, current_term, voted_for, request_vote):
        return {"term": current_term, "voteGranted": False}