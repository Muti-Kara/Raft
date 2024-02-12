import pickle
import rpyc

from raft.utils.models import Peer


class RaftCluster:
    """
    The RaftCluster class represents the cluster manager for a Raft-based distributed system.

    It provides methods for managing the cluster, such as adding nodes, changing configurations, and monitoring node status.

    Attributes:
        nodes (dict): A dictionary containing information about all nodes in the cluster.
    """

    def __init__(self) -> None:
        """Initialize the RaftCluster."""
        self.nodes: dict[str, Peer] = dict()

    def add_node(self, peer: Peer):
        """
        Add a new node to the cluster.

        Args:
            peer (Peer): The Peer object representing the node to be added to the cluster.

        This method adds the specified node to the cluster and triggers the cluster_join RPC on the node.
        """
        self.nodes[peer.id] = peer
        rpyc.connect(*peer.rpc_address).root.cluster_join(peer.id)

    def change_configs(self, new_configs):
        """
        Change the configurations of all nodes in the cluster.

        Args:
            new_configs: The new configurations to be applied to all nodes in the cluster.

        This method stops all nodes, applies the new configurations, and then restarts the nodes.
        """
        node_conns = [rpyc.connect(*node.rpc_address).root for node in self.nodes.values()]
        for node_conn in node_conns:
            node_conn.cluster_stop()
        for node_conn in node_conns:
            node_conn.cluster_config(pickle.dumps(new_configs))
        for node_conn in node_conns:
            node_conn.cluster_start()

    def check_nodes(self):
        """
        Check the status of all nodes in the cluster.

        Returns:
            dict: A dictionary containing information about each node in the cluster.

        This method retrieves information about each node by sending cluster_ping RPCs.
        """
        node_infos = dict()
        for node_id, node in self.nodes.items():
            try:
                node_infos[node_id] = pickle.loads(rpyc.connect(*node.rpc_address).root.cluster_ping()).model_dump()
                node_infos[node_id].update(
                    {
                        "host": node.host,
                        "rpc port": node.rpc_port,
                        "exposed port": node.exposed_port
                    }
                )
            except:
                node_infos[node_id] = None
        return node_infos

    def stop(self):
        """Stop all nodes in the cluster."""
        for node in self.nodes.values():
            rpyc.connect(*node.rpc_address).root.cluster_stop()
    
    def start(self):
        """Start all nodes in the cluster."""
        for node in self.nodes.values():
            rpyc.connect(*node.rpc_address).root.cluster_start()

    def stop_node(self, node_id):
        """
        Stop a specific node in the cluster.

        Args:
            node_id (str): The ID of the node to be stopped.
        """
        rpyc.connect(*self.nodes[node_id].rpc_address).root.cluster_stop()

    def start_node(self, node_id):
        """
        Start a specific node in the cluster.

        Args:
            node_id (str): The ID of the node to be started.
        """
        rpyc.connect(*self.nodes[node_id].rpc_address).root.cluster_start()