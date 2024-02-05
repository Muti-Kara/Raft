from rpyc.utils.server import ThreadedServer
import rpyc

from raft.database import Database, FileDatabase
from raft.states import Follower
import raft.config as rc


@rpyc.service
class RaftNode(rpyc.Service):
    def __init__(self) -> None:
        self.peers = dict()
        self.db: Database = FileDatabase() # For persistent storage
        self.commit_index = 0
        self.last_applied = 0 # This is for applying to state machine

    @rpyc.exposed
    def append_entry(self, append_entry):
        print(f"NODE{rc.NODE_ID} AE IN: {append_entry}", flush=True)
        out = self.state.on_append_entry(self.db.get_state()[0], append_entry)
        print(f"NODE{rc.NODE_ID} AE OUT: {out}", flush=True)
        return out

    @rpyc.exposed
    def request_vote(self, request_vote):
        print(f"NODE{rc.NODE_ID} RV IN: {request_vote}", flush=True)
        out = self.state.on_request_vote(self.db.get_state()[0], self.db.get_state()[1], request_vote)
        print(f"NODE{rc.NODE_ID} RV OUT: {out}", flush=True)
        return out

    def get_peers(self):
        for id, host, port in rc.PEERS:
            if id != rc.NODE_ID:
                try:
                    yield id, rpyc.connect(host, port).root
                except Exception:
                    continue

    def run(self):
        self.state = Follower(self)
        ThreadedServer(self, port=rc.NODE_PORT).start()