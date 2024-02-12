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


@rpyc.service
class RaftNode(rpyc.Service):
    """
    RaftNode represents a single node in the Raft-based distributed system.

    It implements the Raft consensus algorithm and exposes RPC methods for communication with other nodes.

    Attributes:
        state (State): The current state of the node in the Raft consensus algorithm.
        commit_index (int): The index of the highest log entry known to be committed.
        last_applied (int): The index of the highest log entry applied to the state machine.
        data (BaseDatabase): The database used to store Raft-related data.
        machine (BaseMachine): The state machine used to execute commands.
        rpc_port (int): The port on which the RPC server is running.
        current_leader (str): The ID of the current leader node in the cluster.
        current_leader_heartbeat (float): The timestamp of the next expected heartbeat from the leader.
    """

    def __init__(self, machine: BaseMachine, data: BaseDatabase, rpc_port: int) -> None:
        """
        Initialize the RaftNode.

        Args:
            machine (BaseMachine): The state machine used by the node.
            data (BaseDatabase): The database used to store Raft-related data.
            rpc_port (int): The port on which the RPC server will run.
        """
        self.state: State
        self.commit_index = 0
        self.last_applied = 0
        self.data = data
        self.machine = machine
        self.rpc_port = rpc_port
        self.current_leader = None
        self.current_leader_heartbeat = 0
        Idle(self)

    @rpyc.exposed
    def append_entry(self, append_entry, append_entry_callback):
        """
        RPC method for appending a log entry to the node's log.

        Args:
            append_entry: The serialized AppendEntry object containing the log entry to be appended.
            append_entry_callback: The callback function to be executed after appending the entry.

        This method is exposed as an RPC endpoint and is called by the leader to replicate log entries
        across the cluster. It delegates the append operation to the current node state.
        """
        append_entry_callback(pickle.dumps(AppendEntryResponse(
            term=self.data.current_term,
            id=self.id,
            acknowledge=self.state.on_append_entry(pickle.loads(append_entry))
        )))

    @rpyc.exposed
    def request_vote(self, request_vote, request_vote_callback):
        """
        RPC method for processing a RequestVote RPC.

        Args:
            request_vote: The serialized RequestVote object containing the candidate's vote request.
            request_vote_callback: The callback function to be executed after processing the vote request.

        This method is exposed as an RPC endpoint and is called by candidate nodes to request votes
        from other nodes in the cluster. It delegates the vote request to the current node state.
        """
        if time.time() > self.current_leader_heartbeat:
            request_vote_callback(pickle.dumps(RequestVoteResponse(
                term=self.data.current_term,
                id=self.id,
                vote_granted=self.state.on_request_vote(pickle.loads(request_vote))
            )))

    @rpyc.exposed
    def cluster_config(self, data):
        """
        RPC method for applying cluster configuration changes.

        Args:
            data: The serialized ClusterConfigs object containing the new cluster configuration.

        This method is exposed as an RPC endpoint and is called by the cluster manager to apply
        configuration changes to the nodes in the cluster.
        """
        self.cluster: ClusterConfigs = pickle.loads(data)
        self.peers = {peer.id: peer for peer in self.cluster.peers if peer.id != self.id}
        self.data.configure(self.cluster.database_configs)
        self.machine.configure(self.cluster.machine_configs)
    
    @rpyc.exposed
    def cluster_ping(self):
        """
        RPC method for retrieving cluster status information.

        Returns:
            str: The serialized ClusterPingResponse object containing cluster status information.

        This method is exposed as an RPC endpoint and is called by external clients to retrieve
        information about the current state of the cluster.
        """
        return pickle.dumps(ClusterPingResponse(
            term=self.data.current_term,
            state=self.state.__class__.__name__,
            leader=self.current_leader,
            commit_index=self.commit_index,
            last_applied=self.last_applied,
            last_log_idx=len(self.data.logs.logs) - 1,
        ))

    @rpyc.exposed
    def cluster_join(self, node_id):
        """
        RPC method for joining the cluster.

        Args:
            node_id (str): The ID of the node joining the cluster.

        This method is exposed as an RPC endpoint and is called by nodes when they join the cluster.
        """
        self.id = str(node_id)

    @rpyc.exposed
    def cluster_start(self):
        """Start the node."""
        Follower(self)

    @rpyc.exposed
    def cluster_stop(self):
        """Stop the node."""
        self.state._change_state(Idle)

    def request(self, command, get: bool = False):
        """
        Send a request to the current leader or forward it to the leader if this node is not the leader.

        Args:
            command: The command to be executed.
            get (bool): A flag indicating whether the request is a read (get) or a write (post) operation.

        Returns:
            tuple: A tuple containing the response and a boolean indicating whether the node is the leader.

        This method is used by clients to send requests to the cluster. If the node is the leader,
        it directly processes the request; otherwise, it forwards the request to the current leader.
        """
        if self.current_leader == self.id:
            if get:
                return self.machine.get_request(command), True
            return self.data.logs.add_log(Log(term=self.data.current_term, command=command)), True
        if time.time() > self.current_leader_heartbeat:
            return self.peers[self.current_leader], False
        return None, False

    def append_entry_callback(self, response):
        """Callback function for processing the response to an append entry request."""
        self.state.on_append_entry_callback(pickle.loads(response))

    def request_vote_callback(self, response):
        """Callback function for processing the response to a request vote request."""
        self.state.on_request_vote_callback(pickle.loads(response))

    def set_leader(self, leader_id):
        """
        Set the current leader and update the leader heartbeat timestamp.

        Args:
            leader_id (str): The ID of the current leader.

        This method is called when a node detects a new leader in the cluster.
        """
        self.current_leader = leader_id
        self.current_leader_heartbeat = time.time() + (self.cluster.min_election_timeout / 1000)

    def apply_commands(self):
        """
        Apply commands from the log to the state machine.

        This method is called when new log entries are committed to the cluster. It applies
        the commands from the log to the state machine, ensuring that they are executed in order.
        """
        if self.last_applied < self.commit_index:
            for i in range(self.last_applied+1, self.commit_index+1):
                self.machine.post_request(self.data.logs.logs[i].command)
            self.last_applied = self.commit_index

    def run(self):
        """Start the RPC server."""
        ThreadedServer(self, port=self.rpc_port).start()