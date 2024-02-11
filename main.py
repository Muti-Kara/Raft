from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn

from raft.utils.models import ClusterConfigs
from raft.cluster import RaftCluster

cluster = RaftCluster()
app = FastAPI()


class Configs(BaseModel):
    min_election_timeout: float = 1
    max_election_timeout: float = 2
    heartbeat_interval: float = 0.1
    database_configs: dict = {"database_write": 10, "reset": True}
    machine_configs: dict = dict()


class Node(BaseModel):
    host: str = "peer"
    rpc_port: int = 1500
    exposed_port: int = 500


@app.get('/')
async def get_informations():
    return cluster.check_nodes()


@app.post('/node')
def add_node(node: Node):
    cluster.add_node(**node.model_dump())


@app.post('/config')
def new_configs(new_configs: Configs):
    cluster.change_configs(ClusterConfigs(
        **(new_configs.model_dump()),
        peers=cluster.nodes.values()
    ))


@app.post('/node/{node_id}/start')
def start_node(node_id: int):
    cluster.start_node(node_id)


@app.post('/node/{node_id}/stop')
def stop_node(node_id: int):
    cluster.stop_node(node_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)