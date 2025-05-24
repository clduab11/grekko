# Grekko

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Build Status](https://github.com/your-org/grekko/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-informational)](setup.cfg)

---

**Grekko** is a next-generation, AI-driven cryptocurrency trading platform featuring ensemble decision-making, multi-exchange and on-chain intelligence, Solana sniping, robust risk management, and a modular, extensible architecture. Designed for both researchers and advanced traders, Grekko enables rapid strategy development, real-time execution, and deep analytics across centralized and decentralized markets.

---

## 🚀 Key Features

- **AI Ensemble Trading:** Adaptive agent orchestration, LLM/ML-based alpha generation, and reinforcement learning.
- **Multi-Exchange & On-Chain Intelligence:** Integrates CEX, DEX, and on-chain data for holistic market analysis.
- **Solana Sniper Bot:** Sub-second detection and execution on new Solana tokens, with advanced safety/rug detection.
- **Risk Management:** Circuit breakers, exposure controls, stop-loss, and anonymity modules.
- **TradingView Webhook Support:** Secure, real-time trade execution via TradingView alerts.
- **Modular API:** FastAPI-based, with REST and WebSocket endpoints for control, monitoring, and integration.
- **Extensive Testing:** Unit, integration, and simulation test suites for reliability and research.
- **Dockerized Deployment:** Production-ready Dockerfile and Compose for easy setup.
- **Configurable & Extensible:** YAML-based config, plugin-ready, and open for community contributions.

---

## 🏗️ Architecture Overview

Grekko is organized into modular components:

```
src/
├── ai_adaptation/         # Adaptive agents, LLM ensemble, RL, model training
├── alpha_generation/      # Alpha signals: on-chain, social, alt-data, volatility
├── api/                   # FastAPI app, TradingView webhook, REST/WebSocket
├── data_ingestion/        # Exchange, on-chain, and off-chain data connectors
├── execution/             # CEX/DEX execution, decentralized protocols, smart contracts
├── execution_protocol/    # Position management, trade recording, exit handling
├── feedback_loop/         # Model updating, performance analytics, strategy optimization
├── market_analysis/       # Regime detection, trending assets, regulatory/news
├── monitoring/            # Metrics collection and logging
├── paper_trading/         # Simulated trading environment
├── risk_management/       # Circuit breakers, exposure, stop-loss, anonymity
├── safety/                # Emergency controls
├── solana_sniper/         # Token monitor, safety analyzer, auto-buyer
├── strategy/              # Strategy manager, position sizing, trade evaluation
├── utils/                 # Config, credentials, encryption, logging, web3
└── main.py                # Entry point, orchestrates all components
```

See [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) and [`FUTURE_ROADMAP.md`](FUTURE_ROADMAP.md) for details.

---

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (for trade/performance storage)
- [Optional] Docker & Docker Compose

### 1. Clone & Environment Setup

```bash
git clone https://github.com/your-org/grekko.git
cd grekko
chmod +x setup_env.sh start_sniper.py
./setup_env.sh
source ~/.bashrc  # or ~/.zshrc
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. [Optional] Install Test Dependencies

```bash
pip install -r tests/test_requirements.txt
```

### 4. [Optional] Docker Deployment

Build and run the full stack (API, bot, DB):

```bash
docker-compose -f docker/docker-compose.yml up --build
```

Or build the main app image:

```bash
docker build -t grekko:latest -f docker/Dockerfile .
docker run --env-file .env -p 8000:8000 grekko:latest
```

---

## ⚙️ Configuration

All configuration is managed via YAML files in [`config/`](config/):

- `main.yaml` – Core settings (API, logging, DB, etc.)
- `agent_config.yaml` – AI agent and ensemble parameters
- `exchanges.yaml` – Exchange API keys and endpoints
- `risk_parameters.yaml` – Risk management thresholds
- `strategies.yaml` – Strategy selection and tuning
- `tokens.yaml` – Token allow/block lists

**Example: `config/main.yaml`**
```yaml
api:
  host: 0.0.0.0
  port: 8000
database:
  url: postgresql://grekko:grekkopassword@localhost:5432/grekko
logging:
  level: INFO
```

**Environment Variables:**  
See `.env.production.example` for required secrets (API keys, DB credentials, TradingView webhook secret, etc).

---

## 🏃 Usage

### 1. Start the Platform

```bash
python start_sniper.py
```

### 2. API Endpoints

- `POST /bot/start` – Start Solana sniper with config
- `POST /bot/stop` – Stop the bot
- `GET /bot/status` – Get status/metrics
- `GET /bot/positions` – Active positions
- `GET /trades/recent` – Trade history
- `GET /metrics/performance` – Performance analytics
- `WS /ws` – Real-time updates

See [`src/api/main.py`](src/api/main.py:1) for implementation.

### 3. TradingView Webhook

Grekko supports secure, real-time trade execution via TradingView alerts.

- **Endpoint:** `POST /api/v1/tradingview/hook`
- **Security:** Requires secret token (`TRADINGVIEW_WEBHOOK_SECRET`)

**Example Alert JSON:**
```json
{
  "symbol": "BTCUSDT",
  "price": 67000.5,
  "side": "buy",
  "strategy_id": "my-strategy-1",
  "size": 0.01,
  "secret": "YOUR_WEBHOOK_SECRET",
  "leverage": 2,
  "exchange": "binance"
}
```

See [`src/api/tradingview_webhook.py`](src/api/tradingview_webhook.py:1) for details.

---

## 🧪 Testing

Grekko includes comprehensive tests:

- **Unit tests:** [`tests/unit/`](tests/unit/)
- **Integration tests:** [`tests/integration/`](tests/integration/)
- **Simulation/backtesting:** [`tests/simulation/`](tests/simulation/)
- **Temp/experimental:** [`tests/temp_test/`](tests/temp_test/)

**Run all tests:**
```bash
pytest
```

**Run integration test:**
```bash
python test_sniper_integration.py
```

---

## 🐳 Docker & Production

- See [`docker/Dockerfile`](docker/Dockerfile:1) and [`docker/docker-compose.yml`](docker/docker-compose.yml:1)
- Production-ready: sets up system deps, Python, requirements, app code, and runs `src/main.py`
- Mount credentials and config as needed

---

## 🔄 CI/CD

- Automated testing and linting via [`.github/workflows/ci.yml`](.github/workflows/ci.yml:1)
- Pre-commit hooks: [`pre-commit-config.yaml`](pre-commit-config.yaml:1)
- Black, isort, mypy, pytest, safety checks

---

## 🗺️ Roadmap

See [`FUTURE_ROADMAP.md`](FUTURE_ROADMAP.md:1) for full details.

- Multi-DEX and cross-chain expansion
- ML-powered safety scoring
- Advanced analytics and backtesting
- Strategy marketplace and social trading
- DeFi yield optimization and flash loan strategies
- Performance, infrastructure, and AI/ML enhancements

---

## 🤝 Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) (if available) or open an issue/PR.

---

## 📄 License

MIT License. See [`LICENSE`](LICENSE) for details.

---

## 🙏 Acknowledgments

- Solana, Ethereum, and open-source DeFi communities
- Contributors and testers
- [Your organization/team]

---

**Grekko** – Democratizing advanced crypto trading with AI, speed, and transparency.
