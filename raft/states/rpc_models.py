from pydantic import BaseModel

from raft.utils.logs import Log


class AppendEntry(BaseModel):
    term: int
    leader: int
    previous_log_index: int
    previous_log_term: int
    leader_commit: int
    entries: list[Log]


class AppendEntryResponse(BaseModel):
    term: int
    id: int
    success: int


class RequestVote(BaseModel):
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int


class RequestVoteResponse(BaseModel):
    term: int
    id: int
    vote_granted: bool