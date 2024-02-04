from dataclasses import dataclass


@dataclass
class AppendEntry:
    leader: int


@dataclass
class RequestVote:
    peer: int