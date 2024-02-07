from rpyc.utils.server import ThreadedServer
import rpyc
import time

from raft.utils import FileDatabase
from raft.states import Follower
import raft.config as config

network_delay = 0.6


@rpyc.service
class RaftNode(rpyc.Service):
    def __init__(self) -> None:
        super().__init__()
        self.id = config.NODE_ID
        self.peers = {node_id: peer for node_id, peer in config.PEERS.items() if node_id != self.id}
        self.data = FileDatabase()
        self.commit_index = 0
        self.last_applied = 0 # This is for applying commits to state machine

    @rpyc.exposed
    def append_entry(self, append_entry: dict, append_entry_callback):
        time.sleep(network_delay)
        print(f"STATE: {self.state.__class__.__name__}  \tAE from: {append_entry['leader'], append_entry['term']}", flush=True)
        append_entry_callback({
            "id": self.id,
            "term": self.data.current_term,
            "success": self.state.on_append_entry(append_entry)
        })

    def append_entry_callback(self, response: dict):
        time.sleep(network_delay)
        print(f"STATE: {self.state.__class__.__name__}  \tAE to:   {response['id'], response['success']}", flush=True)
        self.state.on_append_entry_callback(response)
        
    @rpyc.exposed
    def request_vote(self, request_vote: dict, request_vote_callback):
        time.sleep(network_delay)
        print(f"STATE: {self.state.__class__.__name__}  \tRV from: {request_vote['candidateId'], request_vote['term']}", flush=True)
        request_vote_callback({
            "id": self.id,
            "term": self.data.current_term,
            "voteGranted": self.state.on_request_vote(request_vote)
        })

    def request_vote_callback(self, response: dict):
        time.sleep(network_delay)
        print(f"STATE: {self.state.__class__.__name__}  \tRV to:   {response['id'], response['voteGranted']}", flush=True)
        self.state.on_request_vote_callback(response)

    def get_peers(self):
        for id, address in self.peers.items():
            try:
                yield id, rpyc.connect(*address).root
            except Exception:
                continue

    def run(self):
        self.state = Follower(self)
        ThreadedServer(self, port=config.NODE_PORT).start()