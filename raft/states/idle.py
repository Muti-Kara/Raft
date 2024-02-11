from .state import State


class Idle(State):
    def __init__(self, node) -> None:
        print(self.__class__.__name__, flush=True)
        self._node = node
        self._node.state = self

    def on_expire(self):
        return

    def on_append_entry(self, ae):
        return

    def on_request_vote(self, rv):
        return