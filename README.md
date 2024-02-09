# Raft Consensus Algorithm Implementation

This repository contains an implementation of the Raft consensus algorithm, designed for distributed systems. It has the following features:

- [x] Leader Election
- [x] Log Replication
- [x] Support for customizable state machines
- [x] An external example API for recording logs for a distributed key-value store
- [ ] Adding or removing members from the cluster

Currently nodes cluster is creating a simple distributed key-value store. If you'd like to use this for other purposes, look at the [Integration](#integration) section.

## Table of Contents

- [Background](#background)
- [Installation](#installation)
- [Integration](#integration)
- [Contributing](#contributing)
- [License](#license)

## Background

Raft is a consensus algorithm developed by Diego Ongaro and John Ousterhout in 2013. It's designed to be more understandable than Paxos while offering similar functionality. It's divided into three subproblems: leader election, log replication, and safety.

## Installation

To use this implementation of Raft, follow these steps:

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

## Integration

This Raft consensus algorithm implementation is designed to be adaptable and suitable for integration into various distributed systems projects. You can easily incorporate this implementation into your own projects by following these steps:

1. **Override BaseMachine Class**: To adapt this implementation to your specific use case, you can override the `BaseMachine` class from `raft.utils.machine`. This allows you to customize the behavior of the state machine according to your requirements.

### `post_request(command)`
The `post_request` method is responsible for applying commands to the state machine. In the context of the Raft consensus algorithm, this method ensures consistency across all nodes in the cluster by executing operations such as updating data or performing transactions. Custom Machines should override this method to define how commands are processed and applied to the state machine.

### `get_request(command)`
The `get_request` method handles requests for information or data retrieval from the state machine. In the Raft consensus algorithm, it plays a crucial role in handling queries from clients or other nodes in the cluster. Custom Machines should override this method to define how queries are processed and responses are generated.

By extending the `BaseMachine` class and providing implementations for these methods, you can customize the behavior of the state machine to suit your project's requirements.

2. **Implement Custom Database**: Create your own database implementations by subclassing `BaseDatabase` respectively. Current implementation of `FileDatabase` is not efficient and real-time.

By integrating this Raft consensus algorithm implementation into your projects, you can achieve robust and fault-tolerant distributed systems with ease.

**Note**: You may also consider extending the functionality of this Raft implementation by adding new RPC methods, state transitions, or additional features specific to your project.

## Contributing

Contributions are welcome! If you'd like to contribute to this Raft implementation, please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Create a new Pull Request

## License

This project is licensed under the [MIT License](LICENSE).
