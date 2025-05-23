# Grekko

![Version](https://img.shields.io/badge/version-1.2.0--beta-blue)
![Status](https://img.shields.io/badge/status-beta-green)
![Python](https://img.shields.io/badge/python-3.11-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![LLM](https://img.shields.io/badge/LLM--ensemble-powered-purple)
![Solana](https://img.shields.io/badge/solana-integrated-orange)

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
- **Sentiment & On-Chain Intelligence**: Social signal processing, dark web scanning, and blockchain analytics
- **Multi-Model Analysis**: Ensemble of specialized LLMs for complementary market insights

### Robust Trading Capabilities
- **Multi-Exchange Integration**: Seamless trading on major CEX and DEX platforms
- **Smart Order Routing**: Optimized execution across venues for best pricing
- **Risk Management**: Comprehensive position sizing, circuit breakers, and drawdown protection
- **Solana Sniper Module**: High-frequency detection and trading for new token launches
- **Privacy-Enhanced Execution**: Transaction mixing and address rotation for enhanced privacy

### Enterprise-Grade Security
- **Secure Credential Management**: Military-grade encryption for API keys and private keys
- **Continuous Monitoring**: Real-time system health and performance tracking
- **Configurable Safety Guardrails**: Fine-grained control over autonomous trading boundaries

## Agent Orchestration

Grekko's core innovation is its Multi-Agent Orchestration System utilizing an ensemble of specialized Large Language Models. Unlike single-model trading systems, Grekko distributes tasks across specialized agents:

- **Market Analyst Agent**: Technical analysis and trend identification
- **Risk Assessment Agent**: Portfolio risk evaluation and position sizing
- **Strategy Optimization Agent**: Performance analysis and parameter tuning
- **Execution Planning Agent**: Order routing and execution timing
- **Sentiment Analysis Agent**: Social media, news, and dark web sentiment tracking
- **Portfolio Management Agent**: Asset allocation and rebalancing
- **Market Regime Agent**: Identifying market phases and adapting strategies
- **Privacy Enhancement Agent**: Transaction obfuscation and security management

These agents collaborate under a master orchestration model using Claude-3.5-Sonnet, combining their specialized insights to form a unified trading intelligence. Each agent leverages a specialized LLM (GPT-4 or Claude variants) optimized for specific analysis types.

## Dual-Mode Operation

### Grekko Mode
Interactive trade assistance providing insights and recommendations while keeping the human in control:
- Strategy recommendations with detailed rationale from the LLM ensemble
- Risk assessment for potential trades
- Performance analytics and portfolio insights
- Learning from your trading preferences
- Sentiment and on-chain analysis with explanation

### Gordon Gekko Mode
Fully autonomous trading with MCP (Model Context Protocol) integration for independent operation:
- Autonomous market analysis and trading decisions
- Real-time execution on configured exchanges
- Self-adjusting strategies based on market conditions
- Privacy-enhanced transaction execution
- Comprehensive audit logs and performance reporting
- Automatic strategy adaptation to changing market regimes

## Specialized Trading Systems

### Paper Trading Environment

Test strategies with real market data but zero financial risk:

- **Realistic Simulation**: Accurate modeling of market conditions, slippage, and fees
- **Comprehensive Analytics**: Detailed performance metrics and risk analysis
- **Transition Planning**: Data-driven evaluation of readiness for live trading
- **Web Dashboard**: Real-time monitoring of paper trading performance

Learn more about paper trading in our [detailed documentation](docs/PAPER_TRADING.md).

### Solana Sniper System

High-frequency trading system for new Solana token launches:

- **Sub-second Detection**: WebSocket monitoring for instant new token discovery
- **Safety Analysis**: Automated rug pull detection and safety scoring
- **MEV Protection**: Jito bundle integration prevents frontrunning
- **Auto-scaling**: Dynamic position sizing based on safety scores
- **Real-time API**: WebSocket API for live trade monitoring

Learn more about the Solana Sniper in our [dedicated guide](SOLANA_SNIPER_README.md).

## Getting Started

> ⚠️ **NOTE**: While Grekko has progressed to beta status, we recommend starting with Paper Trading Mode to safely test strategies before using real funds.

### Prerequisites

- Python 3.11+
- Docker
- Git
- PostgreSQL

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

4. Set up PostgreSQL database:
   ```sh
   # Using Docker
   docker run -d \
     --name grekko-postgres \
     -e POSTGRES_USER=grekko \
     -e POSTGRES_PASSWORD=grekkopassword \
     -e POSTGRES_DB=grekko \
     -p 5432:5432 \
     postgres:14
   ```

5. Start with Docker:
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

2. Configure the LLM ensemble:
   ```yaml
   # In config/main.yaml, adjust LLM ensemble settings:
   llm_ensemble:
     enabled: true
     models:
       meta_model: "claude-3.5-sonnet"
       technical_analysis: "gpt-4"
       market_regime: "claude-3-opus"
       sentiment: "claude-3.5-sonnet"
       risk_assessment: "gpt-4"
     weights:
       technical: 0.3
       regime: 0.3
       sentiment: 0.2
       risk: 0.2
   ```

3. Enable Paper Trading (Recommended for Testing):
   ```yaml
   # In config/main.yaml, set:
   paper_trading:
     enabled: true
     account:
       name: "Paper Trading Account"
       initial_balances:
         USDT: 10000.0
   ```

4. Add exchange API credentials:
   ```sh
   python scripts/setup.sh --add-credential binance --key YOUR_API_KEY --secret YOUR_API_SECRET
   ```

5. Configure Solana Sniper (Optional):
   ```yaml
   # In config/main.yaml
   solana_sniper:
     enabled: true
     max_buy_amount_sol: 0.05
     min_safety_score: 70
     slippage_bps: 300
     use_jito: true
   ```

6. Set environment variables in a .env file:
   ```
   CONFIG_ENV=development
   LOG_LEVEL=INFO
   OPENAI_API_KEY=your_openai_api_key
   CLAUDE_API_KEY=your_claude_api_key
   DATABASE_URL=postgresql://grekko:grekkopassword@localhost:5432/grekko
   HELIUS_API_KEY=your_helius_api_key  # For Solana monitoring
   ```

7. Configure Solana Sniper (optional):
   ```sh
   # Generate a new Solana wallet if you don't have one
   solana-keygen new --no-bip39-passphrase
   
   # Add the wallet path to your .env file
   echo "SOLANA_WALLET_PATH=/path/to/keypair.json" >> .env
   ```

## Architecture

Grekko follows a modular architecture designed for flexibility, security, and performance:

- **Agent Orchestration Layer**: Manages the multi-agent LLM ensemble system and workflow
- **Data Ingestion Layer**: Collects and normalizes data from multiple sources
- **Analysis Layer**: Processes market data and generates insights
- **Strategy Layer**: Implements trading strategies and signals
- **Execution Layer**: Handles order routing and trade execution (centralized and decentralized)
- **Risk Management Layer**: Monitors and controls trading risk
- **Security Layer**: Protects credentials and communications
- **Privacy Layer**: Enhances transaction privacy through obfuscation techniques
- **UI Layer**: Provides monitoring and control interfaces

## Current Development Status

Grekko has progressed to **beta status** (v1.2.0) with all core components implemented and operational. Key milestones include:

- ✅ LLM ensemble multi-model system
- ✅ Dual-mode operation (assisted and autonomous)
- ✅ Comprehensive paper trading environment
- ✅ Integration with major exchanges (CEX and DEX)
- ✅ Advanced risk management system
- ✅ Secure credential management
- ✅ Solana Sniper module
- ✅ Decentralized execution architecture
- ✅ Privacy-enhanced transaction routing

### Under Development

- 🔄 Mobile companion app
- 🔄 Advanced analytics dashboard
- 🔄 Expanded cross-chain support
- 🔄 Zero-knowledge proof transaction privacy
- 🔄 DAO governance integration

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
- [Solana Sniper Guide](SOLANA_SNIPER_README.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Scaling Strategy](SCALING_STRATEGY.md)
- [Future Roadmap](FUTURE_ROADMAP.md)

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Disclaimer

Cryptocurrency trading involves significant risk. While Grekko provides sophisticated tools for trading, the developers are not responsible for any financial losses incurred through the use of this software. Always exercise caution, start with paper trading, and never invest funds you cannot afford to lose. The Solana Sniper module involves particularly high-risk trading activities and should only be used with careful consideration of potential losses.
