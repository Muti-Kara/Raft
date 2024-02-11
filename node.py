from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
import pickle
import os

from raft.utils.database import BaseDatabase
from raft.utils.machine import BaseMachine
from raft.utils.timer import FunctionTimer
from raft.utils.models import LogList
from raft.node import RaftNode
import config


class KeyValueStoreMachine(BaseMachine):
    def configure(self, config):
        self.store = {}

    def post_request(self, command):
        self.store[command["key"]] = command["value"]
        return (command["key"], command["value"]), True

    def get_request(self, command):
        if self.store.get(command["key"], None):
            return self.store[command["key"]], True
        return None, False


class FileDatabase(BaseDatabase):
    def configure(self, config: dict) -> None:
        self._timer = FunctionTimer(config["database_write"], config["database_write"], self.auto_save)

    def connect(self) -> None:
        os.makedirs(os.path.dirname(config.DATABASE_FILE), exist_ok=True)
        if config.DATABASE_LOAD:
            with open(config.DATABASE_FILE, "rb") as f:
                self.current_term, self.voted_for, self.logs = pickle.load(f)
        else:
            with open(config.DATABASE_FILE, "wb") as f:
                pickle.dump((self.current_term, self.voted_for, self.logs), f)

    def auto_save(self):
        with open(config.DATABASE_FILE, "wb") as f:
            pickle.dump((self.current_term, self.voted_for, self.logs), f)
        self._timer.reset()

    @property
    def logs(self) -> LogList:
        return self._logs

    @logs.setter
    def logs(self, value: LogList):
        self._logs = value

    @property
    def current_term(self):
        return self._current_term

    @current_term.setter
    def current_term(self, value):
        self._current_term = value

    @property
    def voted_for(self):
        return self._voted_for

    @voted_for.setter
    def voted_for(self, value):
        self._voted_for = value


node = RaftNode(Machine=KeyValueStoreMachine, Database=FileDatabase)
app = FastAPI()


class Command(BaseModel):
    key: str
    value: str


@app.get('/')
async def get_information():
    return {
        "node id": node.id,
        "current leader": node.current_leader['id'],
        "current term": node.data.current_term,
        "commit index": node.commit_index,
        "last applied": node.last_applied,
        "total log count": len(node.data.logs.logs)
    }


@app.get('/storage')
def get_value(key: str):
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
    res, is_leader = node.request(command.model_dump(), get=False)
    if is_leader:
        return {"log_index": res, "command": command}
    if res:
        return {"leader_url": f"http://{res.host}:{res.exposed_port}/storage", "request_body": command}
    return {"leader_url": f"404 Not Found", "request_body": command}


if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        executor.submit(node.run)
        executor.submit(uvicorn.run, app, host="0.0.0.0", port=config.NODE_EXPOSED_PORT)