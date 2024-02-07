from concurrent.futures import ThreadPoolExecutor
import rpyc

from raft.utils import FunctionTimer, Log
import raft.config as config


class State():
    def __init__(self, node, timeout) -> None:
        from raft.node import RaftNode
        self.node: RaftNode = node
        self.node.state = self # Otherwise in Candidate __init__, node still is in Follower state
        self.timer = FunctionTimer(timeout, self.on_expire)

    def change_state(self, NewState: 'State', new_term: int | None = None):
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


class Follower(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.ELECTION_TIMEOUT)

    def accept_logs(self, entries, previous_log_index, leader_commit):
        index = previous_log_index + 1
        for entry in entries:
            self.node.data.logs[index] = Log(term=entry[0], command=entry[1])
        self.node.commit_index = leader_commit
        return len(self.node.data.logs) - 1 # the last index

    def on_expire(self):
        print(f"Waited for {self.timer._random_interval / 1000} sec", flush=True)
        self.change_state(Candidate)

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term > ae["term"]:
            return 0
        if self.node.data.logs[ae['previousLogIndex']].term != ae['previousLogTerm']:
            return 0
        if self.node.data.current_term < ae["term"]:
            self.node.data.current_term = ae["term"]
        self.timer.reset()
        return self.accept_logs(ae["entries"], ae["previousLogIndex"], ae["leaderCommit"])

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
            "lastLogIndex": len(self.node.data.logs) - 1,
            "lastLogTerm": self.node.data.logs[-1].term,
        }
        with ThreadPoolExecutor() as executor:
            for peer_addr in self.node.peers.values():
                executor.submit(self.call_rv_rpc, peer_addr, request_vote_dict)

    def call_rv_rpc(self, peer_addr, request_vote_dict):
        try:
            rpyc.connect(*peer_addr).root.request_vote(
                request_vote_dict,
                self.node.request_vote_callback
            )
        except:
            return

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


class Leader(State):
    def __init__(self, node) -> None:
        super().__init__(node, config.HEARTBEAT_INTERVAL)
        self.next_idx = {id: len(self.node.data.logs) for id, _ in self.node.peers.items()}
        self.match_idx = {id: 0 for id, _ in self.node.peers.items()}
        self.node.data.logs[len(self.node.data.logs)] = Log(term=self.node.data.current_term, command=f"OBEY_NODE_{self.node.id}")

    def append_entry_dict(self, peer_id):
        return {
            "term": self.node.data.current_term,
            "leader": self.node.id,
            "previousLogIndex": self.next_idx[peer_id] - 1,
            "previousLogTerm": self.node.data.logs[self.next_idx[peer_id] - 1].term,
            "leaderCommit": self.node.commit_index,
            "entries": self.node.data.logs.serialize(self.next_idx[peer_id])
        }

    def on_expire(self):
        sorted_match_index = sorted(self.match_idx.values())
        self.node.commit_index = max(
            self.node.commit_index,
            sorted_match_index[len(sorted_match_index)//2] # median of current acknowledged matches
        )
        self.timer.reset()
        with ThreadPoolExecutor() as executor:
            for peer_id, peer_addr in self.node.peers.items():
                executor.submit(
                    self.call_ae_rpc,
                    peer_id,
                    peer_addr
                )

    def call_ae_rpc(self, peer_id, peer_addr):
        try:
            rpyc.connect(*peer_addr).root.append_entry(
                self.append_entry_dict(peer_id),
                self.node.request_vote_callback
            )
        except:
            return

    def on_append_entry(self, ae: dict):
        if self.node.data.current_term >= ae["term"]:
            return False
        self.change_state(Follower, ae["term"])
        return True

    def on_append_entry_callback(self, res):
        if res["success"]:
            self.next_idx[res["id"]] = res["success"] + 1
            self.match_idx[res["id"]] = res["success"]
        else:
            if self.node.data.current_term < res["term"]:
                return self.change_state(Follower, res["term"])
            else:
                self.next_idx[res['id']] = 0
                self.match_idx[res['id']] = 0

    def on_request_vote(self, rv: dict):
        if self.node.data.current_term >= rv["term"]:
            return False
        self.change_state(Follower, rv["term"])
        return True