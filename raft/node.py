from rpyc.utils.server import ThreadedServer
import rpyc

from raft.states import Follower
import raft.config as rc


@rpyc.service
class RaftNode(rpyc.Service):
    def __init__(self) -> None:
        self.peers = dict()

    @rpyc.exposed
    def append_entry(self, append_entry):
        return self.state.on_append_entry(append_entry)

    @rpyc.exposed
    def request_vote(self, request_vote):
        return self.state.on_request_vote(request_vote)

    def append_entry_dict(self):
        return {
            "leader": rc.NODE_ID
        }

    def request_vote_dict(self):
        return {
            "peer": rc.NODE_ID
        }

    def get_peers(self):
        for id, host, port in rc.PEERS:
            if id != rc.NODE_ID:
                try:
                    yield rpyc.connect(host, port).root
                except Exception:
                    continue

    def run(self):
        self.state = Follower(self)
        ThreadedServer(self, port=rc.NODE_PORT).start()