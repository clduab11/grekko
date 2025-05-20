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
        self.logger = logging.getLogger(__name__)
        
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