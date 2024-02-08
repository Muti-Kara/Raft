from concurrent.futures import ThreadPoolExecutor
from fastapi.responses import RedirectResponse
from rpyc.utils.server import ThreadedServer
from pydantic import BaseModel
from fastapi import FastAPI

from raft.node import RaftNode
import raft.config as config
import uvicorn


class KeyValue(BaseModel):
    key: str
    value: str


node = RaftNode()
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
        "logs": node.data.logs.serialize(0)
    }

@app.get('/storage')
def get_value(key: str):
    res, is_leader = node.get_request(key=key)
    if is_leader:
        return res
    return {"leader_url": f"http://{res[0]}:{res[1]}/storage?key={key}"}

@app.post('/storage')
def get_value(body: KeyValue):
    res, is_leader = node.post_request(key=body.key, value=body.value)
    if is_leader:
        return res
    return {"leader_url": f"http://{res[0]}:{res[1]}/storage", "request_body": body}


if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        executor.submit(node.run)
        executor.submit(rpc.start)
        executor.submit(uvicorn.run, app, host="0.0.0.0", port=config.NODE_HTTP_PORT)