import pickle
import rpyc

from raft.utils.models import Peer


class RaftCluster:
    def __init__(self) -> None:
        self.nodes: dict[int, Peer] = dict()
        self.count = 1

    def add_node(self, host: str, rpc_port: int, exposed_port: int):
        self.nodes[self.count] = Peer(
            id=str(self.count),
            host=host,
            rpc_port=rpc_port,
            exposed_port=exposed_port
        )
        rpyc.connect(host, rpc_port).root.cluster_join(self.count)
        self.count += 1

    def change_configs(self, new_configs):
        node_conns = [rpyc.connect(*node.rpc_address).root for node in self.nodes.values()]
        for node_conn in node_conns:
            node_conn.cluster_stop()
        for node_conn in node_conns:
            node_conn.cluster_config(pickle.dumps(new_configs))
        for node_conn in node_conns:
            node_conn.cluster_start()

    def check_nodes(self):
        node_conns = []
        for node in self.nodes.values():
            try:
                node_conns.append(rpyc.connect(*node[0].rpc_address).root)
            except:
                node_conns.append(None)
        return [pickle.loads(node_conn.ping()) if node_conn else None for node_conn in node_conns]

    def stop_node(self, node_id):
        rpyc.connect(*self.nodes[node_id].rpc_address).root.cluster_stop()

    def start_node(self, node_id):
        rpyc.connect(*self.nodes[node_id].rpc_address).root.cluster_start()