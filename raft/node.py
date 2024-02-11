from rpyc.utils.server import ThreadedServer
import pickle
import rpyc
import time

from raft.utils.models import AppendEntryResponse, RequestVoteResponse, Log, ClusterConfigs, ClusterPingResponse
from raft.utils.database import BaseDatabase
from raft.utils.machine import BaseMachine
from raft.states.follower import Follower
from raft.states.state import State
from raft.states.idle import Idle
import config


@rpyc.service
class RaftNode(rpyc.Service):
    def __init__(self,
        Machine: type[BaseMachine],
        Database: type[BaseDatabase],
    ) -> None:
        self.state: State
        self.commit_index = 0
        self.last_applied = 0
        self.data = Database()
        self.machine = Machine()
        self.current_leader = {"id": None, "heartbeat": 0}
        Idle(self)

    @rpyc.exposed
    def append_entry(self, append_entry, append_entry_callback):
        print(pickle.loads(append_entry), flush=True)
        try:
            append_entry_callback(pickle.dumps(AppendEntryResponse(
                term=self.data.current_term,
                id=self.id,
                acknowledge=self.state.on_append_entry(pickle.loads(append_entry))
            )))
        except Exception as e:
            print(e, flush=True)
        
    @rpyc.exposed
    def request_vote(self, request_vote, request_vote_callback):
        print(pickle.loads(request_vote), flush=True)
        try:
            if time.time() > self.current_leader["heartbeat"]:
                request_vote_callback(pickle.dumps(RequestVoteResponse(
                    term=self.data.current_term,
                    id=self.id,
                    vote_granted=self.state.on_request_vote(pickle.loads(request_vote))
                )))
        except Exception as e:
            print(e, flush=True)

    @rpyc.exposed
    def cluster_config(self, data):
        self.cluster: ClusterConfigs = pickle.loads(data)
        self.peers = {peer.id: peer for peer in self.cluster.peers if peer.id != self.id}
        self.data.configure(self.cluster.database_configs)
        self.machine.configure(self.cluster.machine_configs)
    
    @rpyc.exposed
    def cluster_ping(self):
        return pickle.dumps(ClusterPingResponse(
            term=self.data.current_term,
            state=self.state.__class__.__name__,
            leader=self.current_leader["id"],
            commit_index=self.commit_index,
            last_applied=self.last_applied,
            last_log_idx=len(self.data.logs.logs) - 1,
        ))

    @rpyc.exposed
    def cluster_join(self, node_id):
        self.id = str(node_id)

    @rpyc.exposed
    def cluster_start(self):
        Follower(self)

    @rpyc.exposed
    def cluster_stop(self):
        Idle(self)

    def request(self, command, get: bool = False):
        if self.current_leader["id"] == self.id:
            if get:
                return self.machine.get_request(command), True
            return self.data.logs.add_log(Log(term=self.data.current_term, command=command)), True
        if time.time() > self.current_leader["heartbeat"]:
            return self.peers[self.current_leader["id"]], False
        return None, False

    def append_entry_callback(self, response):
        print(pickle.loads(response), flush=True)
        try:
            self.state.on_append_entry_callback(pickle.loads(response))
        except Exception as e:
            print(e, flush=True)

    def request_vote_callback(self, response):
        print(pickle.loads(response), flush=True)
        try:
            self.state.on_request_vote_callback(pickle.loads(response))
        except Exception as e:
            print(e, flush=True)

    def set_leader(self, leader_id):
        self.current_leader["id"] = leader_id
        self.current_leader["heartbeat"] = time.time() + (self.cluster.min_election_timeout / 1000)

    def apply_commands(self):
        if self.last_applied < self.commit_index:
            for i in range(self.last_applied+1, self.commit_index+1):
                self.machine.post_request(self.data.logs.logs[i].command)
            self.last_applied = self.commit_index

    def run(self):
        ThreadedServer(self, port=config.NODE_RPC_PORT).start()