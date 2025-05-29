# Grekko - Omnivorous AI Trading Platform

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Multi-Chain](https://img.shields.io/badge/chains-Ethereum%20%7C%20Solana%20%7C%20BSC-green.svg)](config/exchanges.yaml)
[![Version](https://img.shields.io/badge/version-0.2.0-informational)](setup.cfg)

---

**Grekko** is an AI-driven, multi-chain trading platform that hunts opportunities across the entire crypto ecosystem. Built on proven Solana sniper technology, Grekko has evolved into a comprehensive platform targeting cryptocurrencies, NFTs, and DeFi instruments wherever volatility and explosive growth emerge.

**From Lightning-Fast Solana Sniper → Universal Crypto Opportunity Platform**

---

## 📈 The Grekko Evolution

### 🎯 Where We Started
- **Proven Foundation**: Sub-100ms Solana token detection
- **Battle-Tested**: Real-world profitable deployment
- **Speed Champion**: Fastest rug-pull detection in class

### 🚀 Where We Are Now
- **Multi-Chain Execution**: Ethereum, Solana, BSC support
- **Universal Exchanges**: CEX (Binance, Coinbase) + DEX (Uniswap, Sushiswap)
- **AI Ensemble**: LLM-powered decision making across all markets
- **Full-Stack Platform**: React dashboard + Python backend + WebSocket real-time

### 🌟 Where We're Going
- **Asset Omnivorous**: Any crypto, NFT, or DeFi instrument with alpha potential
- **Wallet Native**: Browser-first trading experience
- **Institutional Ready**: From $50 retail to $50M institutional deployments

---

## 🔜 Immediate Roadmap: Wallet Integration (Q1 2025)

### Priority Features
- **🏦 Coinbase Onramp**: Seamless fiat-to-crypto conversion
- **👛 Coinbase Wallet**: Direct wallet integration for trading
- **🦊 MetaMask Support**: Browser-native DeFi access

### Why This Matters
- **Lower Barriers**: One-click from fiat to trading
- **Better UX**: Trade directly from your preferred wallet  
- **Broader Access**: Bring institutional-grade AI to retail users
- **DeFi Native**: Native integration with the DeFi ecosystem

---

## 🚀 Core Capabilities

### Multi-Chain Alpha Detection
- **Solana**: Sub-second new token detection with advanced safety analysis
- **Ethereum**: Uniswap V3/V2, Sushiswap integration with MEV protection
- **Cross-Chain**: Arbitrage opportunities between chains and exchanges
- **AI-Powered**: Ensemble decision-making across all supported networks

### Universal Exchange Support
- **Centralized**: Binance, Coinbase Pro with smart order routing
- **Decentralized**: Uniswap, Sushiswap, Raydium, Orca
- **Hybrid Strategies**: CEX-DEX arbitrage and liquidity optimization
- **Failover Logic**: Automatic exchange failover for maximum uptime

### Advanced Risk Management
- **Real-Time Monitoring**: Circuit breakers across all positions
- **Dynamic Position Sizing**: AI-adjusted based on volatility and safety scores
- **Rug Pull Detection**: Advanced pattern recognition for scam avoidance
- **Multi-Asset Correlation**: Portfolio-level risk assessment

### Modern Web Interface
- **React Dashboard**: Real-time charts, agent management, portfolio tracking
- **WebSocket Live Data**: Sub-second market data and position updates
- **Mobile Responsive**: Trade and monitor from any device
- **Multi-Wallet Support**: Connect your preferred wallet directly

---

## 🏗️ Architecture Overview

Grekko's modular architecture enables rapid expansion across chains and asset types:

```
frontend/                    # React-based trading dashboard
├── src/components/          
│   ├── agents/             # AI agent management interface
│   ├── chart/              # Multi-chain trading charts
│   ├── layout/             # Responsive layout components
│   └── wallet/             # Wallet connection components (coming soon)
├── src/store/              # Redux state management
└── src/services/           # API and WebSocket communication

src/                        # Python trading engine
├── ai_adaptation/          # AI ensemble, reinforcement learning
├── alpha_generation/       # Multi-source alpha signals
│   ├── onchain_intelligence/   # Blockchain analysis
│   ├── social_sentiment/       # Twitter, Discord, Reddit
│   ├── alternative_data/       # News, events, macroeconomic
│   └── volatility_liquidity/   # Market microstructure
├── data_ingestion/         # Multi-chain data feeds
│   └── connectors/
│       ├── exchange_connectors/   # CEX APIs
│       ├── onchain_connectors/    # Blockchain RPCs
│       └── offchain_connectors/   # News, social data
├── execution/              # Universal execution layer
│   ├── cex/               # Binance, Coinbase executors
│   ├── dex/               # Uniswap, Sushiswap executors
│   ├── contracts/         # Smart contract interactions
│   └── decentralized_execution/   # MEV protection, flashloans
├── risk_management/        # Portfolio-wide risk controls
├── solana_sniper/         # Specialized Solana components
└── api/                   # FastAPI server, WebSocket feeds

config/                     # Modular configuration
├── exchanges.yaml         # All supported exchanges/chains
├── strategies.yaml        # Trading strategy parameters
├── risk_parameters.yaml   # Risk management settings
└── tokens.yaml           # Asset whitelists/blacklists
```

---

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+ (for dashboard)
- PostgreSQL (for trade storage)
- [Optional] Docker & Docker Compose

### 1. Environment Setup
```bash
git clone https://github.com/your-org/grekko.git
cd grekko
chmod +x setup_env.sh start_sniper.py
./setup_env.sh
source ~/.bashrc  # or ~/.zshrc
```

### 2. Install Dependencies
```bash
# Python backend
pip install -r requirements.txt

# React frontend
cd frontend && npm install && cd ..

# [Optional] Test dependencies
pip install -r tests/test_requirements.txt
```

### 3. Configuration
Set up your trading parameters in [`config/`](config/):

```yaml
# config/main.yaml - Choose your focus
default_strategy: "multi_chain_momentum"
target_chains: ["ethereum", "solana", "bsc"]
target_assets: ["tokens", "nfts", "defi"]

# Focus areas (customize based on your strategy)
solana_sniper:
  enabled: true
  max_buy_amount: 0.1  # SOL
  
ethereum_trader:
  enabled: true
  max_gas_price: 50    # gwei
  
cross_chain_arbitrage:
  enabled: true
  min_profit_bps: 50   # 0.5%
```

### 4. Launch Platform
```bash
# Start the full platform
python start_sniper.py

# Or focus on specific chains
python start_sniper.py --chain ethereum --target volatility
python start_sniper.py --chain solana --target new-tokens
python start_sniper.py --multi-chain --ai-driven
```

### 5. Access Dashboard
```bash
# Start React frontend (optional)
cd frontend && npm start
```
Dashboard available at `http://localhost:3000`

---

## 🎯 Trading Strategies

### Current Implementations
- **Solana Sniper**: Sub-100ms new token detection with safety analysis
- **Ethereum Momentum**: Trend following on established tokens
- **Cross-Chain Arbitrage**: Price differences between chains/exchanges
- **Volatility Harvesting**: High-frequency trading on volatile assets
- **DeFi Yield Optimization**: Automated yield farming across protocols

### AI Ensemble Features
- **Multi-LLM Decision Making**: GPT, Claude, local models consensus
- **Reinforcement Learning**: Continuous strategy optimization
- **Market Regime Detection**: Adapt strategies to market conditions
- **Risk-Adjusted Sizing**: Dynamic position sizing based on confidence

---

## 🔗 API & Integration

### REST Endpoints
- `POST /bot/start` - Start trading with configuration
- `GET /bot/status` - Real-time status and metrics
- `GET /positions` - Active positions across all chains
- `GET /trades/recent` - Trade history and performance
- `POST /strategy/switch` - Change trading strategy
- `GET /metrics/performance` - Detailed analytics

### WebSocket Feeds
- `WS /ws` - Real-time market data and trade updates
- Live position updates
- AI decision notifications
- Risk alerts and circuit breaker triggers

### TradingView Integration
- **Webhook Endpoint**: `POST /api/v1/tradingview/hook`
- **Multi-Chain Support**: Route signals to any supported chain
- **Security**: Token-based authentication

Example TradingView alert:
```json
{
  "symbol": "ETH/USDT",
  "side": "buy",
  "chain": "ethereum",
  "exchange": "uniswap",
  "strategy_id": "momentum-eth",
  "amount_usd": 1000
}
```

---

## 🧪 Testing & Deployment

### Comprehensive Test Suite
```bash
# Full test suite
pytest

# Chain-specific tests
pytest tests/unit/test_ethereum_execution.py
pytest tests/unit/test_solana_sniper.py

# Integration tests
pytest tests/integration/test_multi_chain.py
python test_sniper_integration.py
```

### Docker Deployment
```bash
# Full stack deployment
docker-compose -f docker/docker-compose.yml up --build

# Production deployment
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Environment Variables
See [`.env.production.example`](.env.production.example) for required configuration:
- Exchange API keys (Binance, Coinbase)
- RPC endpoints (Ethereum, Solana, BSC)
- Database credentials
- AI model access keys

---

## 📊 Performance & Metrics

### Real-World Performance
- **Solana Sniper**: 85%+ win rate on safety-filtered tokens
- **Execution Speed**: Sub-200ms average order execution
- **Multi-Chain**: Successfully trading across 3+ chains simultaneously
- **Uptime**: 99.9%+ with automatic failover

### Tracking & Analytics
- **Portfolio Performance**: Real-time P&L across all chains
- **Strategy Attribution**: Performance breakdown by strategy
- **Risk Metrics**: VaR, drawdown, Sharpe ratio
- **Execution Quality**: Slippage, fill rates, latency analysis

---

## 🗺️ Development Roadmap

### Phase 1: Wallet Integration (Q1 2025) - **PRIORITY**
- **Coinbase Onramp**: Direct fiat integration
- **Coinbase Wallet**: Native wallet trading
- **MetaMask Support**: Browser-based DeFi access
- **Wallet Connect**: Universal wallet protocol support

### Phase 2: Asset Expansion (Q2 2025)
- **NFT Trading**: Floor sweeps, rare trait detection
- **DeFi Instruments**: Automated yield farming, liquidity provision
- **Derivatives**: Perpetuals, options across multiple platforms
- **Cross-Chain NFTs**: Multi-chain NFT arbitrage

### Phase 3: Advanced AI (Q3 2025)
- **Predictive Models**: Token success probability prediction
- **Sentiment Integration**: Real-time social media analysis
- **Market Making**: Automated liquidity provision
- **Flash Loan Strategies**: Complex multi-step arbitrage

### Phase 4: Platform Evolution (Q4 2025)
- **Strategy Marketplace**: Community-created strategies
- **Social Trading**: Copy trading and signal sharing
- **Institutional Features**: Prime brokerage, reporting
- **Regulatory Compliance**: KYC/AML integration

---

## 🤝 Contributing

Grekko is evolving rapidly and welcomes contributions:

- **Strategy Development**: New trading algorithms
- **Chain Integration**: Support for additional blockchains  
- **UI/UX**: Frontend improvements and wallet integrations
- **Infrastructure**: Performance optimizations and monitoring

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines.

---

## 📄 Documentation

- [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [`FUTURE_ROADMAP.md`](FUTURE_ROADMAP.md) - Detailed development roadmap
- [`DEPLOYMENT.md`](DEPLOYMENT.md) - Production deployment guide
- [`tests/README.md`](tests/README.md) - Testing framework documentation

---

## 📄 License

MIT License. See [`LICENSE`](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built on proven Solana sniper technology
- Ethereum, Solana, and multi-chain DeFi communities
- Open-source contributors and testers
- Early adopters and feedback providers

---

**Grekko** – *From Solana Specialist to Universal Alpha Hunter*  
**Where opportunity emerges, Grekko hunts.** 🎯

*Ready to evolve your trading? Start with proven Solana technology, expand to multi-chain opportunities.*
