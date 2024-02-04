import threading
import rpyc

from raft.states import Follower, Candidate, Leader
from raft.data import AppendEntry, RequestVote
import raft.config as rc


@rpyc.service
class RaftNode(rpyc.Service):
    def __init__(self) -> None:
        self.state = None
        self.peers = dict()

    @rpyc.exposed
    def append_entry(self, append_entry: AppendEntry):
        return self.state.on_append_entry(append_entry)

    @rpyc.exposed
    def request_vote(self, request_vote: RequestVote):
        return self.state.on_request_vote(request_vote)
    
    def get_peers(self):
        for id, host, port in rc.PEERS:
            if id == rc.NODE_ID:
                continue
            try:
                yield id, rpyc.connect(host, port).root
            except Exception:
                continue

    def run(self):
        def run_rpyc_server():
            from rpyc.utils.server import ThreadedServer
            ThreadedServer(self, port=rc.NODE_PORT).start()

        threading.Thread(target=run_rpyc_server, daemon=True).start()

        self.state = Follower(self)