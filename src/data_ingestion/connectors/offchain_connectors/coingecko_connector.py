"""
CoinGecko API Connector for Grekko

- Provides integration with CoinGecko cryptocurrency market data API
- Fetches price, volume, market cap, and other market data
- Includes error handling and rate limiting support
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import aiohttp

from ....utils.logger import get_logger

logger = get_logger("coingecko_connector")

class CoinGeckoConnector:
    """
    Connector for CoinGecko cryptocurrency market data API.
    Provides comprehensive market data including prices, volumes, and market caps.
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CoinGecko connector.
        
        Args:
            api_key: Optional API key for CoinGecko Pro (higher rate limits)
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.api_key = api_key
        self.logger = logger
        self.last_request_time = 0
        self.rate_limit_delay = 1.5  # Seconds between requests (free tier limit)
        
        # Use a shorter delay if API key is provided (Pro tier)
        if api_key:
            self.rate_limit_delay = 0.1
            
        self.logger.info("CoinGecko connector initialized")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make a rate-limited request to the CoinGecko API.
        
        Args:
            endpoint: API endpoint to call
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
        
        url = f"{self.BASE_URL}/{endpoint}"
        request_params = params or {}
        
        # Add API key if available
        if self.api_key:
            request_params["x_cg_pro_api_key"] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                self.last_request_time = time.time()
                async with session.get(url, params=request_params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        self.logger.error(f"CoinGecko API error: {response.status} - {error_text}")
                        return None
        except asyncio.TimeoutError:
            self.logger.error(f"Request to {endpoint} timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error making request to {endpoint}: {str(e)}")
            return None
    
    async def get_price(self, coins: List[str], vs_currencies: List[str] = ["usd"],
                      include_market_cap: bool = False, include_24hr_vol: bool = False,
                      include_24hr_change: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get current prices for a list of coins.
        
        Args:
            coins: List of coin IDs (e.g. bitcoin, ethereum)
            vs_currencies: List of currencies to get prices in
            include_market_cap: Include market cap data
            include_24hr_vol: Include 24h volume data
            include_24hr_change: Include 24h price change data
            
        Returns:
            Dict containing price data or None if error
        """
        params = {
            "ids": ",".join(coins),
            "vs_currencies": ",".join(vs_currencies),
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_vol": str(include_24hr_vol).lower(),
            "include_24hr_change": str(include_24hr_change).lower(),
            "precision": "full"
        }
        
        return await self._make_request("simple/price", params)
    
    async def get_coin_data(self, coin_id: str, localization: bool = False,
                          tickers: bool = True, market_data: bool = True,
                          community_data: bool = False, developer_data: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get detailed data for a specific coin.
        
        Args:
            coin_id: Coin ID (e.g. bitcoin, ethereum)
            localization: Include localized data
            tickers: Include ticker data
            market_data: Include market data
            community_data: Include community data
            developer_data: Include developer data
            
        Returns:
            Dict containing coin data or None if error
        """
        params = {
            "localization": str(localization).lower(),
            "tickers": str(tickers).lower(),
            "market_data": str(market_data).lower(),
            "community_data": str(community_data).lower(),
            "developer_data": str(developer_data).lower()
        }
        
        return await self._make_request(f"coins/{coin_id}", params)
    
    async def get_market_chart(self, coin_id: str, vs_currency: str = "usd",
                             days: str = "1", interval: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get historical market data for a coin.
        
        Args:
            coin_id: Coin ID (e.g. bitcoin, ethereum)
            vs_currency: Currency to get data in
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            interval: Data interval (daily, hourly, minutely)
            
        Returns:
            Dict containing market chart data or None if error
        """
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        
        if interval:
            params["interval"] = interval
            
        return await self._make_request(f"coins/{coin_id}/market_chart", params)
    
    async def get_ohlc(self, coin_id: str, vs_currency: str = "usd",
                      days: str = "1") -> Optional[List[List[float]]]:
        """
        Get OHLC (Open, High, Low, Close) data for a coin.
        
        Args:
            coin_id: Coin ID (e.g. bitcoin, ethereum)
            vs_currency: Currency to get data in
            days: Number of days (1, 7, 14, 30, 90, 180, 365)
            
        Returns:
            List of OHLC data or None if error
        """
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        
        return await self._make_request(f"coins/{coin_id}/ohlc", params)
    
    async def get_trending(self) -> Optional[Dict[str, Any]]:
        """
        Get trending coins data.
        
        Returns:
            Dict containing trending coins data or None if error
        """
        return await self._make_request("search/trending")
    
    async def get_global_data(self) -> Optional[Dict[str, Any]]:
        """
        Get global cryptocurrency market data.
        
        Returns:
            Dict containing global market data or None if error
        """
        return await self._make_request("global")
    
    async def search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for coins, categories and markets.
        
        Args:
            query: Search query
            
        Returns:
            Dict containing search results or None if error
        """
        params = {
            "query": query
        }
        
        return await self._make_request("search", params)
    
    async def convert_trading_pair(self, trading_pair: str) -> Optional[str]:
        """
        Convert exchange trading pair to CoinGecko coin ID.
        
        Args:
            trading_pair: Trading pair (e.g. BTC/USDT, ETH-USDT)
            
        Returns:
            CoinGecko coin ID or None if not found
        """
        # Handle common formats
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
            # are the base asset (common in many crypto pairs)
            base_asset = clean_pair[:3]  # Default to first 3 chars
        
        # Map common symbols to CoinGecko IDs
        common_mappings = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "DOT": "polkadot",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "LINK": "chainlink",
            "MATIC": "matic-network",
            "LTC": "litecoin",
            "UNI": "uniswap",
            "SHIB": "shiba-inu",
            "ATOM": "cosmos",
            "XLM": "stellar",
            "FTM": "fantom",
            "ALGO": "algorand",
            "TRX": "tron",
            "NEAR": "near",
            "APE": "apecoin",
            "HBAR": "hedera-hashgraph",
            "VET": "vechain",
            "AXS": "axie-infinity",
            "SAND": "the-sandbox",
            "MANA": "decentraland",
            "AAVE": "aave",
            "EGLD": "elrond-erd-2",
            "THETA": "theta-token",
            "EOS": "eos",
            "KSM": "kusama"
        }
        
        # If the base asset is in our mapping, return it
        if base_asset in common_mappings:
            return common_mappings[base_asset]
        
        # Otherwise, try to search for it
        try:
            search_results = await self.search(base_asset.lower())
            if search_results and search_results.get("coins"):
                # Return the first coin result's ID
                return search_results["coins"][0]["id"]
        except:
            pass
            
        # If all else fails, return the lowercase base asset
        # (might work for some coins with simple names)
        return base_asset.lower()