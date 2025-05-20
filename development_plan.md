# Grekko Development Plan

## Executive Summary

Grekko is an advanced AI-powered cryptocurrency trading platform designed as a semi-autonomous LLM-backed trading agent. Its primary purpose is to autonomously execute profitable trades across CEX and DEX platforms based on technical analysis from TradingView and its own decision-making capabilities. Rather than simply providing trading signals or requiring manual execution, Grekko acts as an independent agent that can make trading decisions and execute them with minimal human intervention.

This development plan outlines a comprehensive strategy to transform Grekko from its current skeleton codebase into a fully autonomous trading system with appropriate guardrails and configuration options. The revitalized platform will integrate advanced LLM technologies with technical analysis to make independent trading decisions while allowing users to configure risk parameters, trading strategies, and operational boundaries.

## Current State Analysis

### Codebase Structure
The Grekko project follows a well-designed modular architecture with the following core components:
- Data Ingestion: Connectors for exchanges, blockchain data, and social media
- Market Analysis: Tools for market regime classification and trend detection
- Alpha Generation: Social sentiment analysis and on-chain intelligence
- Strategy: Implementation of various trading strategies
- Execution: Order execution on both CEX and DEX platforms
- Risk Management: Position monitoring and risk controls
- AI Adaptation: ML models and reinforcement learning for adaptive strategies

### Critical Issues
1. **Security Vulnerabilities**:
   - Hardcoded API credentials in `main.py` (line 34)
   - Encryption system exists but isn't properly utilized
   - No secure method for storing/retrieving credentials

2. **Dependency Management**:
   - Empty `requirements.txt` despite numerous dependencies
   - No virtual environment configuration
   - No dependency version pinning

3. **Implementation Status**:
   - Many files are empty placeholders
   - Core functionality incomplete
   - No tests implemented

4. **Autonomous Agent Capabilities**:
   - Missing LLM integration for autonomous decision-making
   - No configuration system for agent behavior and risk parameters
   - Lack of monitoring and oversight tools for autonomous operation

5. **Mobile Integration**:
   - No mobile companion app exists
   - No API endpoints for mobile communication

## External Dependencies

Based on the existing imports, Grekko requires the following external dependencies:

```
# Core Dependencies
python==3.11
pyyaml==6.0
pandas==2.0.0
numpy==1.24.0
aiohttp==3.8.4
asyncio==3.4.3

# AI and Language Models
openai==1.0.0
langchain==0.0.267
transformers==4.30.2
tensorflow==2.12.0
scikit-learn==1.2.2
keras==2.12.0
gym==0.26.0  # For reinforcement learning

# Cryptography 
cryptography==41.0.0
pynacl==1.5.0

# Blockchain
web3==6.0.0
solders==0.14.0  # For Solana
eth-account==0.8.0

# Exchange APIs
ccxt==3.0.0
ccxt.pro==0.10.0  # For websocket support

# Data Analysis
pandas-ta==0.3.14b
statsmodels==0.14.0
ta==0.10.2  # Technical analysis library
tradingview-ta==3.3.0  # TradingView integration

# Database
sqlalchemy==2.0.0

# API and Web
fastapi==0.95.2
uvicorn==0.22.0
websockets==11.0.3

# Testing
pytest==7.3.1
pytest-asyncio==0.21.0

# Utilities
python-dotenv==1.0.0
tqdm==4.65.0
requests==2.30.0
```

## Security Enhancement Plan

### 1. Credential Management System

The existing encryption infrastructure (`EncryptionManager`, `ECDSAKeyManager`, and `HSMKeyManager`) provides a solid foundation for secure credential management. The enhancement plan involves:

1. **Creating a Configuration Vault**:
   - Implement a `.grekko` directory in the user's home folder
   - Store encrypted credentials in this directory
   - Use the existing encryption classes

2. **API & Key Management System**:
   - Develop a credentials manager class that interfaces with the vault
   - Add credential rotation capabilities
   - Implement secure memory handling for credentials

3. **Integration with Existing Code**:
   - Replace hardcoded credentials with secure retrieval
   - Add credentials validation

### 2. Code Snippets for Implementation

**1. Secure Credentials Manager:**

