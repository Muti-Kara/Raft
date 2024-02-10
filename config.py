import os

# Get RPC port from environment variable, default to -1 if not set
NODE_RPC_PORT = int(os.getenv('PEER_RPC_PORT', -1))
# Get HTTP port from environment variable, default to -1 if not set
NODE_EXPOSED_PORT = int(os.getenv('PEER_EXPOSED_PORT', -1))
# Get secret key from environment variable, default to empty string if not set
NODE_SECRET_KEY = os.getenv('PEER_SECRET_KEY', "")