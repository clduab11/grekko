# Grekko

![Version](https://img.shields.io/badge/version-1.0.0--beta-blue)
![Status](https://img.shields.io/badge/status-beta-green)
![Python](https://img.shields.io/badge/python-3.11-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![LLM](https://img.shields.io/badge/LLM-powered-purple)

## Vision

Grekko is a next-generation AI-powered cryptocurrency trading platform built as a multi-agent orchestration system. Moving beyond conventional algorithmic trading, Grekko harnesses the power of specialized Large Language Models (LLMs) to form a collaborative intelligence network that analyzes markets, generates trading insights, and executes strategies with precision. Designed for both automated and assisted trading, Grekko bridges the gap between sophisticated institutional trading systems and accessible retail tools.

## Key Features

### Multi-Agent Architecture
- **Agent Orchestration System**: Collaborative network of specialized LLM agents working together
- **Autonomous Decision Making**: Advanced AI-powered strategy development and execution
- **Dual-Mode Operation**: Choose between fully autonomous trading or assisted decision support

### Comprehensive Market Intelligence
- **Multi-Source Data Integration**: Real-time data from exchanges, blockchains, and social platforms
- **Advanced Market Analysis**: Sophisticated pattern recognition and market regime classification
- **Sentiment & On-Chain Intelligence**: Social signal processing and blockchain analytics

### Robust Trading Capabilities
- **Multi-Exchange Integration**: Seamless trading on major CEX and DEX platforms
- **Smart Order Routing**: Optimized execution across venues for best pricing
- **Risk Management**: Comprehensive position sizing, circuit breakers, and drawdown protection

### Enterprise-Grade Security
- **Secure Credential Management**: Military-grade encryption for API keys and private keys
- **Continuous Monitoring**: Real-time system health and performance tracking
- **Configurable Safety Guardrails**: Fine-grained control over autonomous trading boundaries

## Agent Orchestration

Grekko's core innovation is its Multi-Agent Orchestration System. Unlike single-model trading systems, Grekko distributes tasks across specialized agents:

- **Market Analyst Agent**: Technical analysis and trend identification
- **Risk Assessment Agent**: Portfolio risk evaluation and position sizing
- **Strategy Optimization Agent**: Performance analysis and parameter tuning
- **Execution Planning Agent**: Order routing and execution timing
- **Sentiment Analysis Agent**: Social media and news sentiment tracking
- **Portfolio Management Agent**: Asset allocation and rebalancing

These agents collaborate under a master orchestrator, combining their specialized insights to form a unified trading intelligence.

## Dual-Mode Operation

### Grekko Mode
Interactive trade assistance providing insights and recommendations while keeping the human in control:
- Strategy recommendations with detailed rationale
- Risk assessment for potential trades
- Performance analytics and portfolio insights
- Learning from your trading preferences

### Gordon Gekko Mode
Fully autonomous trading with MCP (Model Context Protocol) integration for independent operation:
- Autonomous market analysis and trading decisions
- Real-time execution on configured exchanges
- Self-adjusting strategies based on market conditions
- Comprehensive audit logs and performance reporting

## Paper Trading System

Test strategies with real market data but zero financial risk:

- **Realistic Simulation**: Accurate modeling of market conditions, slippage, and fees
- **Comprehensive Analytics**: Detailed performance metrics and risk analysis
- **Transition Planning**: Data-driven evaluation of readiness for live trading
- **Web Dashboard**: Real-time monitoring of paper trading performance

Learn more about paper trading in our [detailed documentation](docs/PAPER_TRADING.md).

## Getting Started

> ⚠️ **NOTE**: While Grekko has progressed to beta status, we recommend starting with Paper Trading Mode to safely test strategies before using real funds.

### Prerequisites

- Python 3.11+
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

3. Set up credential storage:
   ```sh
   mkdir -p ~/.grekko
   python scripts/setup.sh --init-vault
   ```

4. Start with Docker:
   ```sh
   # For development
   docker-compose -f docker/docker-compose.yml up -d
   
   # For testing
   docker-compose -f docker/docker-compose.test.yml up -d
   
   # For production
   docker-compose -f docker/docker-compose.prod.yml up -d
   ```

### Configuration

1. Configure the agent orchestration system:
   ```sh
   cp config/agent_config.yaml.example config/agent_config.yaml
   # Edit the file to set your desired parameters
   ```

2. Enable Paper Trading (Recommended for Testing):
   ```yaml
   # In config/main.yaml, set:
   paper_trading:
     enabled: true
     account:
       name: "Paper Trading Account"
       initial_balances:
         USDT: 10000.0
   ```

3. Add exchange API credentials:
   ```sh
   python scripts/setup.sh --add-credential binance --key YOUR_API_KEY --secret YOUR_API_SECRET
   ```

4. Set environment variables in a .env file:
   ```
   CONFIG_ENV=development
   LOG_LEVEL=INFO
   OPENAI_API_KEY=your_openai_api_key
   ```

## Architecture

Grekko follows a modular architecture designed for flexibility, security, and performance:

- **Agent Orchestration Layer**: Manages the multi-agent system and workflow
- **Data Ingestion Layer**: Collects and normalizes data from multiple sources
- **Analysis Layer**: Processes market data and generates insights
- **Strategy Layer**: Implements trading strategies and signals
- **Execution Layer**: Handles order routing and trade execution
- **Risk Management Layer**: Monitors and controls trading risk
- **Security Layer**: Protects credentials and communications
- **UI Layer**: Provides monitoring and control interfaces

## Current Development Status

Grekko has progressed to **beta status** with all core components implemented and operational. Key milestones include:

- ✅ Complete multi-agent orchestration system
- ✅ Dual-mode operation (assisted and autonomous)
- ✅ Comprehensive paper trading environment
- ✅ Integration with major exchanges (CEX and DEX)
- ✅ Advanced risk management system
- ✅ Secure credential management

### Under Development

- 🔄 Mobile companion app
- 🔄 Advanced analytics dashboard
- 🔄 Extended exchange integrations
- 🔄 Enhanced on-chain intelligence

## Contributing

Grekko welcomes contributions from the community. To contribute:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Write tests for your features
5. Submit a pull request

Please review our contribution guidelines in the CONTRIBUTING.md file before submitting.

## Documentation

- [Paper Trading Guide](docs/PAPER_TRADING.md)
- [Agent Orchestration](docs/AGENT_ORCHESTRATION.md)
- [Decentralized Execution](docs/DECENTRALIZED_EXECUTION.md)
- [LLM Ensemble Design](docs/LLM_ENSEMBLE_DESIGN.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN_PHASE2.md)

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Disclaimer

Cryptocurrency trading involves significant risk. While Grekko provides sophisticated tools for trading, the developers are not responsible for any financial losses incurred through the use of this software. Always exercise caution, start with paper trading, and never invest funds you cannot afford to lose.
