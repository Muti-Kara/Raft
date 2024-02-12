from concurrent.futures import ThreadPoolExecutor

from raft.utils.models import AppendEntry, RequestVote, AppendEntryResponse, RequestVoteResponse
from raft.utils.timer import FunctionTimer


class State:
    """
    Abstract base class for defining states in the Raft algorithm.

    Subclasses represent different states (Follower, Candidate, Leader) of a Raft node.

    Attributes:
        node (RaftNode): The Raft node associated with the state.
        min_timeout (float): The minimum timeout for state transitions.
        max_timeout (float): The maximum timeout for state transitions.
        timer (FunctionTimer): Timer for managing state timeouts.
    """

    def __init__(self, node, min_timeout, max_timeout) -> None:
        """
        Initialize the State.

        Args:
            node (RaftNode): The Raft node associated with the state.
            min_timeout (float): The minimum timeout for state transitions.
            max_timeout (float): The maximum timeout for state transitions.
        """
        from raft.node import RaftNode
        print(self.__class__.__name__, flush=True)
        self._node: RaftNode = node
        self._node.state = self
        self._timer = FunctionTimer(min_timeout, max_timeout, self.on_expire)

    def _change_state(self, NewState: 'State', new_term: int | None = None):
        """
        Transition to a new state.

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
        Transition to the Follower state.

        Args:
            new_term (int | None, optional): The new term to set. Defaults to None.
        """
        from .follower import Follower
        self._change_state(Follower, new_term)

    def become_candidate(self, new_term: int | None = None):
        """
        Transition to the Candidate state.

        Args:
            new_term (int | None, optional): The new term to set. Defaults to None.
        """
        from .candidate import Candidate
        self._change_state(Candidate, new_term)

    def become_leader(self, new_term: int | None = None):
        """
        Transition to the Leader state.

        Args:
            new_term (int | None, optional): The new term to set. Defaults to None.
        """
        from .leader import Leader
        self._change_state(Leader, new_term)

    def on_expire(self):
        """
        Handle timeout expiration.
        """
        raise NotImplementedError

    def on_append_entry(self, ae: AppendEntry):
        """
        Handle an AppendEntries request.

        Args:
            ae (AppendEntry): The AppendEntries request to handle.
        """
        raise NotImplementedError

    def on_append_entry_callback(self, res: AppendEntryResponse):
        """
        Handle the response to an AppendEntries request.

        Args:
            res (AppendEntryResponse): The response to handle.
        """
        return

    def on_request_vote(self, rv: RequestVote):
        """
        Handle a RequestVote RPC.

        Args:
            rv (RequestVote): The RequestVote RPC to handle.
        """
        raise NotImplementedError

    def on_request_vote_callback(self, res: RequestVoteResponse):
        """
        Handle the response to a RequestVote RPC.

        Args:
            res (RequestVoteResponse): The response to handle.
        """
        return

    def broadcast_rpc(self):
        """
        Broadcast RPC requests to all peers in the cluster.
        """
        with ThreadPoolExecutor() as executor:
            for peer in self._node.peers.values():
                executor.submit(self.call_rpc, peer.id, peer.rpc_address)

    def call_rpc(self, peer_id, peer_addr):
        """
        Call an RPC request on a specific peer.

        Args:
            peer_id (str): The ID of the peer.
            peer_addr (tuple[str, int]): The address of the peer (host, port).

        Returns:
            None
        """
        return