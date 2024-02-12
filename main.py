from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn

from raft.utils.models import ClusterConfigs, ClusterConfigsWithoutPeers, Peer
from raft.cluster import RaftCluster

cluster = RaftCluster()
app = FastAPI()


@app.get('/')
async def get_informations():
    """
    Get information about the nodes in the Raft cluster.

    Returns:
        dict: Information about the nodes in the Raft cluster.
    """
    return cluster.check_nodes()


@app.post('/node')
def add_node(node: Peer):
    """
    Add a new node to the Raft cluster.

    Args:
        node (Peer): The details of the node to be added.
    """
    cluster.add_node(node)


@app.post('/config')
def new_configs(new_configs: ClusterConfigsWithoutPeers):
    """
    Update the configurations of the Raft cluster.

    Args:
        new_configs (ClusterConfigsWithoutPeers): The new configurations to be applied.
    """
    cluster.change_configs(ClusterConfigs(
        **(new_configs.model_dump()),
        peers=cluster.nodes.values()
    ))


@app.post('/node/start')
def start():
    """
    Start all nodes in the Raft cluster.
    """
    cluster.start()


@app.post('/node/stop')
def stop():
    """
    Stop all nodes in the Raft cluster.
    """
    cluster.stop()


@app.post('/node/{node_id}/start')
def start_node(node_id: str):
    """
    Start a specific node in the Raft cluster.

    Args:
        node_id (str): The ID of the node to start.
    """
    cluster.start_node(node_id)


@app.post('/node/{node_id}/stop')
def stop_node(node_id: str):
    """
    Stop a specific node in the Raft cluster.

    Args:
        node_id (str): The ID of the node to stop.
    """
    cluster.stop_node(node_id)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Raft Cluster Manager")
    parser.add_argument("-h", "--host", default="0.0.0.0", help="Host address")
    parser.add_argument("-p", "--port", default=8000, type=int, help="Port number")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()