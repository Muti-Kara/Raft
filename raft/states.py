from raft.utils import FunctionTimer
import raft.config as config


class State():
    def __init__(self, node, timeout) -> None:
        from raft.node import RaftNode
        self.node: RaftNode = node
        self.node.state = self # Otherwise in Candidate __init__ node still is in Follower state
        self.timer = FunctionTimer(timeout, self.on_expire)

    def on_expire(self):
        raise NotImplementedError

    def on_append_entry(self, ae: dict):
        raise NotImplementedError

    def on_request_vote(self, rv: dict):
        raise NotImplementedError


class Follower(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.ELECTION_TIMEOUT)

    def on_expire(self):
        Candidate(self.node)

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term > ae["term"]:
            return False

        if self.node.data.current_term < ae["term"]:
            self.node.data.current_term = ae["term"]
            return True

        if self.node.data.logs[ae['previousLogIndex']].term != ae['previousLogTerm']:
            return False

        self.timer.reset()
        return True

    def on_request_vote(self, rv: dict):
        if self.node.data.current_term < rv["term"]:
            self.node.data.current_term = rv["term"]
            self.node.data.voted_for = -1

        if self.node.data.current_term > rv["term"]:
            return False
        if self.node.data.voted_for != -1:
            return False
        if self.node.data.logs[-1].term > rv["lastLogTerm"]:
            return False
        if len(self.node.data.logs) > rv["lastLogIndex"]:
            return False

        self.node.data.voted_for = rv['candidateId']
        self.timer.reset()
        return True


class Candidate(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.ELECTION_TIMEOUT)

        self.node.data.current_term += 1
        self.node.data.voted_for = self.node.id
        self.voters = set([self.node.id])
        self.vote_target = (len(config.PEERS) // 2) + 1

        request_vote_dict = {
            "term": self.node.data.current_term,
            "candidateId": self.node.id,
            "lastLogIndex": len(self.node.data.logs),
            "lastLogTerm": self.node.data.logs[-1].term,
        }
        for peer_id, peer in self.node.get_peers():
            res = peer.request_vote(request_vote_dict)
            if self.node.data.current_term < res["term"]:
                self.node.data.current_term = res["term"]
                self.timer.stop()
                Follower(self.node)
                return
            if res['voteGranted']:
                self.voters.add(peer_id)
                if len(self.voters) > self.vote_target:
                    self.timer.stop()
                    Leader(self.node)
                    return

    def on_expire(self):
        Candidate(self.node)

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term > ae["term"]:
            return False
        self.timer.stop()
        Follower(self.node)
        return True

    def on_request_vote(self, rv: dict):
        if self.node.data.current_term >= rv["term"]:
            return False
        self.node.data.current_term = rv["term"]
        self.timer.stop()
        Follower(self.node)
        return True


class Leader(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.HEARTBEAT_INTERVAL)
        self.next_idx = {id: len(self.node.data.logs) for id, _ in self.node.get_peers()}
        self.match_idx = {id: 0 for id, _ in self.node.get_peers()}

    def append_entry_dict(self, peer_id):
        return {
            "term": self.node.data.current_term,
            "leader": self.node.id,
            "previousLogIndex": self.next_idx[peer_id] - 1,
            "previousLogTerm": self.node.data.logs[self.next_idx[peer_id] - 1].term,
            "leaderCommit": self.node.commit_index
        }

    def on_expire(self):
        for peer_id, peer in self.node.get_peers():
            res = peer.append_entry(self.append_entry_dict(peer_id))
            while not res['success']:
                if self.node.data.current_term < res["term"]:
                    self.timer.stop()
                    Follower(self.node)
                    return
                self.next_idx[peer_id] -= 1
                res = peer.append_entry(self.append_entry_dict(peer_id))
        self.timer.start()

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term >= ae["term"]:
            return False
        self.node.data.current_term = ae["term"]
        self.timer.stop()
        Follower(self.node)
        return True

    def on_request_vote(self, rv: dict):
        if self.node.data.current_term >= rv["term"]:
            return False
        self.node.data.current_term = rv["term"]
        self.timer.stop()
        Follower(self.node)
        return True