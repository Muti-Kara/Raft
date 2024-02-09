"""
Example integration of this raft module. KeyValueStoreMachine and FileDatabase
can be re-implemented to fit in a new project. node.get_request and 
node.post_request methods are also rpc exposed but since a the node.append_entry
and node.request_vote methods are also exposed, this is not recommended.

You can check KeyValueStoreMachine and FileDatabase implementations from code.

List of required libraries:
- rpyc
- pydantic
"""

from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn

from raft.utils.machine import KeyValueStoreMachine  # Custom machine implementation
from raft.utils.database import FileDatabase  # Custom database implementation
from raft.node import RaftNode  # Raft consensus node implementation
import config  # Configuration settings

# Initialize a Raft node with custom machine and database implementations
node = RaftNode(Machine=KeyValueStoreMachine, Database=FileDatabase)

# Initialize a FastAPI application
app = FastAPI()

# Define a data model for post request
class Command(BaseModel):
    key: str
    value: str

@app.get('/')
async def get_information():
    """Route to get information about the Raft node"""
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
    """Route to retrieve a value from the Raft node's storage"""
    res, is_leader = node.get_request(command={"key": key})
    if is_leader:
        return {"response": res, "valid": node.last_applied == len(node.data.logs.logs) - 1}
    if res:
        return {"leader_url": f"http://{res[0]}:{res[1]}/storage?key={key}"}    
    return {"leader_url": f"404 Not Found", "key": key}

@app.post('/storage')
def post_value(command: Command):
    """Route to store a key-value pair in the Raft node's storage"""
    res, is_leader = node.post_request(command.model_dump())
    if is_leader:
        return {"log_index": res, "command": command}
    if res:
        return {"leader_url": f"http://{res[0]}:{res[1]}/storage", "request_body": command}
    return {"leader_url": f"404 Not Found", "request_body": command}


if __name__ == "__main__":
    # Start Raft node and FastAPI server concurrently
    with ThreadPoolExecutor() as executor:
        # Start Raft node
        executor.submit(node.run)
        # Start FastAPI server
        executor.submit(uvicorn.run, app, host="0.0.0.0", port=config.NODE_HTTP_PORT)