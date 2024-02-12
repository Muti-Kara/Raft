from .state import State

class Idle(State):
    """
    State representing an idle state for a peer.

    This state is not part of the original Raft algorithm, but is used by the cluster manager to gracefully
    separate a peer from the cluster and make it stop.

    Attributes:
        node (RaftNode): The Raft node associated with the state.
    """

    def __init__(self, node) -> None:
        """
        Initialize the Idle state.

        Args:
            node (RaftNode): The Raft node associated with the state.
        """
        print(self.__class__.__name__, flush=True)
        self._node = node
        self._node.state = self

    def on_expire(self):
        """
        Handle timeout expiration (no-op in this state).
        """
        return

    def on_append_entry(self, ae):
        """
        Handle an AppendEntries request (no-op in this state).

        Args:
            ae (AppendEntry): The AppendEntries request.
        """
        return

    def on_request_vote(self, rv):
        """
        Handle a RequestVote RPC (no-op in this state).

        Args:
            rv (RequestVote): The RequestVote RPC.
        """
        return