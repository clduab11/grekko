"""
Market Data Aggregator for Grekko

- Combines data from multiple sources (TradingView, CoinGecko, Alpha Vantage)
- Provides fallback capabilities if one source fails
- Standardizes data format across different sources
"""

import asyncio
from typing import Dict, Any, Optional, List
import time

from .offchain_connectors.tradingview_connector import TradingViewConnector
from .offchain_connectors.coingecko_connector import CoinGeckoConnector
from .offchain_connectors.alphavantage_connector import AlphaVantageConnector
from ..utils.logger import get_logger

logger = get_logger("market_data_aggregator")

class MarketDataAggregator:
    """
    Aggregates market data from multiple sources with fallback capabilities.
    Provides a unified interface for fetching technical analysis and market data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the market data aggregator.
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        self.logger = logger
        
        # Initialize connectors
        self.tradingview = TradingViewConnector(config.get("tradingview", {}))
        
        # CoinGecko connector (with optional API key)
        coingecko_api_key = None
        if config and "coingecko" in config and "api_key" in config["coingecko"]:
            coingecko_api_key = config["coingecko"]["api_key"]
        self.coingecko = CoinGeckoConnector(coingecko_api_key, config.get("coingecko", {}))
        
        # Alpha Vantage connector (requires API key)
        alphavantage_api_key = None
        if config and "alphavantage" in config and "api_key" in config["alphavantage"]:
            alphavantage_api_key = config["alphavantage"]["api_key"]
        else:
            # Use a demo key with limited functionality for testing
            alphavantage_api_key = "demo"
            
        self.alphavantage = AlphaVantageConnector(alphavantage_api_key, config.get("alphavantage", {}))
        
        self.logger.info("Market data aggregator initialized with all connectors")
    
    async def get_technical_analysis(self, symbol: str, exchange: str = "BINANCE",
                                   interval: str = "1h") -> Dict[str, Any]:
        """
        Get technical analysis data for a trading pair with fallback support.
        
        Args:
            symbol: Trading pair symbol (e.g. BTCUSDT)
            exchange: Exchange name
            interval: Time interval
            
        Returns:
            Dict containing technical analysis data from one or more sources
        """
        result = {
            "symbol": symbol,
            "timestamp": int(time.time()),
            "indicators": {},
            "price": {},
            "sources": []
        }
        
        # Try TradingView first (primary source)
        tradingview_data = await self.tradingview.get_analysis(symbol, exchange, "crypto", interval)
        
        if tradingview_data:
            result["sources"].append("tradingview")
            
            # Extract indicators
            indicators = tradingview_data["indicators"]
            result["indicators"] = {
                "rsi": indicators.get("rsi"),
                "macd": {
                    "value": indicators.get("macd_macd"),
                    "signal": indicators.get("macd_signal"),
                    "histogram": indicators.get("macd_macd", 0) - indicators.get("macd_signal", 0) if indicators.get("macd_macd") and indicators.get("macd_signal") else None
                },
                "ma_200": indicators.get("ma_200"),
                "ma_50": indicators.get("ma_50"),
                "bollinger_bands": {
                    "upper": indicators.get("bb_upper"),
                    "middle": indicators.get("bb_middle"),
                    "lower": indicators.get("bb_lower")
                }
            }
            
            # Extract price data
            if indicators.get("close") is not None:
                result["price"]["current"] = indicators.get("close")
            if indicators.get("high") is not None:
                result["price"]["high_24h"] = indicators.get("high")
            if indicators.get("low") is not None:
                result["price"]["low_24h"] = indicators.get("low")
            if indicators.get("volume") is not None:
                result["price"]["volume_24h"] = indicators.get("volume")
                
            # Add TradingView-specific data
            result["tradingview_summary"] = {
                "recommendation": tradingview_data.get("summary", {}).get("recommendation"),
                "buy_signals": tradingview_data.get("summary", {}).get("buy"),
                "sell_signals": tradingview_data.get("summary", {}).get("sell"),
                "neutral_signals": tradingview_data.get("summary", {}).get("neutral")
            }
        
        # If we're missing price data, try CoinGecko as a fallback
        if not result.get("price") or not result["price"].get("current"):
            # Convert symbol to CoinGecko format
            coin_id = await self.coingecko.convert_trading_pair(symbol)
            
            if coin_id:
                # Get price data
                price_data = await self.coingecko.get_price(
                    [coin_id], 
                    ["usd"], 
                    include_market_cap=True, 
                    include_24hr_vol=True, 
                    include_24hr_change=True
                )
                
                if price_data and coin_id in price_data:
                    if "coingecko" not in result["sources"]:
                        result["sources"].append("coingecko")
                        
                    coin_data = price_data[coin_id]
                    
                    # Add price data
                    if "usd" in coin_data:
                        result["price"]["current"] = coin_data["usd"]
                    if "usd_market_cap" in coin_data:
                        result["price"]["market_cap"] = coin_data["usd_market_cap"]
                    if "usd_24h_vol" in coin_data:
                        result["price"]["volume_24h"] = coin_data["usd_24h_vol"]
                    if "usd_24h_change" in coin_data:
                        result["price"]["change_24h_pct"] = coin_data["usd_24h_change"]
                        
                # Get OHLC data for high/low if missing
                if not result["price"].get("high_24h") or not result["price"].get("low_24h"):
                    ohlc_data = await self.coingecko.get_ohlc(coin_id, "usd", "1")
                    
                    if ohlc_data and len(ohlc_data) > 0:
                        # Find highest high and lowest low in the data
                        high_24h = max([candle[2] for candle in ohlc_data])  # candle[2] is high
                        low_24h = min([candle[3] for candle in ohlc_data])   # candle[3] is low
                        
                        result["price"]["high_24h"] = high_24h
                        result["price"]["low_24h"] = low_24h
        
        # If we're still missing indicators, try Alpha Vantage as a fallback
        if not result["indicators"].get("rsi") or not result["indicators"]["macd"].get("value"):
            # Convert symbol to Alpha Vantage format
            av_symbol = await self.alphavantage.convert_symbol(symbol)
            
            if av_symbol:
                # Get RSI if missing
                if not result["indicators"].get("rsi"):
                    rsi_data = await self.alphavantage.get_rsi(av_symbol, "daily", 14, "close")
                    
                    if rsi_data and "Technical Analysis: RSI" in rsi_data:
                        if "alphavantage" not in result["sources"]:
                            result["sources"].append("alphavantage")
                            
                        # Get the most recent RSI value
                        rsi_values = rsi_data["Technical Analysis: RSI"]
                        if rsi_values:
                            latest_date = sorted(rsi_values.keys())[-1]
                            result["indicators"]["rsi"] = float(rsi_values[latest_date]["RSI"])
                
                # Get MACD if missing
                if not result["indicators"]["macd"].get("value"):
                    macd_data = await self.alphavantage.get_macd(av_symbol, "daily", "close")
                    
                    if macd_data and "Technical Analysis: MACD" in macd_data:
                        if "alphavantage" not in result["sources"]:
                            result["sources"].append("alphavantage")
                            
                        # Get the most recent MACD values
                        macd_values = macd_data["Technical Analysis: MACD"]
                        if macd_values:
                            latest_date = sorted(macd_values.keys())[-1]
                            result["indicators"]["macd"]["value"] = float(macd_values[latest_date]["MACD"])
                            result["indicators"]["macd"]["signal"] = float(macd_values[latest_date]["MACD_Signal"])
                            result["indicators"]["macd"]["histogram"] = float(macd_values[latest_date]["MACD_Hist"])
                
                # Get Bollinger Bands if missing
                if not result["indicators"]["bollinger_bands"].get("upper"):
                    bbands_data = await self.alphavantage.get_bbands(av_symbol, "daily", 20, "close")
                    
                    if bbands_data and "Technical Analysis: BBANDS" in bbands_data:
                        if "alphavantage" not in result["sources"]:
                            result["sources"].append("alphavantage")
                            
                        # Get the most recent Bollinger Bands values
                        bbands_values = bbands_data["Technical Analysis: BBANDS"]
                        if bbands_values:
                            latest_date = sorted(bbands_values.keys())[-1]
                            result["indicators"]["bollinger_bands"]["upper"] = float(bbands_values[latest_date]["Real Upper Band"])
                            result["indicators"]["bollinger_bands"]["middle"] = float(bbands_values[latest_date]["Real Middle Band"])
                            result["indicators"]["bollinger_bands"]["lower"] = float(bbands_values[latest_date]["Real Lower Band"])
        
        # Log the data sources used
        self.logger.info(f"Technical analysis for {symbol} compiled from sources: {', '.join(result['sources'])}")
        
        return result
    
    async def get_market_data(self, symbols: List[str], exchange: str = "BINANCE",
                            interval: str = "1h") -> Dict[str, Dict[str, Any]]:
        """
        Get market data for multiple trading pairs.
        
        Args:
            symbols: List of trading pair symbols
            exchange: Exchange name
            interval: Time interval
            
        Returns:
            Dict mapping symbols to their market data
        """
        results = {}
        
        # Process each symbol in parallel
        tasks = [self.get_technical_analysis(symbol, exchange, interval) for symbol in symbols]
        data_list = await asyncio.gather(*tasks)
        
        # Map results to symbols
        for symbol, data in zip(symbols, data_list):
            results[symbol] = data
            
        return results