```python
# src/utils/credentials_manager.py
import os
import json
import getpass
from pathlib import Path
from .encryption import EncryptionManager, save_vault, load_vault

class CredentialsManager:
    """Manages secure storage and retrieval of API credentials"""
    
    def __init__(self, config_path=None):
        self.home_dir = str(Path.home())
        self.config_dir = os.path.join(self.home_dir, '.grekko')
        self.vault_path = os.path.join(self.config_dir, 'credentials.grekko')
        self.config_path = config_path or os.path.join(os.getcwd(), 'config', 'exchanges.yaml')
        self._ensure_config_dir()
        
    def _ensure_config_dir(self):
        """Ensure the .grekko directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
    def setup_credentials(self):
        """Interactive setup for new credentials"""
        credentials = {}
        
        print("Setting up API credentials...")
        # Get exchanges from config/exchanges.yaml
        exchanges = self._get_configured_exchanges()
        
        for exchange in exchanges:
            print(f"\nSetting up credentials for {exchange}:")
            api_key = input(f"{exchange} API Key: ")
            api_secret = getpass.getpass(f"{exchange} API Secret: ")
            
            credentials[exchange] = {
                'api_key': api_key,
                'api_secret': api_secret
            }
            
        # Get master password for the vault
        master_password = self._get_master_password(new=True)
        
        # Save credentials to encrypted vault
        save_vault(credentials, master_password, self.vault_path)
        print(f"Credentials saved to {self.vault_path}")
        
    def get_credentials(self, exchange):
        """Retrieve credentials for a specific exchange"""
        master_password = self._get_master_password()
        
        try:
            vault = load_vault(master_password, self.vault_path)
            if exchange in vault:
                return vault[exchange]
            else:
                raise ValueError(f"No credentials found for {exchange}")
        except Exception as e:
            raise ValueError(f"Error loading credentials: {str(e)}")
            
    def _get_master_password(self, new=False):
        """Get master password, with confirmation if new"""
        if new:
            while True:
                password = getpass.getpass("Create master password for credential vault: ")
                confirm = getpass.getpass("Confirm master password: ")
                
                if password == confirm:
                    return password
                else:
                    print("Passwords do not match. Please try again.")
        else:
            return getpass.getpass("Enter master password for credential vault: ")
            
    def _get_configured_exchanges(self):
        """Parse exchanges.yaml to get list of configured exchanges"""
        import yaml
        
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                return list(config.keys()) if config else []
        except Exception:
            return ["binance", "coinbase", "uniswap"]  # Fallback defaults
```

**2. Updated Strategy Manager:**

```python
# src/strategy/strategy_manager.py - Secure Version
import logging
from .strategies.arbitrage_strategy import ArbitrageStrategy
from .strategies.mean_reversion_strategy import MeanReversionStrategy
from .strategies.momentum_strategy import MomentumStrategy
from .strategies.sentiment_strategy import SentimentStrategy
from ai_adaptation.ml_models.model_trainer import ModelTrainer
from utils.credentials_manager import CredentialsManager

class StrategyManager:
    def __init__(self, exchange='binance'):
        self.logger = logging.getLogger(__name__)
        self.exchange = exchange
        
        # Retrieve credentials securely
        try:
            credentials = CredentialsManager().get_credentials(exchange)
            self.api_key = credentials['api_key']
            self.api_secret = credentials['api_secret']
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {str(e)}")
            raise
            
        # Initialize strategies with secure credentials
        self.strategies = {
            'arbitrage': ArbitrageStrategy(self.api_key, self.api_secret),
            'mean_reversion': MeanReversionStrategy(lookback_period=20, entry_threshold=0.05, exit_threshold=0.02),
            'momentum': MomentumStrategy(lookback_period=20, entry_threshold=0.05, exit_threshold=0.02),
            'sentiment': SentimentStrategy(sentiment_threshold=0.1)
        }
        self.current_strategy = None
        self.model_trainer = ModelTrainer()

    # Rest of the class remains the same
    # ...
```

## Autonomous LLM-Powered Trading Agent

### 1. Autonomous Agent Architecture

