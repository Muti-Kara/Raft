from concurrent.futures import ThreadPoolExecutor
import rpyc

from raft.utils import FunctionTimer, Log
import raft.config as config


class State():
    def __init__(self, node, min_timeout, max_timeout) -> None:
        print(self.__class__.__name__, flush=True)
        self.node = node
        self.node.state = self
        self.timer = FunctionTimer(min_timeout, max_timeout, self.on_expire)

    def change_state(self, NewState: 'State', new_term: int | None = None):
        if isinstance(self.node.state, NewState):
            return
        if new_term:
            self.node.data.current_term = new_term
        self.timer.stop()
        NewState(self.node)

    def on_expire(self):
        raise NotImplementedError

    def on_append_entry(self, ae: dict):
        raise NotImplementedError

    def on_append_entry_callback(self, res: dict):
        return

    def on_request_vote(self, rv: dict):
        raise NotImplementedError

    def on_request_vote_callback(self, res: dict):
        return

    def broadcast_rpc(self, peer_id, peer_addr):
        return


class Follower(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.MIN_ELECTION_TIMEOUT, config.MAX_ELECTION_TIMEOUT)

    def on_expire(self):
        self.change_state(Candidate)

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term > ae["term"]:
            return -2

        self.timer.reset()
        self.node.set_leader(ae['leader'])

        if self.node.data.current_term < ae["term"]:
            self.node.data.current_term = ae["term"]

        if ae['previousLogIndex'] >= len(self.node.data.logs):
            return -2
        if self.node.data.logs[ae['previousLogIndex']].term != ae['previousLogTerm']:
            return -2
        return self.accept_logs(ae)

    def on_request_vote(self, rv: dict):
        if self.node.data.current_term < rv["term"]:
            self.node.data.current_term = rv["term"]
            self.node.data.voted_for = -1

        if self.node.data.current_term > rv["term"]:
            return False
        if self.node.data.logs[-1].term > rv["lastLogTerm"]:
            return False
        if len(self.node.data.logs) - 1 > rv["lastLogIndex"]:
            return False
        if self.node.data.voted_for != -1:
            return False

        self.node.data.voted_for = rv['candidateId']
        self.timer.reset()
        return True

    def accept_logs(self, ae):
        index = ae["previousLogIndex"] + 1
        for entry in ae["entries"]:
            self.node.data.logs[index] = Log(term=entry[0], command=entry[1])
            index += 1
        self.node.commit_index = ae["leaderCommit"]
        self.node.apply_commands()
        return len(self.node.data.logs) - 1


class Candidate(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.MIN_ELECTION_TIMEOUT, config.MAX_ELECTION_TIMEOUT)

        self.node.data.current_term += 1
        self.node.data.voted_for = self.node.id
        self.voters = set([self.node.id])
        self.vote_target = (len(self.node.peers) // 2) + 1

        with ThreadPoolExecutor() as executor:
            for peer_id, peer_addr in self.node.peers.items():
                executor.submit(self.broadcast_rpc, peer_id, peer_addr)

    def on_expire(self):
        self.change_state(Candidate)

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term > ae["term"]:
            return False
        self.change_state(Follower)
        return self.node.state.on_append_entry(ae)

    def on_request_vote(self, rv: dict):
        if self.node.data.current_term >= rv["term"]:
            return False
        self.change_state(Follower, rv["term"])
        return True

    def on_request_vote_callback(self, res):
        if self.node.data.current_term < res["term"]:
            self.change_state(Follower, res["term"])
        elif res['voteGranted']:
            self.voters.add(res['id'])
            if len(self.voters) >= self.vote_target:
                self.change_state(Leader)

    def broadcast_rpc(self, peer_id, peer_addr):
        try:
            rpyc.connect(*peer_addr).root.request_vote(
                {
                    "term": self.node.data.current_term,
                    "candidateId": self.node.id,
                    "lastLogIndex": len(self.node.data.logs) - 1,
                    "lastLogTerm": self.node.data.logs[-1].term,
                },
                self.node.request_vote_callback
            )
        except:
            return


class Leader(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.HEARTBEAT_INTERVAL, config.HEARTBEAT_INTERVAL)
        self.next_idx = {id: len(self.node.data.logs) for id, _ in self.node.peers.items()}
        self.match_idx = {id: 0 for id, _ in self.node.peers.items()}
        self.node.current_leader["id"] = self.node.id

    def on_expire(self):
        self.timer.reset()
        with ThreadPoolExecutor() as executor:
            for peer_id, peer_addr in self.node.peers.items():
                executor.submit(self.broadcast_rpc, peer_id, peer_addr)

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term >= ae["term"]:
            return False
        self.change_state(Follower, ae["term"])
        return True

    def on_append_entry_callback(self, res):
        if res["success"] != -2:
            self.next_idx[res["id"]] = res["success"] + 1
            self.match_idx[res["id"]] = max(res["success"], self.match_idx[res["id"]])
            sorted_match_index = sorted(self.match_idx.values())
            self.node.commit_index = max(
                self.node.commit_index,
                sorted_match_index[len(sorted_match_index)//2]
            )
            self.node.apply_commands()
        else:
            if self.node.data.current_term < res["term"]:
                return self.change_state(Follower, res["term"])
            else:
                self.next_idx[res['id']] = 1 # I know that create block will exist
                self.match_idx[res['id']] = 1

    def on_request_vote(self, rv: dict):
        if self.node.data.current_term >= rv["term"]:
            return False
        self.change_state(Follower, rv["term"])
        return True

    def broadcast_rpc(self, peer_id, peer_addr):
        try:
            rpyc.connect(*peer_addr).root.append_entry(
                {
                    "term": self.node.data.current_term,
                    "leader": self.node.id,
                    "previousLogIndex": self.next_idx[peer_id] - 1,
                    "previousLogTerm": self.node.data.logs[self.next_idx[peer_id] - 1].term,
                    "leaderCommit": self.node.commit_index,
                    "entries": self.node.data.logs.serialize(self.next_idx[peer_id])
                },
                self.node.append_entry_callback
            )
        except:
            return