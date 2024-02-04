import os

NODE_ID = os.getenv('PEER_ID')
NODE_PORT = os.getenv('PEER_PORT')

PEERS = [
    (1, "peer1", 15001),
    (2, "peer2", 15002),
    (3, "peer3", 15003)
]