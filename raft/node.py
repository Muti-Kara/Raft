import rpyc
import time

from raft.utils import FileDatabase, StateMachine, Log
from raft.states import Follower
import raft.config as config


@rpyc.service
class RaftNode(rpyc.Service):
    @rpyc.exposed
    def append_entry(self, append_entry: dict, append_entry_callback):
        append_entry_callback({
            "id": self.id,
            "term": self.data.current_term,
            "success": self.state.on_append_entry(append_entry)
        })

    def append_entry_callback(self, response: dict):
        self.state.on_append_entry_callback(response)
        
    @rpyc.exposed
    def request_vote(self, request_vote: dict, request_vote_callback):
        if time.time() > self.current_leader["heartbeat"]:
            request_vote_callback({
                "id": self.id,
                "term": self.data.current_term,
                "voteGranted": self.state.on_request_vote(request_vote)
            })

    def request_vote_callback(self, response: dict):
        self.state.on_request_vote_callback(response)

    def set_leader(self, leader_id):
        self.current_leader["id"] = leader_id
        self.current_leader["heartbeat"] = time.time() + (config.MIN_ELECTION_TIMEOUT / 1000)

    def apply_commands(self):
        if self.last_applied < self.commit_index:
            for i in range(self.last_applied+1, self.commit_index+1):
                args = self.data.logs[i].command.split(sep=Log.sep)
                self.state_machine.post_request(key=args[0], value=args[1])
            self.last_applied = self.commit_index

    def post_request(self, key: str, value: str):
        if self.current_leader["id"] == self.id:
            self.data.logs[len(self.data.logs)] = Log(
                term=self.data.current_term,
                command=f"{key}{Log.sep}{value}"
            )
            return str(self.data.logs[len(self.data.logs) - 1]), True
        return self.peers_http[self.current_leader["id"]], False

    def get_request(self, key: str):
        if self.current_leader["id"] == self.id:
            return self.state_machine.get_request(key=key), True
        return self.peers_http[self.current_leader["id"]], False

    def run(self):
        self.id = config.NODE_ID
        self.peers = {node_id: peer[:-1] for node_id, peer in config.PEERS.items() if node_id != self.id}
        self.peers_http = {node_id: peer[::2] for node_id, peer in config.PEERS.items() if node_id != self.id}
        self.commit_index = 0
        self.last_applied = 0
        self.current_leader = {"id": None, "heartbeat": 0}
        self.state_machine = StateMachine()
        self.data = FileDatabase()
        self.state = Follower(self)