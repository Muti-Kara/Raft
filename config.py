import os

# Get node ID from environment variable, default to -1 if not set
NODE_ID = int(os.getenv('PEER_ID', -1))
# Get RPC port from environment variable, default to -1 if not set
NODE_RPC_PORT = int(os.getenv('PEER_RPC_PORT', -1))
# Get HTTP port from environment variable, default to -1 if not set
NODE_HTTP_PORT = int(os.getenv('PEER_HTTP_PORT', -1))
# Construct file path for storing node data
NODE_FILE = f"/app/data/node{NODE_ID}.pkl"

# Election timeout settings
MIN_ELECTION_TIMEOUT = 1  # Minimum election timeout in seconds
MAX_ELECTION_TIMEOUT = 2  # Maximum election timeout in seconds

# Heartbeat interval for leader in seconds
HEARTBEAT_INTERVAL = 0.1

# Interval for writing data to the database in seconds
DATABASE_WRITE = 10

# Peers dictionary mapping peer ID to (host, RPC port, HTTP port)
PEERS = {
    1: ("peer1", 15001, 5001),
    2: ("peer2", 15002, 5002),
    3: ("peer3", 15003, 5003),
    4: ("peer4", 15004, 5004),
    5: ("peer5", 15005, 5005),
}
