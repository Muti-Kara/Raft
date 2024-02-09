from pydantic import BaseModel


class Log(BaseModel):
    """
    Represents a log entry in the Raft consensus algorithm.

    Attributes:
        term (int): The term of the log entry.
        command (dict): The command associated with the log entry.
    """
    term: int
    command: dict


class LogList(BaseModel):
    """
    Represents a list of log entries in the Raft consensus algorithm.

    Attributes:
        logs (list[Log]): List of log entries.
    """
    logs: list[Log] = list()

    def add_log(self, value: Log) -> int:
        """
        Adds a log entry to the log list.

        Args:
            value (Log): The log entry to add.

        Returns:
            int: The index at which the log entry was added.
        """
        self.logs.append(value)
        return len(self.logs) - 1

    def add_logs(self, index: int, value: 'LogList') -> None:
        """
        Adds multiple log entries starting from a specific index.

        Args:
            index (int): The index at which to start adding log entries.
            value (LogList): The list of log entries to add.
        """
        self.logs[index:] = value.logs