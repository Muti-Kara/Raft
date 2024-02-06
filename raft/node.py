from rpyc.utils.server import ThreadedServer
import rpyc

from raft.utils import FileDatabase
from raft.states import Follower
import raft.config as config


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
    def append_entry(self, append_entry: dict):
        print(f"APPEND ENTRY: {append_entry}", flush=True)
        out = {
            "term": self.data.current_term,
            "success": self.state.on_append_entry(append_entry)
        }
        print(f"RESPONSE: {out}", flush=True)
        return out
        
    @rpyc.exposed
    def request_vote(self, request_vote: dict):
        print(f"REQUEST VOTE: {request_vote}", flush=True)
        out = {
            "term": self.data.current_term,
            "voteGranted": self.state.on_request_vote(request_vote)
        }
        print(f"RESPONSE: {out}", flush=True)
        return out

    def get_peers(self):
        for id, address in self.peers.items():
            try:
                yield id, rpyc.connect(*address).root
            except Exception:
                continue

    def run(self):
        self.state = Follower(self)
        ThreadedServer(self, port=config.NODE_PORT).start()