```python
# src/ai_adaptation/agent/trading_agent.py
import logging
import json
import yaml
import os
import openai
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import setup_logger
from strategy.strategy_manager import StrategyManager
from risk_management.risk_manager import RiskManager
from execution.execution_manager import ExecutionManager
from data_ingestion.data_processor import DataProcessor

class TradingAgent:
    """
    Autonomous LLM-backed trading agent that makes independent trading decisions
    based on market data, technical analysis, and configured parameters.
    """
    
    def __init__(self, config_path="config/agent_config.yaml"):
        load_dotenv()
        self.logger = setup_logger("trading_agent", log_level="INFO")
        
        # Load agent configuration
        self.config = self._load_config(config_path)
        
        # Initialize OpenAI API
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing OpenAI API key in environment variables")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = self.config["llm"]["model_name"]
        
        # Initialize components
        self.strategy_manager = StrategyManager(exchange=self.config["default_exchange"])
        self.risk_manager = RiskManager(capital=self.config["risk"]["initial_capital"])
        self.execution_manager = ExecutionManager()
        self.data_processor = DataProcessor()
        
        # Agent state
        self.is_active = False
        self.trading_history = []
        self.current_positions = {}
        self.pending_decisions = []
        
        self.logger.info(f"Trading agent initialized with model: {self.model}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load agent configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            # Validate required settings
            required_sections = ["llm", "risk", "default_exchange", "trading_pairs"]
            for section in required_sections:
                if section not in config:
                    raise ValueError(f"Missing required section '{section}' in agent config")
                    
            return config
        except Exception as e:
            self.logger.error(f"Failed to load agent config: {str(e)}")
            raise
            
    async def start(self):
        """Start the autonomous trading agent"""
        if self.is_active:
            self.logger.warning("Trading agent is already active")
            return
            
        self.is_active = True
        self.logger.info("Trading agent started")
        
        # Begin monitoring and trading loop
        await self._trading_loop()
        
    async def stop(self):
        """Stop the autonomous trading agent"""
        if not self.is_active:
            self.logger.warning("Trading agent is already stopped")
            return
            
        self.is_active = False
        self.logger.info("Trading agent stopped")
        
        # Clean up if necessary
        self._report_status()
        
    async def _trading_loop(self):
        """Main trading loop for autonomous operation"""
        while self.is_active:
            try:
                # 1. Gather market data for configured trading pairs
                market_data = await self._gather_market_data()
                
                # 2. Process data through LLM for decision making
                decisions = await self._make_trading_decisions(market_data)
                
                # 3. Apply risk management rules
                filtered_decisions = self._apply_risk_rules(decisions)
                
                # 4. Execute approved decisions
                for decision in filtered_decisions:
                    await self._execute_decision(decision)
                    
                # 5. Update state and logs
                self._update_agent_state()
                
                # 6. Check for stop conditions
                if self._should_emergency_stop():
                    self.logger.warning("Emergency stop condition detected")
                    await self.stop()
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in trading loop: {str(e)}")
                # Only stop on critical errors, otherwise continue
                if self._is_critical_error(e):
                    await self.stop()
                    break
                    
    async def _gather_market_data(self) -> Dict[str, Any]:
        """Gather market data for configured trading pairs"""
        market_data = {}
        
        try:
            # Get data for each configured trading pair
            for pair in self.config["trading_pairs"]:
                # Get technical indicators from TradingView
                pair_data = await self._fetch_technical_analysis(pair)
                
                # Add additional data sources (sentiment, on-chain, etc.)
                pair_data.update(await self._fetch_additional_data(pair))
                
                market_data[pair] = pair_data
                
            return market_data
        except Exception as e:
            self.logger.error(f"Error gathering market data: {str(e)}")
            return {}
            
    async def _fetch_technical_analysis(self, trading_pair: str) -> Dict[str, Any]:
        """Fetch technical analysis data from TradingView"""
        # This would be implemented with actual TradingView API calls
        # For now, return placeholder data
        return {
            "indicators": {
                "rsi": 65.5,
                "macd": {"value": 0.002, "signal": 0.001, "histogram": 0.001},
                "ma_200": 42000.0,
                "ma_50": 43500.0,
                "bollinger_bands": {"upper": 44500.0, "middle": 43200.0, "lower": 41900.0}
            },
            "price": {
                "current": 43250.0,
                "high_24h": 43800.0,
                "low_24h": 42800.0,
                "volume_24h": 1250000000.0
            }
        }
        
    async def _fetch_additional_data(self, trading_pair: str) -> Dict[str, Any]:
        """Fetch additional data like sentiment and on-chain metrics"""
        # This would pull data from other sources
        return {
            "sentiment": {
                "social_score": 72.5,
                "news_sentiment": 0.65,
                "fear_greed_index": 58
            },
            "on_chain": {
                "exchange_inflow": -250.5,  # Negative means outflow (bullish)
                "active_addresses": 12500,
                "large_transactions": 450
            }
        }
        
    async def _make_trading_decisions(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to make trading decisions based on market data"""
        decisions = []
        
        for pair, data in market_data.items():
            try:
                # Format prompt with market data
                prompt = self._format_decision_prompt(pair, data)
                
                # Get LLM decision
                response = await self._query_llm(prompt)
                
                # Parse decision
                try:
                    decision = json.loads(response)
                    decision["trading_pair"] = pair
                    decision["timestamp"] = datetime.now().isoformat()
                    
                    self.logger.info(f"LLM decision for {pair}: {decision['action']} at confidence {decision['confidence']}")
                    decisions.append(decision)
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse LLM decision for {pair}: {response}")
            except Exception as e:
                self.logger.error(f"Error making decision for {pair}: {str(e)}")
                
        return decisions
        
    def _format_decision_prompt(self, trading_pair: str, market_data: Dict[str, Any]) -> str:
        """Format prompt for LLM trading decision"""
        prompt = f"""
You are Grekko, an advanced cryptocurrency trading AI. You make autonomous trading decisions based on technical analysis and market data.

Current Trading Pair: {trading_pair}

Technical Indicators:
- RSI: {market_data['indicators']['rsi']}
- MACD Value: {market_data['indicators']['macd']['value']}
- MACD Signal: {market_data['indicators']['macd']['signal']}
- MACD Histogram: {market_data['indicators']['macd']['histogram']}
- 200 MA: {market_data['indicators']['ma_200']}
- 50 MA: {market_data['indicators']['ma_50']}
- Bollinger Bands: Upper={market_data['indicators']['bollinger_bands']['upper']}, Middle={market_data['indicators']['bollinger_bands']['middle']}, Lower={market_data['indicators']['bollinger_bands']['lower']}

Price Information:
- Current Price: {market_data['price']['current']}
- 24h High: {market_data['price']['high_24h']}
- 24h Low: {market_data['price']['low_24h']}
- 24h Volume: {market_data['price']['volume_24h']}

Market Sentiment:
- Social Score: {market_data['sentiment']['social_score']}
- News Sentiment: {market_data['sentiment']['news_sentiment']}
- Fear & Greed Index: {market_data['sentiment']['fear_greed_index']}

On-Chain Metrics:
- Exchange Inflow: {market_data['on_chain']['exchange_inflow']}
- Active Addresses: {market_data['on_chain']['active_addresses']}
- Large Transactions: {market_data['on_chain']['large_transactions']}

Your risk profile: {self.config['risk']['profile']}
Current positions: {list(self.current_positions.keys())}

Based on this information, make a trading decision. Respond with JSON only in the following format:
{
  "action": "buy/sell/hold",
  "confidence": 0-1 (your confidence level),
  "size": 0-1 (position size as percentage of available capital),
  "target_price": [price target if buy/sell, null if hold],
  "stop_loss": [stop loss level if buy/sell, null if hold],
  "reasoning": "Brief explanation of your decision"
}
"""
        return prompt
        
    async def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the given prompt"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Grekko, an advanced cryptocurrency trading AI that provides reasoning in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config["llm"].get("temperature", 0.1),
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"LLM query error: {str(e)}")
            raise
            
    def _apply_risk_rules(self, decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply risk management rules to filter trading decisions"""
        filtered_decisions = []
        
        for decision in decisions:
            # Skip low confidence decisions
            if decision["confidence"] < self.config["risk"]["min_confidence"]:
                self.logger.info(f"Skipping low confidence decision for {decision['trading_pair']}: {decision['confidence']} < {self.config['risk']['min_confidence']}")
                continue
                
            # Check max position size
            if decision["size"] > self.config["risk"]["max_position_size"]:
                decision["size"] = self.config["risk"]["max_position_size"]
                self.logger.info(f"Capping position size for {decision['trading_pair']} to {decision['size']}")
                
            # Check max open positions
            if len(self.current_positions) >= self.config["risk"]["max_open_positions"] and decision["action"] == "buy":
                self.logger.info(f"Skipping buy for {decision['trading_pair']} due to max open positions limit")
                continue
                
            # Apply other risk rules
            # ...
            
            filtered_decisions.append(decision)
            
        return filtered_decisions
        
    async def _execute_decision(self, decision: Dict[str, Any]):
        """Execute a trading decision"""
        pair = decision["trading_pair"]
        action = decision["action"]
        
        if action == "hold":
            self.logger.info(f"Holding position for {pair}")
            return
            
        try:
            # Calculate position size
            available_capital = self.risk_manager.get_available_capital()
            position_amount = available_capital * decision["size"]
            
            if action == "buy":
                # Execute buy order
                order = await self.execution_manager.create_order(
                    symbol=pair,
                    order_type="market",
                    side="buy",
                    amount=position_amount
                )
                
                # Update positions
                if order and order["status"] == "executed":
                    self.current_positions[pair] = {
                        "entry_price": order["price"],
                        "amount": order["amount"],
                        "timestamp": datetime.now().isoformat(),
                        "stop_loss": decision["stop_loss"],
                        "target_price": decision["target_price"]
                    }
                    
                    self.logger.info(f"Bought {pair}: {order['amount']} at {order['price']}")
                    
            elif action == "sell":
                # Check if we have this position
                if pair in self.current_positions:
                    # Execute sell order
                    order = await self.execution_manager.create_order(
                        symbol=pair,
                        order_type="market",
                        side="sell",
                        amount=self.current_positions[pair]["amount"]
                    )
                    
                    # Update positions
                    if order and order["status"] == "executed":
                        position_data = self.current_positions.pop(pair)
                        profit_loss = (order["price"] - position_data["entry_price"]) * position_data["amount"]
                        
                        # Record trade in history
                        self.trading_history.append({
                            "pair": pair,
                            "entry_price": position_data["entry_price"],
                            "exit_price": order["price"],
                            "amount": position_data["amount"],
                            "profit_loss": profit_loss,
                            "entry_time": position_data["timestamp"],
                            "exit_time": datetime.now().isoformat()
                        })
                        
                        self.logger.info(f"Sold {pair}: {order['amount']} at {order['price']} (P/L: {profit_loss})")
                else:
                    self.logger.warning(f"Cannot sell {pair}: no position found")
                    
        except Exception as e:
            self.logger.error(f"Error executing decision for {pair}: {str(e)}")
            
    def _update_agent_state(self):
        """Update agent state and check positions"""
        try:
            # Update position values
            for pair, position in list(self.current_positions.items()):
                current_price = self._get_current_price(pair)
                
                # Update unrealized P/L
                entry_price = position["entry_price"]
                amount = position["amount"]
                unrealized_pl = (current_price - entry_price) * amount
                self.current_positions[pair]["current_price"] = current_price
                self.current_positions[pair]["unrealized_pl"] = unrealized_pl
                
                # Check stop loss
                if position["stop_loss"] and current_price <= position["stop_loss"]:
                    self.logger.info(f"Stop loss triggered for {pair} at {current_price}")
                    # Create sell order
                    self.pending_decisions.append({
                        "trading_pair": pair,
                        "action": "sell",
                        "confidence": 1.0,  # High confidence for stop loss
                        "size": 1.0,
                        "target_price": None,
                        "stop_loss": None,
                        "reasoning": "Stop loss triggered"
                    })
                    
                # Check take profit
                if position["target_price"] and current_price >= position["target_price"]:
                    self.logger.info(f"Take profit triggered for {pair} at {current_price}")
                    # Create sell order
                    self.pending_decisions.append({
                        "trading_pair": pair,
                        "action": "sell",
                        "confidence": 1.0,  # High confidence for take profit
                        "size": 1.0,
                        "target_price": None,
                        "stop_loss": None,
                        "reasoning": "Take profit triggered"
                    })
        except Exception as e:
            self.logger.error(f"Error updating agent state: {str(e)}")
            
    def _get_current_price(self, trading_pair: str) -> float:
        """Get current price for a trading pair"""
        # This would be implemented with actual API calls
        # For now, return placeholder data
        return 43250.0  # Placeholder
        
    def _should_emergency_stop(self) -> bool:
        """Check if emergency stop conditions are met"""
        try:
            # Check for drawdown limit
            portfolio_value = self._get_portfolio_value()
            initial_capital = self.config["risk"]["initial_capital"]
            max_drawdown = self.config["risk"]["max_drawdown"]
            
            if (initial_capital - portfolio_value) / initial_capital > max_drawdown:
                self.logger.warning(f"Emergency stop: Max drawdown exceeded ({max_drawdown * 100}%)")
                return True
                
            # Check for network issues
            # ...
            
            # Check for exchange issues
            # ...
            
            return False
        except Exception as e:
            self.logger.error(f"Error in emergency stop check: {str(e)}")
            return True  # Stop on error in safety check
            
    def _get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        cash = self.risk_manager.get_available_capital()
        positions_value = sum(pos["amount"] * pos.get("current_price", pos["entry_price"]) 
                           for pos in self.current_positions.values())
        return cash + positions_value
        
    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if an error is critical enough to stop trading"""
        critical_patterns = [
            "authentication failed",
            "insufficient funds",
            "api key expired",
            "rate limit exceeded",
            "connection error",
            "permission denied"
        ]
        
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in critical_patterns)
        
    def _report_status(self):
        """Generate a status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "active": self.is_active,
            "portfolio_value": self._get_portfolio_value(),
            "initial_capital": self.config["risk"]["initial_capital"],
            "open_positions": self.current_positions,
            "completed_trades": len(self.trading_history),
            "profitable_trades": sum(1 for trade in self.trading_history if trade["profit_loss"] > 0),
            "total_profit_loss": sum(trade["profit_loss"] for trade in self.trading_history)
        }
        
        self.logger.info(f"Status Report: {json.dumps(report, indent=2)}")
        return report
```

