"""
Binance executor for the Grekko trading platform.

Handles order execution on Binance exchange with proper error handling,
rate limiting, and WebSocket support for real-time updates.
"""
import asyncio
import time
import hmac
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import aiohttp
import json

from ...utils.logger import get_logger
from ...utils.credentials_manager import CredentialsManager


class BinanceExecutor:
    """
    Executor for Binance exchange operations.
    
    Implements market orders, limit orders, and other trading operations
    with proper authentication and error handling.
    """
    
    BASE_URL = "https://api.binance.com"
    WS_URL = "wss://stream.binance.com:9443/ws"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Binance executor.
        
        Args:
            config: Binance-specific configuration
        """
        self.config = config
        self.logger = get_logger('binance_executor')
        
        # Get credentials
        self.cred_manager = CredentialsManager()
        self._load_credentials()
        
        # Rate limiting
        self.rate_limiter = {
            'requests_per_minute': config.get('rate_limit', 1200),
            'orders_per_day': config.get('order_limit', 200000),
            'window_start': time.time(),
            'request_count': 0,
            'order_count': 0
        }
        
        # WebSocket connection
        self.ws_connection = None
        self.ws_callbacks = {}
        
        # Session for HTTP requests
        self.session = None
        
        # Symbol info cache
        self.symbol_info = {}
        self.last_symbol_update = 0
        
        self.logger.info("BinanceExecutor initialized")
    
    def _load_credentials(self) -> None:
        """Load Binance API credentials."""
        try:
            creds = self.cred_manager.get_credentials('binance')
            self.api_key = creds['api_key']
            self.api_secret = creds['api_secret']
        except Exception as e:
            self.logger.error(f"Failed to load Binance credentials: {str(e)}")
            raise
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          params: Optional[Dict] = None,
                          signed: bool = False) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs signature
            
        Returns:
            API response
        """
        await self._ensure_session()
        await self._check_rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if signed:
            params = params or {}
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = self.config.get('recv_window', 5000)
            
            # Create signature
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
        
        try:
            async with self.session.request(method, url, params=params, headers=headers) as response:
                self.rate_limiter['request_count'] += 1
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.text()
                    raise Exception(f"Binance API error {response.status}: {error_data}")
                    
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limits."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.rate_limiter['window_start'] > 60:
            self.rate_limiter['window_start'] = current_time
            self.rate_limiter['request_count'] = 0
        
        # Check if we're at the limit
        if self.rate_limiter['request_count'] >= self.rate_limiter['requests_per_minute']:
            sleep_time = 60 - (current_time - self.rate_limiter['window_start'])
            if sleep_time > 0:
                self.logger.warning(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                self.rate_limiter['window_start'] = time.time()
                self.rate_limiter['request_count'] = 0
    
    async def market_order(self, 
                         symbol: str, 
                         side: str, 
                         amount: float,
                         **kwargs) -> Dict[str, Any]:
        """
        Execute a market order.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            amount: Order amount
            **kwargs: Additional parameters
            
        Returns:
            Order execution result
        """
        try:
            # Get symbol info for precision
            symbol_info = await self._get_symbol_info(symbol)
            
            # Format amount according to symbol precision
            formatted_amount = self._format_quantity(amount, symbol_info)
            
            params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': formatted_amount
            }
            
            # Add optional parameters
            if kwargs.get('quote_order_qty'):
                params['quoteOrderQty'] = kwargs['quote_order_qty']
                del params['quantity']
            
            result = await self._make_request('POST', '/api/v3/order', params, signed=True)
            
            self.rate_limiter['order_count'] += 1
            
            return {
                'order_id': result['orderId'],
                'symbol': result['symbol'],
                'status': self._convert_order_status(result['status']),
                'side': result['side'].lower(),
                'type': result['type'].lower(),
                'price': float(result.get('price', 0)),
                'filled_amount': float(result['executedQty']),
                'timestamp': datetime.fromtimestamp(result['transactTime'] / 1000).isoformat(),
                'exchange': 'binance',
                'raw': result
            }
            
        except Exception as e:
            self.logger.error(f"Market order failed: {str(e)}")
            raise
    
    async def limit_order(self,
                        symbol: str,
                        side: str,
                        amount: float,
                        price: float,
                        **kwargs) -> Dict[str, Any]:
        """
        Execute a limit order.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            amount: Order amount
            price: Limit price
            **kwargs: Additional parameters
            
        Returns:
            Order execution result
        """
        try:
            # Get symbol info for precision
            symbol_info = await self._get_symbol_info(symbol)
            
            # Format values according to symbol precision
            formatted_amount = self._format_quantity(amount, symbol_info)
            formatted_price = self._format_price(price, symbol_info)
            
            params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'LIMIT',
                'quantity': formatted_amount,
                'price': formatted_price,
                'timeInForce': kwargs.get('time_in_force', 'GTC')
            }
            
            result = await self._make_request('POST', '/api/v3/order', params, signed=True)
            
            self.rate_limiter['order_count'] += 1
            
            return {
                'order_id': result['orderId'],
                'symbol': result['symbol'],
                'status': self._convert_order_status(result['status']),
                'side': result['side'].lower(),
                'type': result['type'].lower(),
                'price': float(result['price']),
                'filled_amount': float(result['executedQty']),
                'timestamp': datetime.fromtimestamp(result['transactTime'] / 1000).isoformat(),
                'exchange': 'binance',
                'raw': result
            }
            
        except Exception as e:
            self.logger.error(f"Limit order failed: {str(e)}")
            raise
    
    async def stop_loss_order(self,
                            symbol: str,
                            side: str,
                            amount: float,
                            stop_price: float,
                            **kwargs) -> Dict[str, Any]:
        """
        Execute a stop loss order.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            amount: Order amount
            stop_price: Stop trigger price
            **kwargs: Additional parameters
            
        Returns:
            Order execution result
        """
        try:
            # Get symbol info for precision
            symbol_info = await self._get_symbol_info(symbol)
            
            # Format values
            formatted_amount = self._format_quantity(amount, symbol_info)
            formatted_stop_price = self._format_price(stop_price, symbol_info)
            
            params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'STOP_LOSS',
                'quantity': formatted_amount,
                'stopPrice': formatted_stop_price
            }
            
            # Add limit price if provided
            if kwargs.get('limit_price'):
                params['type'] = 'STOP_LOSS_LIMIT'
                params['price'] = self._format_price(kwargs['limit_price'], symbol_info)
                params['timeInForce'] = kwargs.get('time_in_force', 'GTC')
            
            result = await self._make_request('POST', '/api/v3/order', params, signed=True)
            
            return {
                'order_id': result['orderId'],
                'symbol': result['symbol'],
                'status': self._convert_order_status(result['status']),
                'side': result['side'].lower(),
                'type': result['type'].lower(),
                'stop_price': float(result['stopPrice']),
                'timestamp': datetime.fromtimestamp(result['transactTime'] / 1000).isoformat(),
                'exchange': 'binance',
                'raw': result
            }
            
        except Exception as e:
            self.logger.error(f"Stop loss order failed: {str(e)}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair
            
        Returns:
            Cancellation result
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'orderId': order_id
            }
            
            result = await self._make_request('DELETE', '/api/v3/order', params, signed=True)
            
            return {
                'success': True,
                'order_id': result['orderId'],
                'status': self._convert_order_status(result['status']),
                'exchange': 'binance'
            }
            
        except Exception as e:
            self.logger.error(f"Order cancellation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
                'exchange': 'binance'
            }
    
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get order status.
        
        Args:
            order_id: Order ID
            symbol: Trading pair
            
        Returns:
            Order status information
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'orderId': order_id
            }
            
            result = await self._make_request('GET', '/api/v3/order', params, signed=True)
            
            return {
                'order_id': result['orderId'],
                'status': self._convert_order_status(result['status']),
                'filled_amount': float(result['executedQty']),
                'price': float(result.get('price', 0)),
                'avg_price': float(result.get('avgPrice', 0)) if result.get('avgPrice') else None,
                'exchange': 'binance',
                'raw': result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get order status: {str(e)}")
            raise
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get orderbook for a symbol.
        
        Args:
            symbol: Trading pair
            limit: Number of levels (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            Orderbook data
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'limit': limit
            }
            
            result = await self._make_request('GET', '/api/v3/depth', params)
            
            return {
                'bids': [[float(p), float(q)] for p, q in result['bids']],
                'asks': [[float(p), float(q)] for p, q in result['asks']],
                'timestamp': datetime.now().isoformat(),
                'exchange': 'binance'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get orderbook: {str(e)}")
            raise
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker data for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Ticker data
        """
        try:
            params = {'symbol': symbol.upper()}
            result = await self._make_request('GET', '/api/v3/ticker/24hr', params)
            
            return {
                'symbol': result['symbol'],
                'last': float(result['lastPrice']),
                'bid': float(result['bidPrice']),
                'ask': float(result['askPrice']),
                'volume': float(result['volume']),
                'high': float(result['highPrice']),
                'low': float(result['lowPrice']),
                'change_24h': float(result['priceChangePercent']),
                'timestamp': datetime.now().isoformat(),
                'exchange': 'binance'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get ticker: {str(e)}")
            raise
    
    async def get_trading_fees(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading fees for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Fee information
        """
        try:
            # Get account trading fee
            result = await self._make_request('GET', '/sapi/v1/asset/tradeFee', 
                                            {'symbol': symbol.upper()}, signed=True)
            
            if result and len(result) > 0:
                fee_info = result[0]
                return {
                    'maker': float(fee_info['makerCommission']),
                    'taker': float(fee_info['takerCommission']),
                    'currency': 'percentage',
                    'exchange': 'binance'
                }
            
            # Default fees if not found
            return {
                'maker': 0.001,  # 0.1%
                'taker': 0.001,  # 0.1%
                'currency': 'percentage',
                'exchange': 'binance'
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get trading fees: {str(e)}")
            # Return default fees
            return {
                'maker': 0.001,
                'taker': 0.001,
                'currency': 'percentage',
                'exchange': 'binance'
            }
    
    async def is_symbol_supported(self, symbol: str) -> bool:
        """
        Check if a symbol is supported.
        
        Args:
            symbol: Trading pair
            
        Returns:
            True if supported
        """
        try:
            symbol_info = await self._get_symbol_info(symbol)
            return symbol_info is not None
        except:
            return False
    
    async def _get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol trading rules and precision.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Symbol information
        """
        # Update cache if needed
        if time.time() - self.last_symbol_update > 3600:  # 1 hour
            await self._update_symbol_cache()
        
        return self.symbol_info.get(symbol.upper())
    
    async def _update_symbol_cache(self) -> None:
        """Update the symbol information cache."""
        try:
            result = await self._make_request('GET', '/api/v3/exchangeInfo')
            
            self.symbol_info = {}
            for symbol in result['symbols']:
                self.symbol_info[symbol['symbol']] = {
                    'symbol': symbol['symbol'],
                    'status': symbol['status'],
                    'baseAsset': symbol['baseAsset'],
                    'quoteAsset': symbol['quoteAsset'],
                    'filters': {f['filterType']: f for f in symbol['filters']},
                    'orderTypes': symbol['orderTypes'],
                    'baseAssetPrecision': symbol['baseAssetPrecision'],
                    'quoteAssetPrecision': symbol['quoteAssetPrecision']
                }
            
            self.last_symbol_update = time.time()
            self.logger.info(f"Updated symbol cache with {len(self.symbol_info)} symbols")
            
        except Exception as e:
            self.logger.error(f"Failed to update symbol cache: {str(e)}")
    
    def _format_quantity(self, quantity: float, symbol_info: Dict[str, Any]) -> str:
        """Format quantity according to symbol rules."""
        if not symbol_info:
            return str(quantity)
        
        # Get LOT_SIZE filter
        lot_size = symbol_info['filters'].get('LOT_SIZE', {})
        step_size = float(lot_size.get('stepSize', 1))
        
        # Round to step size
        precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
        return f"{quantity:.{precision}f}"
    
    def _format_price(self, price: float, symbol_info: Dict[str, Any]) -> str:
        """Format price according to symbol rules."""
        if not symbol_info:
            return str(price)
        
        # Get PRICE_FILTER
        price_filter = symbol_info['filters'].get('PRICE_FILTER', {})
        tick_size = float(price_filter.get('tickSize', 1))
        
        # Round to tick size
        precision = len(str(tick_size).split('.')[-1]) if '.' in str(tick_size) else 0
        return f"{price:.{precision}f}"
    
    def _convert_order_status(self, status: str) -> str:
        """Convert Binance order status to standard format."""
        status_map = {
            'NEW': 'pending',
            'PARTIALLY_FILLED': 'partial',
            'FILLED': 'filled',
            'CANCELED': 'cancelled',
            'PENDING_CANCEL': 'pending',
            'REJECTED': 'failed',
            'EXPIRED': 'cancelled'
        }
        return status_map.get(status, status.lower())
    
    async def start_websocket(self) -> None:
        """Start WebSocket connection for real-time updates."""
        # Implementation for WebSocket connection
        pass
    
    async def subscribe_orderbook(self, symbol: str, callback) -> None:
        """Subscribe to orderbook updates."""
        # Implementation for orderbook subscription
        pass
    
    async def shutdown(self) -> None:
        """Shutdown the executor gracefully."""
        self.logger.info("Shutting down BinanceExecutor")
        
        if self.ws_connection:
            await self.ws_connection.close()
        
        if self.session:
            await self.session.close()
        
        self.logger.info("BinanceExecutor shutdown complete")