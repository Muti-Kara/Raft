from pydantic import BaseModel


class Log(BaseModel):
    term: int
    command: dict


class LogList(BaseModel):
    logs: list[Log] = list()

    def add_log(self, value: Log) -> int:
        self.logs.append(value)
        return len(self.logs) - 1

    def add_logs(self, index: int, value: 'LogList') -> None:
        self.logs[index:] = value.logs


class Peer(BaseModel):
    id: str
    host: str
    rpc_port: int
    exposed_port: int

    @property
    def rpc_address(self) -> tuple[str, int]:
        return self.host, self.rpc_port


class ClusterConfigs(BaseModel):
    min_election_timeout: float
    max_election_timeout: float
    heartbeat_interval: float
    peers: list[Peer]
    database_configs: dict
    machine_configs: dict

    @property
    def vote_target(self) -> int:
        return (len(self.peers) // 2) + 1


class ClusterPingResponse(BaseModel):
    term: int
    state: str
    leader: str | None
    commit_index: int
    last_applied: int
    last_log_idx: int


class AppendEntry(BaseModel):
    term: int
    leader: str
    previous_log_index: int
    previous_log_term: int
    leader_commit: int
    entries: list[Log]


class AppendEntryResponse(BaseModel):
    term: int
    id: str
    acknowledge: bool | int


class RequestVote(BaseModel):
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


class RequestVoteResponse(BaseModel):
    term: int
    id: str
    vote_granted: bool