### 2. Agent Configuration System

```yaml
# config/agent_config.yaml
# Autonomous Trading Agent Configuration

# General settings
name: "Grekko"
description: "LLM-powered autonomous trading agent"
version: "1.0.0"

# Default exchange to use
default_exchange: "binance"

# Trading pairs to monitor
trading_pairs:
  - "BTC/USDT"
  - "ETH/USDT"
  - "SOL/USDT"
  - "DOGE/USDT"  # Meme coin
  - "SHIB/USDT"  # Meme coin

# LLM configuration
llm:
  provider: "openai"
  model_name: "gpt-4"
  temperature: 0.1
  max_tokens: 1000
  prompt_template_path: "config/prompts/trading_decision.txt"
  
  # Agent personality
  personality:
    risk_appetite: "moderate"   # conservative, moderate, aggressive
    trading_style: "technical"  # technical, sentiment, hybrid
    time_horizon: "medium"      # short, medium, long

# Risk management parameters
risk:
  profile: "balanced"
  initial_capital: 10000.0
  max_position_size: 0.2      # Maximum % of capital per position
  max_open_positions: 5       # Maximum number of concurrent positions
  min_confidence: 0.7         # Minimum confidence level for trades
  max_drawdown: 0.15          # Maximum allowed drawdown (15%)
  stop_loss_enabled: true
  trailing_stop_enabled: true
  trailing_stop_distance: 0.05 # 5% trailing stop
  
  # Circuit breakers
  emergency_stop_conditions:
    - "drawdown > 15%"
    - "consecutive_losses > 5"
    - "api_errors > 3"

# Analysis parameters
analysis:
  timeframes:
    - "5m"
    - "1h"
    - "4h"
    - "1d"
  
  indicators:
    - name: "RSI"
      params: { period: 14 }
    - name: "MACD"
      params: { fast_period: 12, slow_period: 26, signal_period: 9 }
    - name: "Bollinger Bands"
      params: { period: 20, std_dev: 2 }
    - name: "Moving Average"
      params: { period: 50, type: "SMA" }
    - name: "Moving Average"
      params: { period: 200, type: "SMA" }

# Execution parameters
execution:
  order_type: "market"      # market, limit
  slippage_tolerance: 0.5   # Max allowed slippage percentage
  retry_attempts: 3         # Number of retry attempts on failure
  retry_delay: 5            # Seconds between retries

# Reporting and notifications
reporting:
  status_interval: 3600     # Status report interval in seconds
  performance_metrics:
    - "profit_loss"
    - "win_rate"
    - "sharpe_ratio"
    - "max_drawdown"
  notifications:
    trade_executed: true
    stop_loss_triggered: true
    take_profit_triggered: true
    error_occurred: true
    emergency_stop: true
```

