from pydantic import BaseModel


class Log(BaseModel):
    """
    Represents a single log entry in the Raft algorithm.

    Attributes:
        term (int): The term associated with the log entry.
        command (dict): The command associated with the log entry.
    """
    term: int
    command: dict


class LogList(BaseModel):
    """
    Represents a list of log entries in the Raft algorithm.

    Attributes:
        logs (list[Log]): The list of log entries.
    """
    logs: list[Log] = list()

    def add_log(self, value: Log) -> int:
        """
        Add a log entry to the list.

        Args:
            value (Log): The log entry to add.

        Returns:
            int: The index of the added log entry.
        """
        self.logs.append(value)
        return len(self.logs) - 1

    def add_logs(self, index: int, value: 'LogList') -> None:
        """
        Add a list of log entries starting from a specific index.

        Args:
            index (int): The starting index for adding log entries.
            value (LogList): The list of log entries to add.
        """
        self.logs[index:] = value.logs


class Peer(BaseModel):
    """
    Represents a peer in the Raft cluster.

    Attributes:
        id (str): The unique identifier of the peer.
        host (str): The hostname or IP address of the peer.
        rpc_port (int): The RPC port of the peer for internal communication.
        exposed_port (int): The exposed port of the peer for external access.
    """
    id: str
    host: str
    rpc_port: int
    exposed_port: int

    @property
    def rpc_address(self) -> tuple[str, int]:
        """
        Get the RPC address of the peer.

        Returns:
            tuple[str, int]: The RPC address as a tuple of hostname/IP address and port.
        """
        return self.host, self.rpc_port


class ClusterConfigsWithoutPeers(BaseModel):
    """
    Represents cluster configurations without peer information.

    Attributes:
        min_election_timeout (float): The minimum election timeout.
        max_election_timeout (float): The maximum election timeout.
        heartbeat_interval (float): The heartbeat interval.
        database_configs (dict): Additional database configurations.
        machine_configs (dict): Additional machine configurations.
    """
    min_election_timeout: float = 1
    max_election_timeout: float = 2
    heartbeat_interval: float = 0.1
    database_configs: dict = dict()
    machine_configs: dict = dict()


class ClusterConfigs(BaseModel):
    """
    Represents cluster configurations including peer information.

    Attributes:
        min_election_timeout (float): The minimum election timeout.
        max_election_timeout (float): The maximum election timeout.
        heartbeat_interval (float): The heartbeat interval.
        peers (list[Peer]): The list of peers in the cluster.
        database_configs (dict): Additional database configurations.
        machine_configs (dict): Additional machine configurations.
    """
    min_election_timeout: float
    max_election_timeout: float
    heartbeat_interval: float
    peers: list[Peer]
    database_configs: dict
    machine_configs: dict

    @property
    def vote_target(self) -> int:
        """
        Get the number of votes required for consensus.

        Returns:
            int: The number of votes required for consensus.
        """
        return (len(self.peers) // 2) + 1


class ClusterPingResponse(BaseModel):
    """
    Represents the response to a ping request in the Raft cluster.

    Attributes:
        term (int): The current term of the responding node.
        state (str): The state of the responding node.
        leader (str | None): The leader of the cluster, or None if unknown.
        commit_index (int): The commit index of the responding node.
        last_applied (int): The last applied index of the responding node.
        last_log_idx (int): The last log index of the responding node.
    """
    term: int
    state: str
    leader: str | None
    commit_index: int
    last_applied: int
    last_log_idx: int


class AppendEntry(BaseModel):
    """
    Represents an AppendEntries request in the Raft algorithm.

    Attributes:
        term (int): The current term of the leader.
        leader (str): The leader ID.
        previous_log_index (int): The index of the log entry immediately preceding the new ones.
        previous_log_term (int): The term of the log entry immediately preceding the new ones.
        leader_commit (int): The leader's commit index.
        entries (list[Log]): The log entries to append.
    """
    term: int
    leader: str
    previous_log_index: int
    previous_log_term: int
    leader_commit: int
    entries: list[Log]


class AppendEntryResponse(BaseModel):
    """
    Represents the response to an AppendEntries request in the Raft algorithm.

    Attributes:
        term (int): The current term of the responder.
        id (str): The ID of the responder.
        acknowledge (bool | int): Whether the entries were successfully appended.
    """
    term: int
    id: str
    acknowledge: bool | int


class RequestVote(BaseModel):
    """
    Represents a RequestVote RPC in the Raft algorithm.

    Attributes:
        term (int): The candidate's term.
        candidate_id (str): The ID of the candidate requesting the vote.
        last_log_index (int): The index of the candidate's last log entry.
        last_log_term (int): The term of the candidate's last log entry.
    """
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


class RequestVoteResponse(BaseModel):
    """
    Represents the response to a RequestVote RPC in the Raft algorithm.

    Attributes:
        term (int): The current term of the responder.
        id (str): The ID of the responder.
        vote_granted (bool): Whether the vote was granted.
    """
    term: int
    id: str
    vote_granted: bool