"""
Alpha Vantage API Connector for Grekko

- Provides integration with Alpha Vantage financial data API
- Fetches forex data, technical indicators, and fundamental data
- Includes error handling and rate limiting support
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import aiohttp

from ....utils.logger import get_logger

logger = get_logger("alphavantage_connector")

class AlphaVantageConnector:
    """
    Connector for Alpha Vantage financial data API.
    Provides access to forex, technical indicators, and fundamental data.
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Alpha Vantage connector.
        
        Args:
            api_key: Alpha Vantage API key
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.api_key = api_key
        self.logger = logger
        self.last_request_time = 0
        self.rate_limit_delay = 12.0  # Free tier allows 5 requests per minute (12s between requests)
        
        # Check if premium tier config is provided
        if config and config.get("premium_tier"):
            self.rate_limit_delay = 1.0  # Adjusted for premium tier
            
        self.logger.info("Alpha Vantage connector initialized")
    
    async def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make a rate-limited request to the Alpha Vantage API.
        
        Args:
            params: Query parameters
            
        Returns:
            JSON response as dictionary or None if error
        """
        # Implement basic rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            delay = self.rate_limit_delay - time_since_last_request
            await asyncio.sleep(delay)
        
        # Add API key to parameters
        request_params = params.copy()
        request_params["apikey"] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                self.last_request_time = time.time()
                async with session.get(self.BASE_URL, params=request_params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for API errors in the response
                        if "Error Message" in data:
                            self.logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                            return None
                        
                        if "Note" in data and "API call frequency" in data["Note"]:
                            self.logger.warning(f"Alpha Vantage rate limit warning: {data['Note']}")
                            # Still return the data since it might be valid
                            
                        return data
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Alpha Vantage API error: {response.status} - {error_text}")
                        return None
        except asyncio.TimeoutError:
            self.logger.error("Request to Alpha Vantage API timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error making request to Alpha Vantage API: {str(e)}")
            return None
    
    async def get_forex_rate(self, from_currency: str, to_currency: str) -> Optional[Dict[str, Any]]:
        """
        Get current exchange rate between two currencies.
        
        Args:
            from_currency: From currency code
            to_currency: To currency code
            
        Returns:
            Dict containing exchange rate data or None if error
        """
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        
        return await self._make_request(params)
    
    async def get_intraday(self, symbol: str, interval: str = "60min", 
                          outputsize: str = "compact") -> Optional[Dict[str, Any]]:
        """
        Get intraday time series data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            interval: Time interval between data points (1min, 5min, 15min, 30min, 60min)
            outputsize: Amount of data to return (compact or full)
            
        Returns:
            Dict containing time series data or None if error
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }
        
        return await self._make_request(params)
    
    async def get_daily(self, symbol: str, outputsize: str = "compact") -> Optional[Dict[str, Any]]:
        """
        Get daily time series data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            outputsize: Amount of data to return (compact or full)
            
        Returns:
            Dict containing time series data or None if error
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize
        }
        
        return await self._make_request(params)
    
    async def get_crypto_intraday(self, symbol: str, market: str = "USD", 
                                interval: str = "60min") -> Optional[Dict[str, Any]]:
        """
        Get intraday cryptocurrency data.
        
        Args:
            symbol: The crypto symbol (e.g. BTC)
            market: Market to compare against (e.g. USD)
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            Dict containing crypto data or None if error
        """
        params = {
            "function": "CRYPTO_INTRADAY",
            "symbol": symbol,
            "market": market,
            "interval": interval
        }
        
        return await self._make_request(params)
    
    async def get_crypto_daily(self, symbol: str, market: str = "USD") -> Optional[Dict[str, Any]]:
        """
        Get daily cryptocurrency data.
        
        Args:
            symbol: The crypto symbol (e.g. BTC)
            market: Market to compare against (e.g. USD)
            
        Returns:
            Dict containing crypto data or None if error
        """
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market
        }
        
        return await self._make_request(params)
    
    async def get_technical_indicator(self, symbol: str, indicator: str, interval: str = "daily",
                                    time_period: int = 14, series_type: str = "close") -> Optional[Dict[str, Any]]:
        """
        Get technical indicator data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            indicator: Technical indicator function (RSI, MACD, BBANDS, etc.)
            interval: Time interval (1min, 5min, 15min, 30min, 60min, daily, weekly, monthly)
            time_period: Number of data points to calculate the indicator
            series_type: Price type (close, open, high, low)
            
        Returns:
            Dict containing indicator data or None if error
        """
        params = {
            "function": indicator,
            "symbol": symbol,
            "interval": interval,
            "time_period": str(time_period),
            "series_type": series_type
        }
        
        return await self._make_request(params)
    
    async def get_rsi(self, symbol: str, interval: str = "daily", 
                    time_period: int = 14, series_type: str = "close") -> Optional[Dict[str, Any]]:
        """
        Get RSI (Relative Strength Index) data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            interval: Time interval
            time_period: Number of data points to calculate RSI
            series_type: Price type
            
        Returns:
            Dict containing RSI data or None if error
        """
        return await self.get_technical_indicator(symbol, "RSI", interval, time_period, series_type)
    
    async def get_macd(self, symbol: str, interval: str = "daily", 
                     series_type: str = "close", fastperiod: int = 12,
                     slowperiod: int = 26, signalperiod: int = 9) -> Optional[Dict[str, Any]]:
        """
        Get MACD (Moving Average Convergence/Divergence) data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            interval: Time interval
            series_type: Price type
            fastperiod: Fast period
            slowperiod: Slow period
            signalperiod: Signal period
            
        Returns:
            Dict containing MACD data or None if error
        """
        params = {
            "function": "MACD",
            "symbol": symbol,
            "interval": interval,
            "series_type": series_type,
            "fastperiod": str(fastperiod),
            "slowperiod": str(slowperiod),
            "signalperiod": str(signalperiod)
        }
        
        return await self._make_request(params)
    
    async def get_bbands(self, symbol: str, interval: str = "daily", 
                       time_period: int = 20, series_type: str = "close",
                       nbdevup: int = 2, nbdevdn: int = 2) -> Optional[Dict[str, Any]]:
        """
        Get Bollinger Bands data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            interval: Time interval
            time_period: Number of data points
            series_type: Price type
            nbdevup: Standard deviation multiplier for upper band
            nbdevdn: Standard deviation multiplier for lower band
            
        Returns:
            Dict containing Bollinger Bands data or None if error
        """
        params = {
            "function": "BBANDS",
            "symbol": symbol,
            "interval": interval,
            "time_period": str(time_period),
            "series_type": series_type,
            "nbdevup": str(nbdevup),
            "nbdevdn": str(nbdevdn),
            "matype": "0"  # Simple Moving Average
        }
        
        return await self._make_request(params)
    
    async def convert_symbol(self, trading_pair: str) -> str:
        """
        Convert exchange trading pair to Alpha Vantage symbol format.
        
        Args:
            trading_pair: Trading pair (e.g. BTC/USDT, ETH-USD)
            
        Returns:
            Symbol in Alpha Vantage format
        """
        # For crypto, Alpha Vantage uses symbols like "BTC" (not trading pairs)
        # Remove common separators
        clean_pair = trading_pair.replace("/", "").replace("-", "").replace("_", "").upper()
        
        # Extract the base asset (first part)
        base_asset = None
        
        # Try to identify the base asset by removing common quote assets
        for quote in ["USDT", "USD", "BTC", "ETH", "BUSD", "USDC"]:
            if clean_pair.endswith(quote):
                base_asset = clean_pair[:-len(quote)]
                break
        
        if not base_asset:
            # If we couldn't identify a known quote asset, assume the first 3-4 characters
            base_asset = clean_pair[:3]  # Default to first 3 chars
            
        return base_asset