### 3. Agent Integration with Main Application

```python
# src/main.py - Updated with autonomous agent
import logging
import yaml
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from utils.credentials_manager import CredentialsManager
from ai_adaptation.agent.trading_agent import TradingAgent
from api.mobile_api import start_api_server

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def initialize_logging(log_level):
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, 'grekko.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    return logger

def ensure_credentials():
    """Ensure credentials exist, guide through setup if needed"""
    cred_manager = CredentialsManager()
    home_dir = str(Path.home())
    vault_path = os.path.join(home_dir, '.grekko', 'credentials.grekko')
    
    if not os.path.exists(vault_path):
        print("No credentials vault found. Setting up credentials...")
        cred_manager.setup_credentials()
    
    return True

async def main():
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config('config/main.yaml')
    logger = initialize_logging(config['general']['log_level'])
    
    # Ensure credentials are set up
    ensure_credentials()
    
    # Start the mobile API server in background
    api_task = asyncio.create_task(start_api_server())
    
    # Initialize and start the autonomous trading agent
    trading_agent = TradingAgent(config_path="config/agent_config.yaml")
    
    try:
        # Start the agent
        await trading_agent.start()
        
        # Keep the main process running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        await trading_agent.stop()
        
    finally:
        # Cleanup
        api_task.cancel()
        logger.info("Grekko trading agent shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
```

