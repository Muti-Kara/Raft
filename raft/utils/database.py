from .models import LogList, Log

class BaseDatabase:
    """
    Abstract base class for defining the interface of a Raft node's database.

    Subclasses must implement methods to connect to the database and handle data retrieval and storage.

    Attributes:
        None
    """

    def __init__(self) -> None:
        """
        Initialize the BaseDatabase.

        Sets default values for logs, current_term, and voted_for.
        """
        self.logs = LogList(logs=[Log(term=0, command={"block": "create"})])
        self.current_term = 0
        self.voted_for = None
        self.connect()

    def connect(self) -> None:
        """
        Connect to the database.

        This method should be implemented by subclasses to establish a connection to the database.
        """
        raise NotImplementedError

    def configure(self, config) -> None:
        """
        Configure the database.

        This method should be implemented by subclasses to configure the database with the provided parameters.

        Args:
            config: Configuration parameters for the database.
        """
        raise NotImplementedError    

    @property
    def logs(self) -> LogList:
        """
        Get the logs from the database.

        Returns:
            LogList: The logs stored in the database.
        """
        raise NotImplementedError

    @logs.setter
    def logs(self, value: LogList):
        """
        Set the logs in the database.

        Args:
            value (LogList): The logs to be set in the database.
        """
        raise NotImplementedError

    @property
    def current_term(self) -> int:
        """
        Get the current term from the database.

        Returns:
            int: The current term stored in the database.
        """
        raise NotImplementedError

    @current_term.setter
    def current_term(self, value: int) -> None:
        """
        Set the current term in the database.

        Args:
            value (int): The current term to be set in the database.
        """
        raise NotImplementedError

    @property
    def voted_for(self) -> str | bool:
        """
        Get the voted-for candidate from the database.

        Returns:
            str | bool: The ID of the candidate voted for, or a boolean indicating if no vote has been cast.
        """
        raise NotImplementedError

    @voted_for.setter
    def voted_for(self, value: str | bool) -> None:
        """
        Set the voted-for candidate in the database.

        Args:
            value (str | bool): The ID of the candidate to be set as voted for, or a boolean indicating no vote.
        """
        raise NotImplementedError