from pydantic import BaseModel

from raft.utils.logs import Log


class AppendEntry(BaseModel):
    """
    Represents an AppendEntries RPC message.

    Attributes:
        term (int): The term of the sender's log entry.
        leader (int): The ID of the leader sending the message.
        previous_log_index (int): The index of the log entry immediately preceding the new entries.
        previous_log_term (int): The term of the log entry immediately preceding the new entries.
        leader_commit (int): The leader's commit index.
        entries (list[Log]): The log entries to append to the receiver's log.
    """
    term: int
    leader: int
    previous_log_index: int
    previous_log_term: int
    leader_commit: int
    entries: list[Log]


class AppendEntryResponse(BaseModel):
    """
    Represents a response to an AppendEntries RPC message.

    Attributes:
        term (int): The term of the receiver's log.
        id (int): The ID of the receiver node.
        acknowledge (bool | int): Indicates whether the append entry request was successful. If successful it contains the largest acknowledged log's index.
    """
    term: int
    id: int
    acknowledge: bool | int


class RequestVote(BaseModel):
    """
    Represents a RequestVote RPC message.

    Attributes:
        term (int): The term of the sender's log.
        candidate_id (int): The ID of the candidate requesting the vote.
        last_log_index (int): The index of the candidate's last log entry.
        last_log_term (int): The term of the candidate's last log entry.
    """
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int


class RequestVoteResponse(BaseModel):
    """
    Represents a response to a RequestVote RPC message.

    Attributes:
        term (int): The term of the receiver's log.
        id (int): The ID of the receiver node.
        vote_granted (bool): Indicates whether the vote was granted to the candidate.
    """
    term: int
    id: int
    vote_granted: bool