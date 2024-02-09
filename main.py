from concurrent.futures import ThreadPoolExecutor
from rpyc.utils.server import ThreadedServer
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn

from raft.utils.machine import KeyStoreMachine
from raft.utils.database import FileDatabase
from raft.node import RaftNode
import config


class Command(BaseModel):
    key: str
    value: str


node = RaftNode(Machine=KeyStoreMachine, Database=FileDatabase)
rpc = ThreadedServer(node, port=config.NODE_RPC_PORT)
app = FastAPI()

@app.get('/')
def get_information():
    return {
        "node id": node.id,
        "current leader": node.current_leader['id'],
        "current term": node.data.current_term,
        "voted for": node.data.voted_for,
        "commit index": node.commit_index,
        "last applied": node.last_applied,
        "logs": node.data.logs.model_dump()
    }

@app.get('/storage')
def get_value(key: str):
    res, is_leader = node.get_request(command={"key": key})
    if is_leader:
        return res
    return {"leader_url": f"http://{res[0]}:{res[1]}/storage?key={key}"}

@app.post('/storage')
def get_value(command: Command):
    res, is_leader = node.post_request(command.model_dump())
    if is_leader:
        return res
    return {"leader_url": f"http://{res[0]}:{res[1]}/storage", "request_body": command}

if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        executor.submit(node.run)
        executor.submit(rpc.start)
        executor.submit(uvicorn.run, app, host="0.0.0.0", port=config.NODE_HTTP_PORT)