## Mobile Companion App Architecture

### 1. React Native App Architecture

```
mobile/
├── src/
│   ├── api/              # API client for communicating with Grekko backend
│   ├── components/       # Reusable UI components
│   ├── navigation/       # Navigation structure
│   ├── screens/          # Main app screens
│   │   ├── Auth/         # Authentication screens
│   │   ├── Dashboard/    # Main dashboard
│   │   ├── Portfolio/    # Portfolio tracking
│   │   ├── AgentConfig/  # Configure trading agent parameters
│   │   ├── Trades/       # Active & historical trades
│   │   ├── Analytics/    # Performance analytics
│   │   └── Settings/     # App settings
│   ├── store/            # State management
│   ├── utils/            # Utility functions
│   └── App.js            # Main app component
├── assets/               # Images, fonts, etc.
├── .env                  # Environment variables
└── package.json          # Dependencies
```

### 2. Agent Control Interface

```javascript
// mobile/src/screens/AgentConfig/AgentControlScreen.js
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { Button, Text, Card, Switch, Slider, Divider } from 'react-native-elements';
import { useDispatch, useSelector } from 'react-redux';
import { getAgentConfig, updateAgentConfig, startAgent, stopAgent } from '../../store/actions/agentActions';
import { AgentStatusCard } from '../../components/AgentStatus';
import { RiskParametersForm } from '../../components/RiskParameters';
import { TradingPairsList } from '../../components/TradingPairs';

const AgentControlScreen = () => {
  const dispatch = useDispatch();
  const { config, status, isLoading, error } = useSelector(state => state.agent);
  const [localConfig, setLocalConfig] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    dispatch(getAgentConfig());
  }, [dispatch]);

  useEffect(() => {
    if (config) {
      setLocalConfig(config);
    }
  }, [config]);

  const handleConfigChange = (section, field, value) => {
    setLocalConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
    setHasChanges(true);
  };

  const handleSaveConfig = () => {
    dispatch(updateAgentConfig(localConfig))
      .then(() => {
        setHasChanges(false);
        Alert.alert('Success', 'Agent configuration updated successfully');
      })
      .catch(err => {
        Alert.alert('Error', 'Failed to update agent configuration');
      });
  };

  const handleStartAgent = () => {
    Alert.alert(
      'Start Trading Agent',
      'Are you sure you want to start the autonomous trading agent? This will begin executing trades based on your configuration.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Start Agent', 
          onPress: () => dispatch(startAgent())
            .then(() => Alert.alert('Success', 'Trading agent started successfully'))
            .catch(err => Alert.alert('Error', 'Failed to start trading agent'))
        }
      ]
    );
  };

  const handleStopAgent = () => {
    Alert.alert(
      'Stop Trading Agent',
      'Are you sure you want to stop the autonomous trading agent? This will halt all trading activity.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Stop Agent', 
          style: 'destructive',
          onPress: () => dispatch(stopAgent())
            .then(() => Alert.alert('Success', 'Trading agent stopped successfully'))
            .catch(err => Alert.alert('Error', 'Failed to stop trading agent'))
        }
      ]
    );
  };

  if (isLoading && !config) {
    return (
      <View style={styles.centered}>
        <Text>Loading agent configuration...</Text>
      </View>
    );
  }

  if (error && !config) {
    return (
      <View style={styles.centered}>
        <Text>Error loading agent configuration: {error}</Text>
        <Button 
          title="Retry" 
          onPress={() => dispatch(getAgentConfig())} 
          buttonStyle={styles.retryButton}
        />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <AgentStatusCard status={status} />
      
      <Card containerStyle={styles.card}>
        <Card.Title>Agent Controls</Card.Title>
        <Card.Divider />
        <View style={styles.buttonContainer}>
          <Button
            title="Start Agent"
            onPress={handleStartAgent}
            disabled={status?.active}
            buttonStyle={[styles.actionButton, styles.startButton]}
            icon={{ name: 'play', type: 'font-awesome' }}
          />
          <Button
            title="Stop Agent"
            onPress={handleStopAgent}
            disabled={!status?.active}
            buttonStyle={[styles.actionButton, styles.stopButton]}
            icon={{ name: 'stop', type: 'font-awesome' }}
          />
        </View>
      </Card>

      <Card containerStyle={styles.card}>
        <Card.Title>Agent Personality</Card.Title>
        <Card.Divider />
        
        <Text style={styles.label}>Risk Appetite</Text>
        <View style={styles.sliderContainer}>
          <Text>Conservative</Text>
          <Slider
            value={
              localConfig?.llm?.personality?.risk_appetite === 'conservative' ? 0 :
              localConfig?.llm?.personality?.risk_appetite === 'moderate' ? 1 : 2
            }
            onValueChange={value => {
              const riskValues = ['conservative', 'moderate', 'aggressive'];
              handleConfigChange('llm', 'personality', {
                ...localConfig?.llm?.personality,
                risk_appetite: riskValues[value]
              });
            }}
            minimumValue={0}
            maximumValue={2}
            step={1}
            style={styles.slider}
          />
          <Text>Aggressive</Text>
        </View>
        
        <Text style={styles.label}>Trading Style</Text>
        <View style={styles.buttonGroup}>
          <Button
            title="Technical"
            type={localConfig?.llm?.personality?.trading_style === 'technical' ? 'solid' : 'outline'}
            onPress={() => handleConfigChange('llm', 'personality', {
              ...localConfig?.llm?.personality,
              trading_style: 'technical'
            })}
            buttonStyle={styles.styleButton}
          />
          <Button
            title="Sentiment"
            type={localConfig?.llm?.personality?.trading_style === 'sentiment' ? 'solid' : 'outline'}
            onPress={() => handleConfigChange('llm', 'personality', {
              ...localConfig?.llm?.personality,
              trading_style: 'sentiment'
            })}
            buttonStyle={styles.styleButton}
          />
          <Button
            title="Hybrid"
            type={localConfig?.llm?.personality?.trading_style === 'hybrid' ? 'solid' : 'outline'}
            onPress={() => handleConfigChange('llm', 'personality', {
              ...localConfig?.llm?.personality,
              trading_style: 'hybrid'
            })}
            buttonStyle={styles.styleButton}
          />
        </View>
      </Card>
      
      {/* Risk Parameters Form */}
      <RiskParametersForm 
        risk={localConfig?.risk} 
        onChange={(field, value) => handleConfigChange('risk', field, value)} 
      />
      
      {/* Trading Pairs */}
      <TradingPairsList 
        pairs={localConfig?.trading_pairs} 
        onChange={pairs => setLocalConfig(prev => ({...prev, trading_pairs: pairs}))}
      />
      
      <View style={styles.saveButtonContainer}>
        <Button
          title="Save Configuration"
          onPress={handleSaveConfig}
          disabled={!hasChanges}
          buttonStyle={styles.saveButton}
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  // Styles...
});

export default AgentControlScreen;
```

