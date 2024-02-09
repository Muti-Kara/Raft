from rpyc.utils.server import ThreadedServer
import pickle
import rpyc
import time

from raft.states.rpc_models import AppendEntryResponse, RequestVoteResponse
from raft.utils.database import BaseDatabase
from raft.utils.machine import BaseMachine
from raft.states.follower import Follower
from raft.utils.logs import Log
import config


@rpyc.service
class RaftNode(rpyc.Service):
    def __init__(self, Machine: type[BaseMachine], Database: type[BaseDatabase]) -> None:
        """
        Initializes a Raft Node instance.

        Args:
            Machine (type[BaseMachine]): Type of the machine implementation.
            Database (type[BaseDatabase]): Type of the database implementation.
        """
        self.id = config.NODE_ID
        self.peers_rpc = {node_id: peer[:-1] for node_id, peer in config.PEERS.items() if node_id != self.id}
        self.peers_http = {node_id: peer[::2] for node_id, peer in config.PEERS.items() if node_id != self.id}
        self.commit_index = 0
        self.last_applied = 0
        self.data: BaseDatabase = Database()
        self.machine: BaseMachine = Machine()
        self.current_leader = {"id": None, "heartbeat": 0}

    @rpyc.exposed
    def append_entry(self, append_entry, append_entry_callback):
        print(pickle.loads(append_entry), flush=True)
        """
        Exposed method for appending log entries.

        Args:
            append_entry: AppendEntry message. In pickled form.
            append_entry_callback: Callback function to handle the response.
        """
        append_entry_callback(pickle.dumps(AppendEntryResponse(
            term=self.data.current_term,
            id=self.id,
            acknowledge=self.state.on_append_entry(pickle.loads(append_entry))
        )))

    def append_entry_callback(self, response):
        print(pickle.loads(response), flush=True)
        """
        Callback function for handling append entry responses.

        Args:
            response: Response from append_entry. In pickled form.
        """
        self.state.on_append_entry_callback(pickle.loads(response))
        
    @rpyc.exposed
    def request_vote(self, request_vote, request_vote_callback):
        """
        Exposed method for handling request for votes.

        Args:
            request_vote: RequestVote message. In pickled form.
            request_vote_callback: Callback function to handle the response.
        """
        if time.time() > self.current_leader["heartbeat"]:
            request_vote_callback(pickle.dumps(RequestVoteResponse(
                term=self.data.current_term,
                id=self.id,
                vote_granted=self.state.on_request_vote(pickle.loads(request_vote))
            )))

    def request_vote_callback(self, response):
        """
        Callback function for handling request vote responses.

        Args:
            response: Response from request_vote. In pickled form.
        """
        self.state.on_request_vote_callback(pickle.loads(response))

    def set_leader(self, leader_id):
        """
        Sets the leader of the node.

        Args:
            leader_id: ID of the leader node.
        """
        self.current_leader["id"] = leader_id
        self.current_leader["heartbeat"] = time.time() + (config.MIN_ELECTION_TIMEOUT / 1000)

    def apply_commands(self):
        """
        Applies commands to the state machine.
        """
        if self.last_applied < self.commit_index:
            for i in range(self.last_applied+1, self.commit_index+1):
                self.machine.post_request(self.data.logs.logs[i].command)
            self.last_applied = self.commit_index

    @rpyc.exposed
    def post_request(self, command):
        """
        Exposed method for processing POST requests.

        Args:
            command: Command to be processed.

        Returns:
            tuple: Log index and whether the node is the leader or not.
        """
        if self.current_leader["id"] == self.id:
            log_idx = self.data.logs.add_log(Log(term=self.data.current_term, command=command))
            return log_idx, True
        if time.time() > self.current_leader["heartbeat"]:
            return self.peers_http[self.current_leader["id"]], False
        return None, False

    @rpyc.exposed
    def get_request(self, command):
        """
        Exposed method for processing GET requests.

        Args:
            command: Command to be processed.

        Returns:
            tuple: Result of the GET request and whether the node is the leader or not.
        """
        if self.current_leader["id"] == self.id:
            return self.machine.get_request(command), True
        if time.time() > self.current_leader["heartbeat"]:
            return self.peers_http[self.current_leader["id"]], False
        return None, False

    def run(self):
        """
        Runs the Raft node.
        """
        Follower(self)
        ThreadedServer(self, port=config.NODE_RPC_PORT).start()