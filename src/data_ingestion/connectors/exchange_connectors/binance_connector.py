"""
Binance exchange connector for the Grekko trading system.

This module provides connectivity to the Binance exchange API,
including order execution, market data retrieval, and advanced trading strategies.
"""
import ccxt.pro as ccxt
import time
import logging
import asyncio
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from ....utils.logger import get_logger
from ....utils.credentials_manager import CredentialsManager
from ....risk_management.circuit_breaker import CircuitBreaker, TriggerReason

class BinanceConnector:
    """
    Connector for the Binance exchange.
    
    Provides methods for market data retrieval, order execution,
    and advanced trading strategies like triangular arbitrage and TWAP.
    This connector builds on the ccxt.pro library for optimal performance.
    
    Attributes:
        api_key (str): Binance API key (securely loaded)
        api_secret (str): Binance API secret (securely loaded)
        exchange (ccxt.binance): CCXT Binance exchange instance
        logger (logging.Logger): Logger for connector events
        circuit_breaker (CircuitBreaker): Safety circuit breaker for this connector
        historical_spreads (Dict[str, List[float]]): Historical spread data by symbol
        exchange_info (Dict): Cached exchange information
        order_history (List[Dict]): History of executed orders
        last_request_time (Dict[str, float]): Timestamps of last API requests by endpoint
        error_counts (Dict[str, int]): Count of errors by category
    """
    
    def __init__(self, testnet: bool = False, use_credentials: bool = True,
                circuit_breaker: Optional[CircuitBreaker] = None,
                api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the Binance connector with secure credentials.
        
        Args:
            testnet (bool): Whether to use the testnet (default: False)
            use_credentials (bool): Whether to load credentials from vault (default: True)
            circuit_breaker (Optional[CircuitBreaker]): Circuit breaker instance or None to create new
            api_key (Optional[str]): Binance API key (overrides credentials manager if provided)
            api_secret (Optional[str]): Binance API secret (overrides credentials manager if provided)
        """
        self.logger = get_logger('binance_connector')
        self.logger.info(f"Initializing Binance connector (testnet: {testnet})")
        
        # Initialize credentials securely
        if api_key is not None and api_secret is not None:
            self.api_key = api_key
            self.api_secret = api_secret
            self.logger.info("Loaded API key/secret from constructor arguments")
        elif use_credentials:
            try:
                cred_manager = CredentialsManager()
                credentials = cred_manager.get_credentials('binance')
                self.api_key = credentials['api_key']
                self.api_secret = credentials['api_secret']
                self.logger.info("Loaded secure credentials for Binance")
            except Exception as e:
                self.logger.error(f"Failed to load Binance credentials: {e}")
                raise ValueError(f"Could not load Binance credentials: {e}")
        else:
            # For testing purposes only
            self.logger.warning("Using empty credentials - limited to public API endpoints only")
            self.api_key = ""
            self.api_secret = ""
        
        # Configure CCXT options
        options = {
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'timeout': 30000,  # 30 seconds timeout
            'verbose': False,  # Set to True for debugging
        }
        
        # Add testnet configuration if requested
        if testnet:
            options['test'] = True
            self.logger.info("Using Binance testnet")
        
        # Initialize exchange
        try:
            self.exchange = ccxt.binance(options)
            self.logger.info("CCXT Binance exchange instance created")
        except Exception as e:
            self.logger.error(f"Failed to initialize CCXT Binance: {e}")
            raise
        
        # Initialize circuit breaker
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            max_drawdown_pct=0.10,
            volatility_threshold=3.0,
            max_consecutive_losses=5,
            cooldown_minutes=5,
            max_api_errors=5
        )
        
        # Initialize state tracking
        self.historical_spreads = {}
        self.exchange_info = None
        self.order_history = []
        self.last_request_time = {}
        self.error_counts = {
            "network": 0,
            "exchange": 0,
            "timeout": 0,
            "auth": 0,
            "rate_limit": 0,
            "other": 0
        }
        self.last_error_reset = datetime.now()
        self.is_initialized = False
        
        # Attempt to load exchange info to verify connectivity
        asyncio.create_task(self._initialize())
    
    async def _initialize(self) -> bool:
        """
        Initialize the connector by loading exchange information and verifying connectivity.
        
        Returns:
            bool: True if initialization succeeded, False otherwise
        """
        try:
            # Test connection with public API call
            self.logger.info("Testing connection to Binance API...")
            await self.exchange.fetch_time()
            
            # Load exchange information (markets, trading pairs, etc.)
            self.logger.info("Loading exchange information...")
            exchange_info = await self.exchange.load_markets(reload=True)
            
            # Cache exchange information
            self.exchange_info = exchange_info
            self.is_initialized = True
            
            # Log successful initialization
            pairs_count = len(exchange_info.keys())
            self.logger.info(f"Successfully initialized Binance connector - {pairs_count} trading pairs available")
            
            return True
            
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error during initialization: {e}")
            self._record_error("network", e)
            return False
            
        except ccxt.AuthenticationError as e:
            self.logger.error(f"Authentication error during initialization: {e}")
            self._record_error("auth", e)
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {e}")
            self.logger.error(traceback.format_exc())
            self._record_error("other", e)
            return False
    
    def _record_error(self, error_type: str, error: Exception) -> None:
        """
        Record an error in the connector and potentially trigger circuit breaker.
        
        Args:
            error_type (str): The type of error
            error (Exception): The exception that occurred
        """
        # Reset error counts every hour
        if (datetime.now() - self.last_error_reset).total_seconds() > 3600:
            self.error_counts = {k: 0 for k in self.error_counts}
            self.last_error_reset = datetime.now()
        
        # Increment the appropriate error counter
        if error_type in self.error_counts:
            self.error_counts[error_type] += 1
        else:
            self.error_counts["other"] += 1
            
        # Check if we should trigger circuit breaker
        total_errors = sum(self.error_counts.values())
        if total_errors >= self.circuit_breaker.max_api_errors:
            # Create error details
            details = {
                "error_counts": self.error_counts,
                "last_error": str(error),
                "error_type": error_type
            }
            
            # Record in circuit breaker
            self.circuit_breaker.record_error(error_type, error)
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ticker data for a symbol with enhanced error handling.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Optional[Dict[str, Any]]: Ticker data or None if an error occurred
        """
        # Check if circuit breaker is active
        can_trade, reason = self.circuit_breaker.can_trade(1.0)  # Use 1.0 as dummy value
        if not can_trade:
            self.logger.warning(f"Cannot fetch ticker for {symbol}: {reason}")
            return None
            
        # Record request time for rate limiting analytics
        endpoint = f"fetch_ticker_{symbol}"
        self.last_request_time[endpoint] = time.time()
        
        try:
            # Fetch ticker data from exchange
            self.logger.debug(f"Fetching ticker for {symbol}")
            ticker = await self.exchange.fetch_ticker(symbol)
            
            # Update historical spread data for this symbol
            if ticker and 'bid' in ticker and 'ask' in ticker and ticker['bid'] and ticker['ask']:
                spread = ticker['ask'] - ticker['bid']
                spread_pct = spread / ticker['bid'] if ticker['bid'] > 0 else 0
                
                if symbol not in self.historical_spreads:
                    self.historical_spreads[symbol] = []
                    
                # Keep only the last 100 spread values
                if len(self.historical_spreads[symbol]) >= 100:
                    self.historical_spreads[symbol].pop(0)
                    
                self.historical_spreads[symbol].append(spread_pct)
                
            return ticker
            
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error when fetching ticker for {symbol}: {e}")
            self._record_error("network", e)
            
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error when fetching ticker for {symbol}: {e}")
            self._record_error("exchange", e) 
            
        except ccxt.RequestTimeout as e:
            self.logger.error(f"Timeout when fetching ticker for {symbol}: {e}")
            self._record_error("timeout", e)
            
        except ccxt.RateLimitExceeded as e:
            self.logger.error(f"Rate limit exceeded when fetching ticker for {symbol}: {e}")
            self._record_error("rate_limit", e)
            # Add exponential backoff
            await asyncio.sleep(2)
            
        except ccxt.AuthenticationError as e:
            self.logger.error(f"Authentication error when fetching ticker for {symbol}: {e}")
            self._record_error("auth", e)
            
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching ticker for {symbol}: {e}")
            self.logger.error(traceback.format_exc())
            self._record_error("other", e)
            
        return None
    
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Fetch order book for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            limit (int): Number of orders to fetch (default: 20)
            
        Returns:
            Optional[Dict[str, Any]]: Order book data or None if an error occurred
        """
        try:
            order_book = await self.exchange.fetch_order_book(symbol, limit)
            return order_book
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error when fetching order book for {symbol}: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error when fetching order book for {symbol}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching order book for {symbol}: {e}")
        return None
    
    async def create_order(self, symbol: str, order_type: str, side: str, 
                          amount: float, price: Optional[float] = None,
                          params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create an order on the exchange with comprehensive error handling and safety checks.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            order_type (str): Order type ('limit', 'market', etc.)
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount
            price (Optional[float]): Order price (required for limit orders)
            params (Optional[Dict[str, Any]]): Additional parameters for the order
            
        Returns:
            Optional[Dict[str, Any]]: Order data or None if an error occurred
        """
        # Verify initialization
        if not self.is_initialized:
            self.logger.error(f"Cannot create order - connector not initialized")
            return None
            
        # Check if circuit breaker is active
        can_trade, reason = self.circuit_breaker.can_trade(amount * (price or 1.0))
        if not can_trade:
            self.logger.warning(f"Cannot create order - circuit breaker active: {reason}")
            return None
            
        # Verify credentials for trading
        if not self.api_key or not self.api_secret:
            self.logger.error("Cannot create order - API credentials not set")
            return None
        
        # Validate inputs
        if order_type.lower() == 'limit' and price is None:
            self.logger.error(f"Cannot create limit order without price")
            return None
            
        # Safety check for order parameters
        if amount <= 0:
            self.logger.error(f"Invalid order amount: {amount}")
            return None
            
        # Initialize parameters
        params = params or {}
        max_retries = 3
        last_error = None
        
        # Record attempt in our metrics
        order_key = f"{symbol}_{side}_{order_type}"
        self.last_request_time[f"create_order_{order_key}"] = time.time()
        
        # Implement retries with exponential backoff
        for attempt in range(max_retries):
            try:
                # Log the order attempt
                self.logger.info(
                    f"Creating order: {symbol} {side} {order_type} {amount}" + 
                    (f" @ {price}" if price else "")
                )
                
                # Execute the order
                order = await self.exchange.create_order(symbol, order_type, side, amount, price, params)
                
                # Log success
                self.logger.info(
                    f"Order created: {order['id']} for {symbol} {side} {amount}" +
                    (f" @ {price}" if price else "")
                )
                
                # Record in order history
                order_record = {
                    "id": order['id'],
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "amount": amount,
                    "price": price,
                    "timestamp": datetime.now().isoformat(),
                    "status": order['status'] if 'status' in order else 'created'
                }
                self.order_history.append(order_record)
                
                # Return the order
                return order
                
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error when creating order (attempt {attempt+1}/{max_retries}): {e}")
                self._record_error("network", e)
                last_error = e
                
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error when creating order: {e}")
                self._record_error("exchange", e)
                last_error = e
                
                # If it's a permanent error like insufficient funds, don't retry
                if any(x in str(e).lower() for x in ["insufficient", "invalid", "min", "max", "precision"]):
                    self.logger.error(f"Permanent exchange error, not retrying: {e}")
                    break
                    
            except ccxt.RequestTimeout as e:
                self.logger.error(f"Timeout when creating order: {e}")
                self._record_error("timeout", e)
                last_error = e
                
            except ccxt.RateLimitExceeded as e:
                self.logger.error(f"Rate limit exceeded when creating order: {e}")
                self._record_error("rate_limit", e)
                last_error = e
                
                # Use longer backoff for rate limits
                await asyncio.sleep(5 * (2 ** attempt))
                continue
                
            except ccxt.AuthenticationError as e:
                self.logger.error(f"Authentication error when creating order: {e}")
                self._record_error("auth", e)
                # Don't retry auth errors
                return None
                
            except Exception as e:
                self.logger.error(f"Unexpected error when creating order: {e}")
                self.logger.error(traceback.format_exc())
                self._record_error("other", e)
                last_error = e
            
            # Calculate backoff delay
            if attempt < max_retries - 1:
                retry_delay = 2 ** attempt
                self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries}) after {retry_delay}s")
                await asyncio.sleep(retry_delay)
        
        # If we got here, all retries failed
        self.logger.error(f"Order creation failed after {max_retries} attempts")
        
        # Check if we need to trigger circuit breaker
        if last_error:
            details = {
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "amount": amount,
                "price": price,
                "error": str(last_error)
            }
            
            # Only trigger circuit breaker for persistent errors
            if self.error_counts["network"] > 2 or self.error_counts["exchange"] > 2:
                self.circuit_breaker.trigger(TriggerReason.API_ERRORS, details)
        
        return None
    
    async def cancel_order(self, order_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Cancel an existing order.
        
        Args:
            order_id (str): Order ID to cancel
            symbol (str): Trading pair symbol
            
        Returns:
            Optional[Dict[str, Any]]: Cancellation result or None if an error occurred
        """
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Order cancelled: {order_id} for {symbol}")
            return result
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error when cancelling order: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error when cancelling order: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error when cancelling order: {e}")
        return None
    
    async def fetch_balance(self) -> Optional[Dict[str, Any]]:
        """
        Fetch account balance.
        
        Returns:
            Optional[Dict[str, Any]]: Balance data or None if an error occurred
        """
        try:
            balance = await self.exchange.fetch_balance()
            return balance
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error when fetching balance: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error when fetching balance: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching balance: {e}")
        return None
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', 
                         since: Optional[int] = None, limit: Optional[int] = None) -> Optional[List[List[float]]]:
        """
        Fetch OHLCV (candlestick) data.
        
        Args:
            symbol (str): Trading pair symbol
            timeframe (str): Timeframe ('1m', '5m', '1h', '1d', etc.)
            since (Optional[int]): Timestamp in ms to fetch from
            limit (Optional[int]): Number of candles to fetch
            
        Returns:
            Optional[List[List[float]]]: OHLCV data or None if an error occurred
        """
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            return ohlcv
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error when fetching OHLCV: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error when fetching OHLCV: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching OHLCV: {e}")
        return None
    
    async def triangular_arbitrage(self, base_symbol: str, quote_symbol: str, 
                                  arbitrage_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Detect and execute triangular arbitrage opportunities.
        
        Args:
            base_symbol (str): Base currency symbol (e.g., 'BTC')
            quote_symbol (str): Quote currency symbol (e.g., 'USDT')
            arbitrage_symbol (str): Arbitrage currency symbol (e.g., 'ETH')
            
        Returns:
            Optional[Dict[str, Any]]: Arbitrage opportunity data or None if not found/error
        """
        try:
            # Fetch the relevant tickers
            ticker_base_quote = await self.fetch_ticker(f"{base_symbol}/{quote_symbol}")
            ticker_arbitrage_base = await self.fetch_ticker(f"{arbitrage_symbol}/{base_symbol}")
            ticker_arbitrage_quote = await self.fetch_ticker(f"{arbitrage_symbol}/{quote_symbol}")
            
            if not ticker_base_quote or not ticker_arbitrage_base or not ticker_arbitrage_quote:
                self.logger.warning("Could not fetch all required tickers for arbitrage")
                return None
            
            # Extract prices
            price_base_quote = ticker_base_quote['last']
            price_arbitrage_base = ticker_arbitrage_base['last']
            price_arbitrage_quote = ticker_arbitrage_quote['last']
            
            # Calculate arbitrage opportunity
            # Path: quote -> base -> arbitrage -> quote
            direct_path = 1.0 / price_base_quote  # quote to base
            arbitrage_path = price_arbitrage_base / price_arbitrage_quote  # base to arbitrage to quote
            
            arbitrage_ratio = direct_path * arbitrage_path
            arbitrage_profit_pct = (arbitrage_ratio - 1.0) * 100
            
            result = {
                'arbitrage_ratio': arbitrage_ratio,
                'profit_percentage': arbitrage_profit_pct,
                'path': f"{quote_symbol} -> {base_symbol} -> {arbitrage_symbol} -> {quote_symbol}",
                'prices': {
                    f"{base_symbol}/{quote_symbol}": price_base_quote,
                    f"{arbitrage_symbol}/{base_symbol}": price_arbitrage_base,
                    f"{arbitrage_symbol}/{quote_symbol}": price_arbitrage_quote
                }
            }
            
            # Log the opportunity
            if arbitrage_ratio > 1.01:  # 1% profit threshold
                self.logger.info(f"Arbitrage opportunity detected: {arbitrage_profit_pct:.2f}% profit")
                result['profitable'] = True
                
                # TODO: Execute the arbitrage trades here
                # 1. Convert quote to base
                # 2. Convert base to arbitrage
                # 3. Convert arbitrage back to quote
                
                return result
            else:
                self.logger.debug(f"No profitable arbitrage opportunity: {arbitrage_profit_pct:.2f}%")
                result['profitable'] = False
                return result
            
        except Exception as e:
            self.logger.error(f"Error in triangular arbitrage: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the connector.
        
        Returns:
            Dict[str, Any]: Status information including health metrics
        """
        # Calculate availability metrics
        request_count = len(self.last_request_time)
        error_count = sum(self.error_counts.values())
        error_rate = error_count / max(1, request_count) if request_count > 0 else 0
        
        # Get circuit breaker status
        circuit_breaker_status = self.circuit_breaker.get_status()
        
        # Compile status report
        status = {
            "initialized": self.is_initialized,
            "timestamp": datetime.now().isoformat(),
            "markets_loaded": len(self.exchange_info) if self.exchange_info else 0,
            "request_count": request_count,
            "error_counts": self.error_counts,
            "error_rate": error_rate,
            "order_history_count": len(self.order_history),
            "circuit_breaker": circuit_breaker_status,
            "api_credentials_configured": bool(self.api_key and self.api_secret),
            "tracked_symbols": list(self.historical_spreads.keys()),
            "health": {
                "status": "healthy" if error_rate < 0.1 and not circuit_breaker_status["is_active"] else "degraded",
                "issues": [],
            }
        }
        
        # Add any health issues
        if error_rate >= 0.1:
            status["health"]["issues"].append(f"High error rate: {error_rate:.1%}")
        
        if circuit_breaker_status["is_active"]:
            status["health"]["issues"].append(f"Circuit breaker active: {circuit_breaker_status['trigger_reason']}")
            
        if not self.is_initialized:
            status["health"]["issues"].append("Connector not initialized")
            
        if not self.api_key or not self.api_secret:
            status["health"]["issues"].append("API credentials not configured")
            
        # Set overall health status
        if len(status["health"]["issues"]) > 0:
            if circuit_breaker_status["is_active"] or not self.is_initialized:
                status["health"]["status"] = "critical"
            else:
                status["health"]["status"] = "degraded"
        
        return status
        
    async def ping(self) -> Tuple[bool, float]:
        """
        Ping the exchange API to check connectivity and measure latency.
        
        Returns:
            Tuple[bool, float]: (success, latency_ms)
        """
        start_time = time.time()
        try:
            await self.exchange.fetch_time()
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            return True, latency
        except Exception as e:
            self.logger.error(f"Failed to ping exchange: {e}")
            latency = (time.time() - start_time) * 1000
            return False, latency
            
    async def twap_execution(self, symbol: str, order_type: str, side: str, 
                            amount: float, price: Optional[float] = None, 
                            interval: int = 60, slices: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a TWAP (Time-Weighted Average Price) order.
        
        Args:
            symbol (str): Trading pair symbol
            order_type (str): Order type ('limit', 'market')
            side (str): Order side ('buy', 'sell')
            amount (float): Total amount to trade
            price (Optional[float]): Order price (for limit orders)
            interval (int): Time interval between slices in seconds
            slices (int): Number of slices to divide the order into
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of executed orders or None if failed
        """
        try:
            slice_amount = amount / slices
            executed_orders = []
            
            self.logger.info(f"Starting TWAP execution for {symbol} {side} {amount} in {slices} slices")
            
            for i in range(slices):
                # For limit orders, we might want to adjust the price based on current market
                current_price = price
                if order_type == 'limit' and not current_price:
                    ticker = await self.fetch_ticker(symbol)
                    if not ticker:
                        self.logger.error("Could not fetch current price for TWAP execution")
                        return None
                    current_price = ticker['bid'] if side == 'sell' else ticker['ask']
                
                # Execute the slice
                order = await self.create_order(symbol, order_type, side, slice_amount, current_price)
                if order:
                    executed_orders.append(order)
                    self.logger.info(f"TWAP slice {i+1}/{slices} executed: {order['id']}")
                else:
                    self.logger.error(f"Failed to execute TWAP slice {i+1}/{slices}")
                    # Continue with the remaining slices
                
                # Wait for the next slice
                if i < slices - 1:  # Don't wait after the last slice
                    await asyncio.sleep(interval)
            
            self.logger.info(f"TWAP execution completed: {len(executed_orders)}/{slices} slices executed")
            return executed_orders
            
        except Exception as e:
            self.logger.error(f"Error in TWAP execution: {e}")
            return None
    
    async def get_exchange_info(self) -> Optional[Dict[str, Any]]:
        """
        Get exchange information including trading pairs, limits, etc.
        
        Returns:
            Optional[Dict[str, Any]]: Exchange information or None if an error occurred
        """
        try:
            exchange_info = await self.exchange.load_markets(reload=True)
            return exchange_info
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error when fetching exchange info: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error when fetching exchange info: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching exchange info: {e}")
        return None
    
    async def fetch_open_orders(self, symbol: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch open orders.
        
        Args:
            symbol (Optional[str]): Trading pair symbol or None for all symbols
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of open orders or None if an error occurred
        """
        try:
            open_orders = await self.exchange.fetch_open_orders(symbol)
            return open_orders
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error when fetching open orders: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error when fetching open orders: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error when fetching open orders: {e}")
        return None
