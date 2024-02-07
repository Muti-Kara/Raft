import os

NODE_ID = int(os.getenv('PEER_ID'))
NODE_PORT = int(os.getenv('PEER_PORT'))
NODE_DIR = f"/app/data/node{NODE_ID}/"

ELECTION_TIMEOUT = 1000
HEARTBEAT_INTERVAL = 100
VOTE_CHECK_INTERVAL = 100
APPEND_ENTRY_EXPIRY = 1000
DATABASE_WRITE = 5000

PEERS = {
#   id   host    port
    1: ("peer1", 15001),
    2: ("peer2", 15002),
    3: ("peer3", 15003)
}