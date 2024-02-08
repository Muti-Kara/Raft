import os

NODE_ID = int(os.getenv('PEER_ID', -1))
NODE_RPC_PORT = int(os.getenv('PEER_RPC_PORT', -1))
NODE_HTTP_PORT = int(os.getenv('PEER_HTTP_PORT', -1))
NODE_DIR = f"/app/data/node{NODE_ID}/"

MIN_ELECTION_TIMEOUT = 1
MAX_ELECTION_TIMEOUT = 2
HEARTBEAT_INTERVAL = 0.1
DATABASE_WRITE = 10

PEERS = {
#   id   host    port
    1: ("peer1", 15001, 5001),
    2: ("peer2", 15002, 5002),
    3: ("peer3", 15003, 5003),
    4: ("peer4", 15004, 5004),
    5: ("peer5", 15005, 5005),
}