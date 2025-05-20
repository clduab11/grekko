# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Description

Grekko is a secure, private cryptocurrency trading system with real-time connectivity to both centralized exchanges (CEXs) and decentralized exchanges (DEXs). It supports meme coin trading, private key/API secret management with encryption, and non-custodial execution through wallet integration.

## Commands

### Setup and Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks for secret scanning
pip install pre-commit
pre-commit install

# Setup Docker environment
docker-compose up -d
```

### Running the Application

```bash
# Start the main application
python src/main.py

# Monitor logs
tail -f logs/grekko.log
```

### Testing

```bash
# Run backtests
python scripts/backtest.py

# Run unit tests (assuming pytest)
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

### Security

```bash
# Run secret detection scan
pre-commit run detect-secrets --all-files
```

## Architecture

The Grekko codebase follows a modular architecture with the following key components:

1. **Data Ingestion Layer**
   - Connects to exchanges (CEX/DEX), blockchain data sources, and social media
   - Processes and normalizes data from multiple sources
   - Provides real-time data streaming

2. **Strategy Layer**
   - Implements various trading strategies (arbitrage, mean reversion, momentum, sentiment)
   - Strategy manager that can switch between strategies based on market conditions
   - Position sizing and trade evaluation

3. **AI Adaptation Layer**
   - Machine learning models for market prediction
   - Reinforcement learning environment for adaptive trading
   - Ensemble methods for strategy selection

4. **Execution Layer**
   - Handles order execution on both CEX and DEX platforms
   - Smart contract integration for on-chain trading
   - Latency optimization for high-frequency trading

5. **Risk Management Layer**
   - Position monitoring and circuit breakers
   - Exposure calculation and risk limits
   - Stop-loss and trailing stop management
   - Privacy-focused components (address rotation, transaction mixing)

6. **Alpha Generation**
   - Alternative data analysis
   - On-chain intelligence
   - Social sentiment analysis
   - Volatility and liquidity monitoring

7. **Market Analysis**
   - Algorithmic activity detection
   - Market regime classification
   - Regulatory compliance scanning
   - Trending asset identification

## Configuration

The system uses YAML configuration files in the `config/` directory:

- `main.yaml`: Core configuration including logging, database, and risk parameters
- `exchanges.yaml`: Exchange-specific configurations 
- `strategies.yaml`: Strategy parameters and settings
- `tokens.yaml`: Token configurations
- `risk_parameters.yaml`: Risk management parameters

Sensitive information should never be committed to the repository. The system uses a secure vault (`config_vault` in `main.yaml`) for storing encrypted API keys and private keys.

## Security Protocols

- All API keys and private keys must be stored in the encrypted vault, never in code
- All code changes are scanned for secrets using pre-commit hooks
- Network communications use TLS 1.3
- All `.grekko` vault files are ignored by git