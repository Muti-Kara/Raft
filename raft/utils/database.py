import pickle
import os

from .timer import FunctionTimer
from .logs import LogList, Log
import config


class FileDatabase:
    def __init__(self, reset: bool = True) -> None:
        os.makedirs(os.path.dirname(config.NODE_FILE), exist_ok=True)

        if reset:
            self.logs = LogList(logs=[Log(term=0, command={"block": "create"})])
            self._state = {"current_term": 0, "voted_for": None}
        else:
            self.load()

        self._timer = FunctionTimer(config.DATABASE_WRITE, config.DATABASE_WRITE, self._auto_save)

    def _auto_save(self):
        with open(config.NODE_FILE, "wb") as f:
            pickle.dump((self._state, self.logs), f)
        self._timer.reset()

    def load(self):
        with open(config.NODE_FILE, "rb") as f:
            self._state, self.logs = pickle.load(f)

    @property
    def current_term(self):
        return self._state["current_term"]

    @current_term.setter
    def current_term(self, value):
        self._state["current_term"] = value

    @property
    def voted_for(self):
        return self._state["voted_for"]

    @voted_for.setter
    def voted_for(self, value):
        self._state["voted_for"] = value