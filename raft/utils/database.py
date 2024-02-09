import pickle
import os

from .timer import FunctionTimer
from .logs import LogList, Log
import config


class BaseDatabase:
    """
    Abstract base class for database implementations.

    Provides an interface for accessing and modifying Raft node data.
    """
    def __init__(self, reset: bool) -> None:
        """
        Initializes the database instance.

        Args:
            reset (bool): Whether to reset the database or load from an existing state.
        """
        if reset:
            self.init()
        else:
            self.load()

    def init(self) -> None:
        """
        Initializes the database to its default state.
        
        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    def load(self) -> None:
        """
        Loads the database state from storage.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @property
    def logs(self) -> LogList:
        """
        Property to access the log entries in the database.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @property
    def current_term(self) -> int:
        """
        Property to access the current term in the database.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @current_term.setter
    def current_term(self, value: int) -> None:
        """
        Setter for the current term property.

        Args:
            value (int): The value to set as the current term.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @property
    def voted_for(self) -> int:
        """
        Property to access the voted for candidate ID in the database.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @voted_for.setter
    def voted_for(self, value: int) -> None:
        """
        Setter for the voted for candidate property.

        Args:
            value (int): The candidate ID to set as voted for.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError


class FileDatabase(BaseDatabase):
    """
    File-based implementation of the database.

    Data is stored in a file using pickle serialization.
    """
    def __init__(self, reset: bool = True) -> None:
        """
        Initializes the FileDatabase instance.

        Args:
            reset (bool, optional): Whether to reset the database. Defaults to True.
        """
        super().__init__(reset)
        os.makedirs(os.path.dirname(config.NODE_FILE), exist_ok=True)
        self._timer = FunctionTimer(config.DATABASE_WRITE, config.DATABASE_WRITE, self._auto_save)

    def _auto_save(self):
        """
        Automatically saves the database state to file at regular intervals.
        """
        with open(config.NODE_FILE, "wb") as f:
            pickle.dump((self._state, self._logs), f)
        self._timer.reset()

    def init(self):
        """
        Initializes the database with default values.
        """
        self._logs = LogList(logs=[Log(term=0, command={"block": "create"})])
        self._state = {"current_term": 0, "voted_for": None}

    def load(self):
        """
        Loads the database state from file.
        """
        with open(config.NODE_FILE, "rb") as f:
            self._state, self._logs = pickle.load(f)

    @property
    def logs(self):
        """
        Property to access the log entries in the database.
        """
        return self._logs

    @property
    def current_term(self):
        """
        Property to access the current term in the database.
        """
        return self._state["current_term"]

    @current_term.setter
    def current_term(self, value):
        """
        Setter for the current term property.
        """
        self._state["current_term"] = value

    @property
    def voted_for(self):
        """
        Property to access the voted for candidate ID in the database.
        """
        return self._state["voted_for"]

    @voted_for.setter
    def voted_for(self, value):
        """
        Setter for the voted for candidate property.
        """
        self._state["voted_for"] = value