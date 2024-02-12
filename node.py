"""
This is an example implementation of a Raft node to connect to the cluster. 

To function properly, each node must have an exposed port (for external access types such as HTTP),
and an RPC port (for communication between peers and the cluster manager).

To use this implementation, you must extend two classes: BaseDatabase and BaseMachine.
This file provides an example implementation demonstrating how to extend these classes.

The BaseDatabase class handles storage and retrieval of Raft node state,
while the BaseMachine class defines the behavior and logic of the Raft node.

By following this example, you can implement your own Raft node with custom database and machine logic.

"""

from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
import pickle
import uuid
import os

from raft.utils.database import BaseDatabase
from raft.utils.machine import BaseMachine
from raft.utils.timer import FunctionTimer
from raft.utils.models import LogList
from raft.node import RaftNode

# Get RPC port from environment variable, default to -1 if not set
NODE_RPC_PORT = int(os.getenv('PEER_RPC_PORT', -1))
# Get HTTP port from environment variable, default to -1 if not set
NODE_EXPOSED_PORT = int(os.getenv('PEER_EXPOSED_PORT', -1))

# For database connections (You must change these with necessary information to connect your database)
# Database file path. Default to a unique file path in the /app/data directory
DATABASE_FILE = os.getenv('DATABASE_FILE', f"/app/data/node{uuid.uuid4()}.pkl")
# Boolean flag indicating whether to load existing database data. Default to False
DATABASE_LOAD = os.getenv('DATABASE_LOAD', False)



class KeyValueStoreMachine(BaseMachine):
    """
    Concrete implementation of BaseMachine.
    This machine provides functionality for a simple key-value store.
    """

    def configure(self, config):
        """
        Configure the key-value store machine.
        """
        self.store = {}

    def post_request(self, command):
        """
        Process a POST request for the key-value store.

        Args:
            command (dict): The command to be executed.

        Returns:
            tuple: A tuple containing the key-value pair and a boolean indicating success.
        """
        self.store[command["key"]] = command["value"]
        return (command["key"], command["value"]), True

    def get_request(self, command):
        """
        Process a GET request for the key-value store.

        Args:
            command (dict): The command to be executed.

        Returns:
            tuple: A tuple containing the value corresponding to the key and a boolean indicating success.
        """
        if self.store.get(command["key"], None):
            return self.store[command["key"]], True
        return None, False


class FileDatabase(BaseDatabase):
    """
    Concrete implementation of BaseDatabase.
    This database handles storage and retrieval of Raft node state in a file.
    """

    def configure(self, config: dict) -> None:
        """
        Configure the file database.

        Args:
            config (dict): Configuration parameters.
        """
        self._timer = FunctionTimer(config["database_write"], config["database_write"], self.auto_save)

    def connect(self) -> None:
        """
        Connect to the file database.
        """
        os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
        if DATABASE_LOAD:
            with open(DATABASE_FILE, "rb") as f:
                self.current_term, self.voted_for, self.logs = pickle.load(f)
        else:
            with open(DATABASE_FILE, "wb") as f:
                pickle.dump((self.current_term, self.voted_for, self.logs), f)

    def auto_save(self):
        """
        Automatically save the database state to file.
        """
        with open(DATABASE_FILE, "wb") as f:
            pickle.dump((self.current_term, self.voted_for, self.logs), f)
        self._timer.reset()

    @property
    def logs(self) -> LogList:
        """
        Get the logs from the database.

        Returns:
            LogList: The logs stored in the database (Pydantic model).
        """
        return self._logs

    @logs.setter
    def logs(self, value: LogList):
        """
        Set the logs in the database.

        Args:
            value (LogList): The logs to be set in the database (Pydantic model).
        """
        self._logs = value

    @property
    def current_term(self):
        """
        Get the current term from the database.

        Returns:
            int: The current term.
        """
        return self._current_term

    @current_term.setter
    def current_term(self, value):
        """
        Set the current term in the database.

        Args:
            value (int): The current term to be set.
        """
        self._current_term = value

    @property
    def voted_for(self):
        """
        Get the voted-for candidate from the database.

        Returns:
            str: The candidate ID that received the vote, or None if no vote has been given.
        """
        return self._voted_for

    @voted_for.setter
    def voted_for(self, value):
        """
        Set the voted-for candidate in the database.

        Args:
            value (str): The candidate ID to be set as voted-for, or None if no vote is given.
        """
        self._voted_for = value


node = RaftNode(
    machine=KeyValueStoreMachine(),
    data=FileDatabase(),
    rpc_port=NODE_RPC_PORT
)
app = FastAPI()


class Command(BaseModel):
    """
    Model representing a command for the Raft node.
    """
    key: str
    value: str


@app.get('/')
async def get_information():
    """
    Get information about the Raft node.

    Returns:
        dict: Information about the Raft node.
    """
    return {
        "node id": node.id,
        "current leader": node.current_leader,
        "current term": node.data.current_term,
        "commit index": node.commit_index,
        "last applied": node.last_applied,
        "total log count": len(node.data.logs.logs)
    }


@app.get('/storage')
def get_value(key: str):
    """
    Get a value from the key-value store.

    Args:
        key (str): The key to retrieve the value for.

    Returns:
        dict: Response containing the value and validity information.
    """
    res, is_leader = node.request(command={"key": key}, get=True)
    if is_leader:
        if res[1]:
            return {"response": res[0], "valid": node.last_applied == len(node.data.logs.logs) - 1}
        return {"response": "404 Not Found", "valid": node.last_applied == len(node.data.logs.logs) - 1}
    if res:
        return {"leader_url": f"http://{res.host}:{res.exposed_port}/storage?key={key}"}    
    return {"leader_url": f"404 Not Found", "key": key}


@app.post('/storage')
def post_value(command: Command):
    """
    Post a value to the key-value store.

    Args:
        command (Command): The command to post.

    Returns:
        dict: Response containing log index and command information.
    """
    res, is_leader = node.request(command.model_dump(), get=False)
    if is_leader:
        return {"log_index": res, "command": command}
    if res:
        return {"leader_url": f"http://{res.host}:{res.exposed_port}/storage", "request_body": command}
    return {"leader_url": f"404 Not Found", "request_body": command}


if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        executor.submit(node.run)
        executor.submit(uvicorn.run, app, host="0.0.0.0", port=NODE_EXPOSED_PORT)