## Refactoring Roadmap

### Phase 1: Foundation (Week 1-2)
1. **Development Environment Setup**
   - Set up Python 3.11 virtual environment
   - Populate requirements.txt with all dependencies
   - Configure Docker environment for development

2. **Security Implementation**
   - Implement the credentials management system
   - Replace hardcoded credentials
   - Set up secure configuration loading

3. **Core Infrastructure**
   - Implement logging system
   - Set up database structure
   - Create CI/CD pipeline with GitHub Actions

### Phase 2: Autonomous Agent Core (Week 3-5)
1. **LLM Integration**
   - Set up OpenAI API integration
   - Implement the TradingAgent class
   - Create prompt templates for trading decisions
   - Build agent configuration system

2. **TradingView Data Integration**
   - Implement TradingView API connector
   - Create technical indicator analyzers
   - Build data normalization pipeline

3. **Strategy Implementation**
   - Complete existing strategy classes
   - Add the LLM-powered strategy
   - Implement strategy evaluation metrics

### Phase 3: Risk Management & Testing (Week 6-7)
1. **Risk Management**
   - Implement position sizing algorithms
   - Add trailing stop functionality
   - Create circuit breaker system

2. **Testing Infrastructure**
   - Set up unit tests with pytest
   - Create integration tests for exchange connectivity
   - Build backtesting system for strategy validation

