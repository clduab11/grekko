"""
Momentum trading strategy implementation for the Grekko platform.

This module implements a momentum-based trading strategy that identifies
trending assets and generates trading signals based on price momentum
and other technical indicators.
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from datetime import datetime, timedelta

from ...utils.logger import get_logger
from ...data_ingestion.connectors.exchange_connectors.binance_connector import BinanceConnector
from ...risk_management.circuit_breaker import CircuitBreaker
from ..position_sizer import PositionSizer, PositionSizingMethod
from ..trade_evaluator import TradeEvaluator, SignalStrength, SignalType

class TradingSignal(Enum):
    """Trading signals that can be generated by the momentum strategy."""
    BUY = "buy"
    SELL = "sell"
    EXIT = "exit"
    HOLD = "hold"

class MomentumStrategy:
    """
    Momentum-based trading strategy that identifies trends and generates signals.
    
    This strategy analyzes price momentum over a specified lookback period and
    generates trading signals when momentum crosses certain thresholds. It can
    use various momentum calculation methods and combines them with other
    technical indicators for confirmation.
    
    Attributes:
        lookback_period (int): Period for momentum calculation in candles
        entry_threshold (float): Momentum threshold for entry signals
        exit_threshold (float): Momentum threshold for exit signals
        use_macd (bool): Whether to use MACD for signal confirmation
        use_rsi (bool): Whether to use RSI for signal confirmation
        minimum_volume (float): Minimum volume required for valid signals
        position_sizer (PositionSizer): Position sizer for trade sizing
        trade_evaluator (TradeEvaluator): Trade evaluator for signal evaluation
        data (pd.DataFrame): Historical price data for analysis
        indicators (Dict[str, pd.Series]): Calculated technical indicators
        logger (logging.Logger): Logger for strategy events
    """
    
    def __init__(self, 
                 lookback_period: int = 20,
                 entry_threshold: float = 0.05,
                 exit_threshold: float = 0.02,
                 use_macd: bool = True,
                 use_rsi: bool = True,
                 minimum_volume: float = 0.0,
                 risk_per_trade: float = 0.01,
                 position_sizer: Optional[PositionSizer] = None,
                 trade_evaluator: Optional[TradeEvaluator] = None,
                 connector: Optional[BinanceConnector] = None,
                 circuit_breaker: Optional[CircuitBreaker] = None):
        """
        Initialize the momentum strategy.
        
        Args:
            lookback_period (int): Period for momentum calculation
            entry_threshold (float): Threshold for entry signals
            exit_threshold (float): Threshold for exit signals
            use_macd (bool): Whether to use MACD for confirmation
            use_rsi (bool): Whether to use RSI for confirmation
            minimum_volume (float): Minimum volume required for signals
            risk_per_trade (float): Risk per trade as percentage of capital
            position_sizer (Optional[PositionSizer]): Position sizer or None
            trade_evaluator (Optional[TradeEvaluator]): Trade evaluator or None
            connector (Optional[BinanceConnector]): Exchange connector or None
            circuit_breaker (Optional[CircuitBreaker]): Circuit breaker or None
        """
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.use_macd = use_macd
        self.use_rsi = use_rsi
        self.minimum_volume = minimum_volume
        self.risk_per_trade = risk_per_trade
        
        # Initialize main DataFrame for price data
        self.data = pd.DataFrame()
        
        # Dictionary to store calculated indicators
        self.indicators = {}
        
        # External components
        self.position_sizer = position_sizer
        self.trade_evaluator = trade_evaluator
        self.connector = connector
        self.circuit_breaker = circuit_breaker
        
        # Active trades tracking
        self.active_trades = {}
        self.trade_history = []
        
        # Configure logger
        self.logger = get_logger('momentum_strategy')
        self.logger.info(
            f"Momentum strategy initialized with lookback period: {lookback_period}, "
            f"entry threshold: {entry_threshold:.1%}, exit threshold: {exit_threshold:.1%}"
        )
        
        # Performance metrics
        self.performance_metrics = {
            "trades_count": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "avg_profit_pct": 0.0,
            "avg_loss_pct": 0.0,
            "profit_factor": 0.0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0
        }
    
    def add_data(self, price_data: Union[Dict[str, Any], pd.DataFrame]) -> None:
        """
        Add new price data to the strategy's dataset.
        
        Args:
            price_data (Union[Dict[str, Any], pd.DataFrame]): New price data
        """
        # Convert dict to DataFrame if needed
        if isinstance(price_data, dict):
            # Create a single row DataFrame from dict
            new_data = pd.DataFrame([price_data])
        else:
            new_data = price_data.copy()
        
        # Ensure required columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in new_data.columns:
                if col == 'timestamp' and 'time' in new_data.columns:
                    new_data['timestamp'] = new_data['time']
                elif col == 'close' and 'price' in new_data.columns:
                    new_data['close'] = new_data['price']
                else:
                    self.logger.warning(f"Missing required column {col} in price data")
                    if col in ['open', 'high', 'low', 'close']:
                        # For OHLC, use 'price' as fallback if available
                        if 'price' in new_data.columns:
                            new_data[col] = new_data['price']
                        else:
                            return  # Cannot proceed without price data
        
        # Append new data
        if self.data.empty:
            self.data = new_data
        else:
            self.data = pd.concat([self.data, new_data], ignore_index=True)
        
        # Keep only the required lookback period
        max_lookback = max(200, self.lookback_period * 2)  # Keep at least 2x lookback period or 200 rows
        if len(self.data) > max_lookback:
            self.data = self.data.iloc[-max_lookback:]
        
        # Update indicators after adding new data
        self._calculate_indicators()
        
    def _calculate_indicators(self) -> None:
        """Calculate technical indicators used by the strategy."""
        if len(self.data) < self.lookback_period:
            self.logger.debug(f"Not enough data to calculate indicators: {len(self.data)} < {self.lookback_period}")
            return
            
        # Calculate simple momentum (percentage change)
        self.indicators['momentum'] = self.data['close'].pct_change(self.lookback_period)
        
        # Calculate ROC (Rate of Change)
        self.indicators['roc'] = (self.data['close'] / self.data['close'].shift(self.lookback_period) - 1) * 100
        
        # Calculate SMA (Simple Moving Average)
        self.indicators['sma_fast'] = self.data['close'].rolling(window=self.lookback_period // 2).mean()
        self.indicators['sma_slow'] = self.data['close'].rolling(window=self.lookback_period).mean()
        
        # Calculate EMA (Exponential Moving Average)
        self.indicators['ema_fast'] = self.data['close'].ewm(span=self.lookback_period // 2, adjust=False).mean()
        self.indicators['ema_slow'] = self.data['close'].ewm(span=self.lookback_period, adjust=False).mean()
        
        # Calculate RSI if enabled
        if self.use_rsi:
            delta = self.data['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / avg_loss
            self.indicators['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD if enabled
        if self.use_macd:
            ema_12 = self.data['close'].ewm(span=12, adjust=False).mean()
            ema_26 = self.data['close'].ewm(span=26, adjust=False).mean()
            
            self.indicators['macd_line'] = ema_12 - ema_26
            self.indicators['macd_signal'] = self.indicators['macd_line'].ewm(span=9, adjust=False).mean()
            self.indicators['macd_histogram'] = self.indicators['macd_line'] - self.indicators['macd_signal']
            
        # Calculate Bollinger Bands
        self.indicators['middle_band'] = self.data['close'].rolling(window=20).mean()
        std_dev = self.data['close'].rolling(window=20).std()
        self.indicators['upper_band'] = self.indicators['middle_band'] + (std_dev * 2)
        self.indicators['lower_band'] = self.indicators['middle_band'] - (std_dev * 2)
        
        # Calculate ATR (Average True Range) for volatility
        high_low = self.data['high'] - self.data['low']
        high_close = (self.data['high'] - self.data['close'].shift()).abs()
        low_close = (self.data['low'] - self.data['close'].shift()).abs()
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        self.indicators['atr'] = true_range.rolling(window=14).mean()
        
        # Calculate volume indicators
        self.indicators['volume_sma'] = self.data['volume'].rolling(window=20).mean()
        self.indicators['volume_ratio'] = self.data['volume'] / self.indicators['volume_sma']
        
    def calculate_momentum(self) -> float:
        """
        Calculate the momentum value for the latest data point.
        
        Returns:
            float: Momentum value (percent change over lookback period)
        """
        if 'momentum' in self.indicators and not self.indicators['momentum'].empty:
            return self.indicators['momentum'].iloc[-1]
        else:
            # Calculate directly if indicator not available
            if len(self.data) >= self.lookback_period:
                current_price = self.data['close'].iloc[-1]
                past_price = self.data['close'].iloc[-self.lookback_period]
                return (current_price / past_price - 1) if past_price > 0 else 0
            return 0
    
    def identify_trade_signal(self, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Identify a trading signal based on momentum and other indicators.
        
        Args:
            market_data (Optional[Dict[str, Any]]): Additional market data
            
        Returns:
            Dict[str, Any]: Trading signal information
        """
        # Add market data to historical data if provided
        if market_data:
            self.add_data(market_data)
            
        # Check if we have enough data
        if len(self.data) < self.lookback_period:
            return {
                "symbol": market_data.get("symbol") if market_data else None,
                "action": TradingSignal.HOLD.value,
                "strength": 0.0,
                "reason": "Insufficient data for analysis"
            }
        
        # Get the latest indicator values
        momentum = self.indicators['momentum'].iloc[-1] if 'momentum' in self.indicators and not self.indicators['momentum'].empty else 0
        roc = self.indicators['roc'].iloc[-1] if 'roc' in self.indicators and not self.indicators['roc'].empty else 0
        
        # Check if we have RSI data
        has_rsi = self.use_rsi and 'rsi' in self.indicators and not self.indicators['rsi'].empty
        rsi = self.indicators['rsi'].iloc[-1] if has_rsi else 50
        
        # Check if we have MACD data
        has_macd = self.use_macd and 'macd_histogram' in self.indicators and not self.indicators['macd_histogram'].empty
        macd_hist = self.indicators['macd_histogram'].iloc[-1] if has_macd else 0
        
        # Check volume if minimum is set
        volume_check_passed = True
        if self.minimum_volume > 0 and 'volume' in self.data:
            latest_volume = self.data['volume'].iloc[-1]
            volume_check_passed = latest_volume >= self.minimum_volume
        
        # Volume ratio for confirmation
        volume_ratio = self.indicators['volume_ratio'].iloc[-1] if 'volume_ratio' in self.indicators and not self.indicators['volume_ratio'].empty else 1.0
        high_volume = volume_ratio > 1.2  # 20% above average
        
        # Define signal strength components
        momentum_strength = min(1.0, abs(momentum) / (self.entry_threshold * 2))
        
        # RSI component (extreme values decrease strength)
        rsi_strength = 1.0
        if has_rsi:
            if momentum > 0 and rsi > 70:  # Overbought in uptrend
                rsi_strength = max(0.2, 1.0 - (rsi - 70) / 30)
            elif momentum < 0 and rsi < 30:  # Oversold in downtrend
                rsi_strength = max(0.2, 1.0 - (30 - rsi) / 30)
            
        # MACD confirmation
        macd_strength = 1.0
        if has_macd:
            macd_confirmation = (momentum > 0 and macd_hist > 0) or (momentum < 0 and macd_hist < 0)
            macd_strength = 0.7 if not macd_confirmation else 1.0
            
        # Volume confirmation
        volume_strength = 0.7 if not high_volume else 1.0
        
        # Calculate final signal strength
        signal_strength = momentum_strength * rsi_strength * macd_strength * volume_strength
        
        # Determine the signal based on momentum and confirmation
        if momentum > self.entry_threshold:
            # Potential BUY signal
            action = TradingSignal.BUY.value
            reason = f"Momentum above threshold: {momentum:.2%} > {self.entry_threshold:.2%}"
        elif momentum < -self.entry_threshold:
            # Potential SELL signal
            action = TradingSignal.SELL.value
            reason = f"Momentum below threshold: {momentum:.2%} < -{self.entry_threshold:.2%}"
        elif abs(momentum) < self.exit_threshold:
            # Momentum losing strength, potential EXIT
            action = TradingSignal.EXIT.value
            reason = f"Momentum diminishing: |{momentum:.2%}| < {self.exit_threshold:.2%}"
        else:
            # No clear signal, HOLD
            action = TradingSignal.HOLD.value
            reason = "No clear momentum signal"
            
        # Calculate additional signal components
        sma_trend = None
        if 'sma_fast' in self.indicators and 'sma_slow' in self.indicators:
            sma_fast = self.indicators['sma_fast'].iloc[-1]
            sma_slow = self.indicators['sma_slow'].iloc[-1]
            sma_trend = "bullish" if sma_fast > sma_slow else "bearish" 
            
        # Price relative to Bollinger Bands
        bb_position = None
        if 'upper_band' in self.indicators and 'lower_band' in self.indicators:
            price = self.data['close'].iloc[-1]
            upper = self.indicators['upper_band'].iloc[-1]
            lower = self.indicators['lower_band'].iloc[-1]
            
            if price > upper:
                bb_position = "above_upper"
            elif price < lower:
                bb_position = "below_lower"
            else:
                bb_position = "inside"
        
        # Create target and stop loss prices
        current_price = self.data['close'].iloc[-1]
        atr = self.indicators['atr'].iloc[-1] if 'atr' in self.indicators and not self.indicators['atr'].empty else current_price * 0.01
        
        if action == TradingSignal.BUY.value:
            target_price = current_price * (1 + max(0.02, abs(momentum) * 2))
            stop_loss = current_price - (atr * 2)
        elif action == TradingSignal.SELL.value:
            target_price = current_price * (1 - max(0.02, abs(momentum) * 2))
            stop_loss = current_price + (atr * 2)
        else:
            target_price = None
            stop_loss = None
            
        # Assemble the final signal
        symbol = market_data.get("symbol") if market_data else self.data.get("symbol", "unknown")
        
        signal = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "type": SignalType.MOMENTUM.value,
            "action": action,
            "direction": "long" if action == TradingSignal.BUY.value else "short" if action == TradingSignal.SELL.value else "flat",
            "strength": signal_strength,
            "current_price": current_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_reward_ratio": abs((target_price - current_price) / (current_price - stop_loss)) if target_price and stop_loss and stop_loss != current_price else None,
            "momentum": momentum,
            "roc": roc,
            "volume_ratio": volume_ratio,
            "reason": reason,
            "confirmations": {
                "macd": macd_hist if has_macd else None,
                "rsi": rsi if has_rsi else None,
                "sma_trend": sma_trend,
                "bb_position": bb_position,
                "high_volume": high_volume
            }
        }
        
        # Log the signal
        signal_str = f"{action} signal for {symbol} with strength {signal_strength:.2f}"
        if action in [TradingSignal.BUY.value, TradingSignal.SELL.value]:
            self.logger.info(f"Generated {signal_str} (momentum: {momentum:.2%})")
        else:
            self.logger.debug(f"Generated {signal_str} (momentum: {momentum:.2%})")
            
        return signal
    
    async def execute_trade(self, 
                          signal: Dict[str, Any], 
                          amount: Optional[float] = None,
                          market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a trade based on the given signal.
        
        Args:
            signal (Dict[str, Any]): Trading signal to execute
            amount (Optional[float]): Optional override for position size
            market_data (Optional[Dict[str, Any]]): Additional market data
            
        Returns:
            Dict[str, Any]: Trade execution result
        """
        # Initialize result dictionary
        result = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "signal": signal,
            "order": None,
            "amount": amount,
            "message": ""
        }
        
        # Ensure we have a connector
        if not self.connector:
            result["message"] = "No exchange connector available"
            self.logger.error(result["message"])
            return result
            
        # Check circuit breaker if available
        if self.circuit_breaker:
            can_trade, reason = self.circuit_breaker.can_trade(signal.get("current_price", 1.0))
            if not can_trade:
                result["message"] = f"Circuit breaker active: {reason}"
                self.logger.warning(result["message"])
                return result
                
        # Check if signal is actionable
        action = signal.get("action")
        if action not in [TradingSignal.BUY.value, TradingSignal.SELL.value]:
            result["message"] = f"Signal is not actionable: {action}"
            self.logger.info(result["message"])
            return result
        
        # Evaluate the trade if evaluator is available
        if self.trade_evaluator and market_data:
            should_trade, confidence, evaluation = self.trade_evaluator.evaluate_trade(
                signal=signal,
                market_data=market_data,
                existing_positions=list(self.active_trades.values())
            )
            
            result["evaluation"] = evaluation
            
            if not should_trade:
                result["message"] = f"Trade evaluation failed with confidence {confidence:.2f}"
                self.logger.info(result["message"])
                return result
        
        # Calculate position size if not provided
        if amount is None and self.position_sizer:
            # Get current price from signal or market data
            current_price = signal.get("current_price") or market_data.get("last", 0)
            
            # Calculate position size
            position_size, metadata = self.position_sizer.calculate_position_size(
                method=PositionSizingMethod.RISK_BASED,
                ticker_data=market_data,
                risk_per_trade_pct=self.risk_per_trade,
                stop_loss_pct=abs((signal.get("stop_loss", 0) - current_price) / current_price) if signal.get("stop_loss") else 0.05
            )
            
            amount = position_size / current_price if current_price > 0 else 0
            result["position_sizing"] = metadata
        
        # Ensure we have a valid amount
        if not amount or amount <= 0:
            result["message"] = f"Invalid position size: {amount}"
            self.logger.error(result["message"])
            return result
            
        # Determine order parameters
        symbol = signal.get("symbol")
        side = "buy" if action == TradingSignal.BUY.value else "sell"
        order_type = "market"  # Use market orders for simplicity
        
        # Execute the order
        try:
            self.logger.info(f"Executing {side.upper()} order for {symbol}: {amount} units")
            
            order = await self.connector.create_order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                amount=amount
            )
            
            if order:
                # Record the trade
                trade_id = order.get("id", str(datetime.now().timestamp()))
                
                self.active_trades[trade_id] = {
                    "id": trade_id,
                    "symbol": symbol,
                    "entry_time": datetime.now().isoformat(),
                    "entry_price": order.get("price", signal.get("current_price", 0)),
                    "amount": amount,
                    "side": side,
                    "target_price": signal.get("target_price"),
                    "stop_loss": signal.get("stop_loss"),
                    "signal": signal
                }
                
                # Update result
                result["success"] = True
                result["order"] = order
                result["message"] = f"Successfully executed {side} order for {symbol}"
                result["trade_id"] = trade_id
                
                # Update performance metrics
                self.performance_metrics["trades_count"] += 1
                
                self.logger.info(result["message"])
            else:
                result["message"] = f"Order creation failed"
                self.logger.error(result["message"])
        
        except Exception as e:
            result["message"] = f"Error executing trade: {str(e)}"
            self.logger.error(result["message"])
            
        return result
    
    async def close_trade(self, trade_id: str, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Close an existing trade.
        
        Args:
            trade_id (str): ID of the trade to close
            market_data (Optional[Dict[str, Any]]): Current market data
            
        Returns:
            Dict[str, Any]: Trade closing result
        """
        # Initialize result dictionary
        result = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "trade_id": trade_id,
            "order": None,
            "message": ""
        }
        
        # Check if trade exists
        if trade_id not in self.active_trades:
            result["message"] = f"Trade {trade_id} not found"
            self.logger.error(result["message"])
            return result
            
        # Get trade details
        trade = self.active_trades[trade_id]
        symbol = trade["symbol"]
        entry_side = trade["side"]
        amount = trade["amount"]
        
        # Determine exit side (opposite of entry)
        exit_side = "sell" if entry_side == "buy" else "buy"
        
        # Execute the exit order
        try:
            self.logger.info(f"Closing trade {trade_id} for {symbol}: {exit_side.upper()} {amount} units")
            
            order = await self.connector.create_order(
                symbol=symbol,
                order_type="market",
                side=exit_side,
                amount=amount
            )
            
            if order:
                # Get exit price
                exit_price = order.get("price", market_data.get("last", 0) if market_data else 0)
                
                # Calculate P&L
                entry_price = trade["entry_price"]
                pnl_pct = (exit_price / entry_price - 1) * (1 if entry_side == "buy" else -1)
                
                # Create trade record for history
                trade_record = {
                    **trade,
                    "exit_time": datetime.now().isoformat(),
                    "exit_price": exit_price,
                    "exit_order": order,
                    "pnl_percentage": pnl_pct,
                    "pnl_amount": pnl_pct * entry_price * amount,
                    "duration": (datetime.now() - datetime.fromisoformat(trade["entry_time"])).total_seconds() / 60  # minutes
                }
                
                # Add to trade history
                self.trade_history.append(trade_record)
                
                # Remove from active trades
                del self.active_trades[trade_id]
                
                # Update performance metrics
                if pnl_pct > 0:
                    self.performance_metrics["winning_trades"] += 1
                    self.performance_metrics["avg_profit_pct"] = (self.performance_metrics["avg_profit_pct"] * (self.performance_metrics["winning_trades"] - 1) + pnl_pct) / self.performance_metrics["winning_trades"]
                else:
                    self.performance_metrics["losing_trades"] += 1
                    self.performance_metrics["avg_loss_pct"] = (self.performance_metrics["avg_loss_pct"] * (self.performance_metrics["losing_trades"] - 1) + abs(pnl_pct)) / self.performance_metrics["losing_trades"]
                
                self.performance_metrics["win_rate"] = self.performance_metrics["winning_trades"] / self.performance_metrics["trades_count"]
                self.performance_metrics["total_pnl"] += pnl_pct
                
                # Update result
                result["success"] = True
                result["order"] = order
                result["message"] = f"Successfully closed trade {trade_id} with P&L: {pnl_pct:.2%}"
                result["trade_record"] = trade_record
                
                # Log the result
                log_level = "info" if pnl_pct >= 0 else "warning"
                getattr(self.logger, log_level)(result["message"])
                
                # Update circuit breaker if available
                if self.circuit_breaker:
                    self.circuit_breaker.record_trade_result(pnl_pct > 0)
            
            else:
                result["message"] = f"Failed to create exit order for trade {trade_id}"
                self.logger.error(result["message"])
        
        except Exception as e:
            result["message"] = f"Error closing trade {trade_id}: {str(e)}"
            self.logger.error(result["message"])
            
        return result
    
    async def monitor_trades(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Monitor active trades and close them if needed based on targets or stops.
        
        Args:
            market_data (Dict[str, Any]): Current market data
            
        Returns:
            List[Dict[str, Any]]: List of monitoring actions taken
        """
        if not self.active_trades:
            return []
            
        symbol = market_data.get("symbol")
        current_price = market_data.get("last", 0)
        
        if not symbol or not current_price:
            return []
            
        actions = []
        
        # Check each active trade for this symbol
        for trade_id, trade in list(self.active_trades.items()):
            if trade["symbol"] != symbol:
                continue
                
            # Check stop loss
            stop_loss = trade.get("stop_loss")
            if stop_loss and ((trade["side"] == "buy" and current_price <= stop_loss) or 
                              (trade["side"] == "sell" and current_price >= stop_loss)):
                # Stop loss triggered
                self.logger.warning(f"Stop loss triggered for trade {trade_id} at {current_price}")
                
                # Close the trade
                close_result = await self.close_trade(trade_id, market_data)
                actions.append({
                    "action": "stop_loss",
                    "trade_id": trade_id,
                    "result": close_result
                })
                continue
                
            # Check take profit
            target_price = trade.get("target_price")
            if target_price and ((trade["side"] == "buy" and current_price >= target_price) or 
                                (trade["side"] == "sell" and current_price <= target_price)):
                # Take profit triggered
                self.logger.info(f"Take profit triggered for trade {trade_id} at {current_price}")
                
                # Close the trade
                close_result = await self.close_trade(trade_id, market_data)
                actions.append({
                    "action": "take_profit",
                    "trade_id": trade_id,
                    "result": close_result
                })
                
        return actions
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate strategy performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        # Update metrics that need calculation
        if self.performance_metrics["winning_trades"] > 0 and self.performance_metrics["losing_trades"] > 0:
            # Calculate profit factor (total gains / total losses)
            total_gains = self.performance_metrics["avg_profit_pct"] * self.performance_metrics["winning_trades"]
            total_losses = self.performance_metrics["avg_loss_pct"] * self.performance_metrics["losing_trades"]
            
            if total_losses > 0:
                self.performance_metrics["profit_factor"] = total_gains / total_losses
            
        # Calculate max drawdown from trade history
        if self.trade_history:
            equity_curve = [0]  # Start with 0
            
            for trade in sorted(self.trade_history, key=lambda x: x["exit_time"]):
                equity_curve.append(equity_curve[-1] + trade.get("pnl_amount", 0))
                
            # Calculate drawdown
            peak = equity_curve[0]
            max_drawdown = 0
            
            for value in equity_curve:
                if value > peak:
                    peak = value
                else:
                    drawdown = (peak - value) / peak if peak > 0 else 0
                    max_drawdown = max(max_drawdown, drawdown)
                    
            self.performance_metrics["max_drawdown"] = max_drawdown
        
        # Return a copy of the metrics
        return dict(self.performance_metrics)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the strategy.
        
        Returns:
            Dict[str, Any]: Strategy status information
        """
        return {
            "name": "Momentum Strategy",
            "config": {
                "lookback_period": self.lookback_period,
                "entry_threshold": self.entry_threshold,
                "exit_threshold": self.exit_threshold,
                "use_macd": self.use_macd,
                "use_rsi": self.use_rsi
            },
            "data_points": len(self.data),
            "active_trades": len(self.active_trades),
            "completed_trades": len(self.trade_history),
            "performance": self.calculate_performance_metrics()
        }