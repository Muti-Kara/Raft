import pickle
import rpyc
import time

from raft.states.rpc_models import AppendEntryResponse, RequestVoteResponse
from raft.states.follower import Follower
from raft.utils.logs import Log
import config


@rpyc.service
class RaftNode(rpyc.Service):
    def __init__(self, Machine, Database) -> None:
        self.id = config.NODE_ID
        self.peers = {node_id: peer[:-1] for node_id, peer in config.PEERS.items() if node_id != self.id}
        self.peers_http = {node_id: peer[::2] for node_id, peer in config.PEERS.items() if node_id != self.id}
        self.commit_index = 0
        self.last_applied = 0
        self.data = Database()
        self.machine = Machine()
        self.current_leader = {"id": None, "heartbeat": 0}

    @rpyc.exposed
    def append_entry(self, append_entry, append_entry_callback):
        append_entry_callback(pickle.dumps(AppendEntryResponse(
            term=self.data.current_term,
            id=self.id,
            success=self.state.on_append_entry(pickle.loads(append_entry))
        )))

    def append_entry_callback(self, response):
        self.state.on_append_entry_callback(pickle.loads(response))
        
    @rpyc.exposed
    def request_vote(self, request_vote, request_vote_callback):
        if time.time() > self.current_leader["heartbeat"]:
            request_vote_callback(pickle.dumps(RequestVoteResponse(
                term=self.data.current_term,
                id=self.id,
                vote_granted=self.state.on_request_vote(pickle.loads(request_vote))
            )))

    def request_vote_callback(self, response):
        self.state.on_request_vote_callback(pickle.loads(response))

    def set_leader(self, leader_id):
        self.current_leader["id"] = leader_id
        self.current_leader["heartbeat"] = time.time() + (config.MIN_ELECTION_TIMEOUT / 1000)

    def apply_commands(self):
        if self.last_applied < self.commit_index:
            for i in range(self.last_applied+1, self.commit_index+1):
                self.machine.post_request(self.data.logs.logs[i].command)
            self.last_applied = self.commit_index

    def post_request(self, command):
        if self.current_leader["id"] == self.id:
            self.data.logs.add_log(Log(term=self.data.current_term, command=command))
            return self.data.logs.logs[-1].model_dump_json(), True
        return self.peers_http[self.current_leader["id"]], False

    def get_request(self, command):
        if self.current_leader["id"] == self.id:
            return self.machine.get_request(command), True
        return self.peers_http[self.current_leader["id"]], False

    def run(self):
        Follower(self)