# Raft Consensus Algorithm Implementation

This repository contains an implementation of the Raft consensus algorithm, designed for distributed systems. It has the following features:

- [x] Having a preconfigured peer cluster
    - [x] Append Entry and Request Vote RPC's
    - [x] Tested against network delays
- [x] An external API for recording logs
- [ ] Adding or removing members from the cluster
- [ ] Making this suitable for integrating into other projects (Partially done!)

## Table of Contents

- [Background](#background)
- [Installation](#installation)
- [Usage](#usage)
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

## Usage

This repository is not yet ready for integration into other projects. Please wait for updates.

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