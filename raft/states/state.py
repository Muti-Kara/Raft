from .rpc_models import AppendEntry, RequestVote, AppendEntryResponse, RequestVoteResponse
from raft.utils.timer import FunctionTimer


class State:
    """
    Base class for states in the Raft consensus algorithm.

    Provides common functionality and interface for all state implementations.
    """
    def __init__(self, node, min_timeout, max_timeout) -> None:
        """
        Initializes a State instance.

        Args:
            node: The Raft node associated with this state.
            min_timeout: Minimum timeout for state transitions.
            max_timeout: Maximum timeout for state transitions.
        """
        from raft.node import RaftNode
        print(self.__class__.__name__, flush=True)
        self._node: RaftNode = node
        self._node.state = self
        self._timer = FunctionTimer(min_timeout, max_timeout, self.on_expire)

    def _change_state(self, NewState: 'State', new_term: int | None = None):
        """
        Changes the current state to a new state.

        Args:
            NewState (State): The new state to transition to.
            new_term (int | None, optional): The new term to set. Defaults to None.
        """
        if isinstance(self._node.state, NewState):
            return
        if new_term:
            self._node.data.current_term = new_term
        self._timer.stop()
        NewState(self._node)

    def become_follower(self, new_term: int | None = None):
        """
        Transition to the follower state.

        Args:
            new_term (int | None, optional): The new term to set. Defaults to None.
        """
        from .follower import Follower
        self._change_state(Follower, new_term)

    def become_candidate(self, new_term: int | None = None):
        """
        Transition to the candidate state.

        Args:
            new_term (int | None, optional): The new term to set. Defaults to None.
        """
        from .candidate import Candidate
        self._change_state(Candidate, new_term)

    def become_leader(self, new_term: int | None = None):
        """
        Transition to the leader state.

        Args:
            new_term (int | None, optional): The new term to set. Defaults to None.
        """
        from .leader import Leader
        self._change_state(Leader, new_term)

    def on_expire(self):
        """
        Method to handle state transition timeouts.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    def on_append_entry(self, ae: AppendEntry):
        """
        Method to handle incoming AppendEntry messages.

        Args:
            ae (AppendEntry): The incoming AppendEntry message.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    def on_append_entry_callback(self, res: AppendEntryResponse):
        """
        Method to handle AppendEntry response callbacks.

        Args:
            res (AppendEntryResponse): The AppendEntry response.

        Returns:
            Any: Additional information as needed.
        """
        return

    def on_request_vote(self, rv: RequestVote):
        """
        Method to handle incoming RequestVote messages.

        Args:
            rv (RequestVote): The incoming RequestVote message.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    def on_request_vote_callback(self, res: RequestVoteResponse):
        """
        Method to handle RequestVote response callbacks.

        Args:
            res (RequestVoteResponse): The RequestVote response.

        Returns:
            Any: Additional information as needed.
        """
        return

    def broadcast_rpc(self, peer_id, peer_addr):
        """
        Method to broadcast RPC messages to peers.

        Args:
            peer_id: The ID of the peer.
            peer_addr: The address of the peer.

        Returns:
            Any: Additional information as needed.
        """
        return