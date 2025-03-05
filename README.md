# Grekko

## Overview

Grekko is a secure, private cryptocurrency trading system with real-time connectivity to both centralized exchanges (CEXs) and decentralized exchanges (DEXs). It supports meme coin trading, private key/API secret management with military-grade encryption, and non-custodial execution through wallet integration.

## Features

- Real-time connectivity to CEXs (Coinbase Pro API, Binance Spot/Margin) & DEXs (Uniswap v3, PancakeSwap)
- Meme coin trading via direct DEX router contracts (Ethereum, BSC, Solana)
- Private key/API secret management with military-grade encryption
- Non-custodial execution through wallet integration

## Security Protocols

- Zero hardcoded credentials - 12FA architecture
- TLS 1.3 for all exchange communications
- HSM-like key storage using libsodium sealed boxes
- Gas estimation buffers for on-chain trades
- Time-weighted order slicing for large positions

## Getting Started

### Prerequisites

- Python 3.8+
- Docker
- Git

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/clduab11/grekko.git
   cd grekko
   ```

2. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up Docker:
   ```sh
   docker-compose up -d
   ```

### Configuration

1. Make the repository private:
   - Go to GitHub repository settings
   - Navigate to the "Danger Zone"
   - Click on "Make private"

2. Replace all testnet keys with `[REDACTED]` placeholders:
   - Open the configuration files
   - Replace any testnet keys with `[REDACTED]`

3. Add `.gitignore` entry for `*.grekko` vault files:
   - Open the `.gitignore` file
   - Add the following line:
     ```
     *.grekko
     ```

4. Implement pre-commit hooks for secret scanning:
   - Install pre-commit:
     ```sh
     pip install pre-commit
     ```
   - Create a `.pre-commit-config.yaml` file with the following content:
     ```yaml
     repos:
       - repo: https://github.com/pre-commit/pre-commit-hooks
         rev: v3.4.0
         hooks:
           - id: detect-secrets
     ```
   - Install the pre-commit hooks:
     ```sh
     pre-commit install
     ```

### Usage

1. Start the application:
   ```sh
   python src/main.py
   ```

2. Monitor the logs for any issues:
   ```sh
   tail -f logs/grekko.log
   ```

## Contributing

We welcome contributions from the community. Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