3. **Performance Metrics**
   - Add performance tracking
   - Implement profit/loss analysis
   - Create visualization tools

### Phase 4: Mobile App Development (Week 8-10)
1. **Backend API**
   - Set up FastAPI for mobile communication
   - Implement authentication system
   - Create endpoints for agent control and data retrieval

2. **React Native App**
   - Set up development environment
   - Create UI components
   - Implement state management
   - Build agent configuration interface

3. **Integration**
   - Connect app to backend API
   - Add real-time updates
   - Implement push notifications

### Phase 5: Deployment & Monitoring (Week 11-12)
1. **Deployment Infrastructure**
   - Set up staging and production environments
   - Create Docker compose for production
   - Configure monitoring tools

2. **Documentation**
   - Update readme and architecture docs
   - Add API documentation
   - Create user guides

3. **Security Auditing**
   - Conduct security review
   - Add additional encryption layers
   - Implement secure communication

## Development Environment Setup

### Docker-Based Development Environment

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  grekko-app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    volumes:
      - ..:/app
      - ~/.grekko:/root/.grekko
    ports:
      - "8000:8000"  # API port
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - CONFIG_ENV=development
    command: python src/main.py
    
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_USER=grekko
      - POSTGRES_PASSWORD=grekkopassword
      - POSTGRES_DB=grekko
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
      
  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
```

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directory for credentials
RUN mkdir -p /root/.grekko

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create directory for logs
RUN mkdir -p /app/logs

# Default command
CMD ["python", "src/main.py"]
```

### Local Development Setup Script

```bash
#!/bin/bash
# scripts/setup.sh

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p ~/.grekko

# Set up pre-commit hooks
pip install pre-commit
pre-commit install

# Set up environment variables
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Grekko Environment Configuration
PYTHONPATH=$(pwd)
LOG_LEVEL=INFO
CONFIG_ENV=development

# API Keys (do not fill in - use credentials manager)
OPENAI_API_KEY=
TRADINGVIEW_API_KEY=

# Database
DATABASE_URL=postgresql://grekko:grekkopassword@localhost:5432/grekko

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
fi

echo "Development environment setup complete."
echo "Run 'source venv/bin/activate' to activate the virtual environment."
```

## Conclusion

This development plan provides a comprehensive roadmap for transforming Grekko into a fully autonomous LLM-powered cryptocurrency trading agent. By addressing critical security concerns, implementing proper dependency management, and integrating advanced LLM capabilities, Grekko will become a cutting-edge trading platform that can autonomously make and execute trading decisions based on technical analysis from TradingView.

The key innovation of this implementation is the autonomous agent architecture that allows Grekko to function as a semi-independent trading entity with configurable risk parameters and personality traits. The agent can analyze market data, generate trading signals, and execute trades with minimal human intervention while still allowing for oversight through the mobile companion app.

The plan emphasizes security and reliability throughout, ensuring that API credentials are stored securely and that the system includes proper risk management controls with circuit breakers to prevent catastrophic losses. With a phased implementation approach, the development team can deliver incremental value while working toward the complete vision of an AI-powered trading system that can potentially generate significant profits for its users.