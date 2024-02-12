# Raft Consensus Algorithm Implementation with Cluster Manager

This repository contains an implementation of the Raft consensus algorithm, designed for distributed systems. In addition to the core Raft features such as leader election and log replication, it includes a cluster manager for managing the membership of the cluster. However, it's important to note that the membership change rules in this implementation may not strictly adhere to the Raft paper. Instead, they are handled in a more centralized manner within the cluster manager.

## Key Features

- [x] Leader Election
- [x] Log Replication
- [x] Support for Customizable State Machines
- [x] Example API for Recording Logs for a Distributed Key-Value Store
- [x] Cluster Manager for Adding or Removing Members from the Cluster

This implementation primarily focuses on providing a basic Raft consensus algorithm with additional functionalities for managing the cluster's membership.

If you'd like to use this implementation for purposes other than a distributed key-value store, you can adapt it according to your specific requirements. See the [Integration](#integration) section for more details.


## Table of Contents

- [Background](#background)
- [Installation](#installation)
- [Integration](#integration)
- [Contributing](#contributing)
- [Package Overview](#package-overview)
- [License](#license)


## Background

Raft is a consensus algorithm developed in 2013 by Diego Ongaro and John Ousterhout as an alternative to Paxos, aiming for better understandability without sacrificing functionality. It addresses three key challenges:

- **Leader Election**: Raft ensures each term has a single leader responsible for client requests, like appending log entries.
  
- **Log Replication**: The leader replicates log entries to all nodes, ensuring consistency across the cluster.

- **Safety**: Raft guarantees safety by ensuring committed log entries are replicated to all nodes, preventing inconsistencies.

Raft involves state transitions between followers, candidates, and leaders, depending on communication and election outcomes. Understanding these transitions is crucial for grasping how Raft achieves consensus in distributed systems.


## Installation

To use this implementation of Raft, you have two options:

### Option 1: Install from PyPI

1. Install the `raft-cluster` package via pip:
    ```bash
    pip install raft-cluster
    ```

2. Run the cluster manager using the following command:
    ```bash
    run-cluster-manager
    ```

3. Use docker-compose to run the peers:
    ```bash
    docker-compose up
    ```

### Option 2: Install from Source

1. Clone the repository:
    ```bash
    git clone https://github.com/Muti-Kara/raft.git
    ```

2. Navigate to the cloned directory:
    ```bash
    cd raft
    ```

3. Use docker-compose to run the peers:
    ```bash
    docker-compose up
    ```

The cluster manager runs on port 8000, while the HTTP servers for nodes run on ports 5001-5005, and the RPC endpoints for nodes run on ports 15001-15005.


## Integration

Integrating this Raft consensus algorithm implementation into your distributed systems projects is straightforward. Follow these steps to incorporate it into your own projects:

1. **Customize the BaseMachine Class**: Tailor this implementation to your specific use case by overriding the `BaseMachine` class found in `raft.utils.machine`. This customization allows you to adjust the behavior of the state machine according to your project's requirements.

    - **post_request(command)**: This method applies commands to the state machine, ensuring consistency across all nodes in the cluster. It executes operations such as updating data or performing transactions. Customize this method in your own `BaseMachine` subclass to define how commands are processed and applied to the state machine.

    - **get_request(command)**: Handles requests for information or data retrieval from the state machine. It is crucial for processing queries from clients or other nodes in the cluster. Override this method in your `BaseMachine` subclass to define how queries are processed and responses are generated.

    By extending the `BaseMachine` class and providing implementations for these methods, you can tailor the behavior of the state machine to meet your project's specific requirements.

2. **Implement Custom Database**: Develop your database implementations by subclassing `BaseDatabase`. The current implementation, `FileDatabase`, may not be suitable for real-time and efficient use cases.

Integrating this Raft consensus algorithm into your projects enables you to build robust and fault-tolerant distributed systems seamlessly.


## Contributing

Contributions are welcome! If you'd like to contribute to this Raft implementation, please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Create a new Pull Request

## Package Overview

The Raft consensus algorithm implementation is organized into several packages, each serving a specific purpose. Here's an overview of the main packages and their contents:

- **main.py**: Main server for cluster management.
  - Responsible for handling HTTP requests and managing the cluster's configuration and state transitions.

- **node.py**: Example concrete implementation of a Raft node for a simple key-value store.
  - Demonstrates how to use the Raft algorithm to build a distributed system with basic key-value store functionality.

- **raft**: Core packages for Raft consensus algorithm.
  - Contains essential classes and utilities for implementing the Raft consensus algorithm.

  - **node.py**: Contains the `RaftNode` class.
    - This class represents a single node in the Raft cluster and provides methods for handling RPC requests.

  - **cluster.py**: Contains the `Cluster` class.
    - Responsible for managing the cluster configuration, maintaining information about all nodes in the cluster.

  - **utils**: Utilities used throughout the Raft implementation.
    - **timer.py**: Provides functionality for managing timers used for timeout and periodic events.
    - **models.py**: Defines Pydantic models for representing data structures used in the Raft algorithm, such as logs, cluster configurations, and RPC message payloads.
    - **machine.py**: Contains the `BaseMachine` class, which defines the interface for custom state machine implementations.
    - **database.py**: Defines the `BaseDatabase` interface for creating custom database implementations to store cluster data.

  - **states**: Contains classes representing different states of a Raft node.
    - **state.py**: Defines the base `State` class, which serves as the parent class for all state implementations.
    - **idle.py**: Represents the idle state of a Raft node, where it is not actively participating in leader election or log replication.
    - **follower.py**: Represents the follower state of a Raft node, where it awaits instructions from the leader and responds to RPC requests.
    - **candidate.py**: Represents the candidate state of a Raft node, where it initiates leader election and requests votes from other nodes.
    - **leader.py**: Represents the leader state of a Raft node, where it coordinates log replication and manages the cluster's consistency and consensus.


## License

This project is licensed under the [MIT License](LICENSE).
