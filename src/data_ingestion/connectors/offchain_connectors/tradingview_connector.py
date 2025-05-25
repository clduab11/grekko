"""
TradingView Connector for Grekko

- Provides integration with TradingView's Technical Analysis data
- Uses tradingview-ta library to fetch indicators and technical analysis
- Includes error handling and logging
"""

import asyncio
from typing import Dict, Any, Optional, List
import tradingview_ta as tv
from tradingview_ta import TA_Handler, Interval, Exchange

from ....utils.logger import get_logger

logger = get_logger("tradingview_connector")

class TradingViewConnector:
    """
    Connector for TradingView technical analysis data.
    Uses tradingview-ta library to fetch indicators and technical analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TradingView connector.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logger
        self.logger.info("TradingView connector initialized")
        
        # Default intervals mapping
        self.intervals = {
            "1m": Interval.INTERVAL_1_MINUTE,
            "5m": Interval.INTERVAL_5_MINUTES,
            "15m": Interval.INTERVAL_15_MINUTES,
            "30m": Interval.INTERVAL_30_MINUTES,
            "1h": Interval.INTERVAL_1_HOUR,
            "2h": Interval.INTERVAL_2_HOURS,
            "4h": Interval.INTERVAL_4_HOURS,
            "1d": Interval.INTERVAL_1_DAY,
            "1W": Interval.INTERVAL_1_WEEK,
            "1M": Interval.INTERVAL_1_MONTH
        }
    
    async def get_analysis(self, symbol: str, exchange: str = "BINANCE", 
                         screener: str = "crypto", interval: str = "1h") -> Optional[Dict[str, Any]]:
        """
        Get technical analysis data for a specific symbol.
        
        Args:
            symbol: Trading pair symbol (e.g. BTCUSDT)
            exchange: Exchange name (e.g. BINANCE)
            screener: Screener to use (crypto, forex, etc.)
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1W, 1M)
            
        Returns:
            Dict containing technical analysis data or None if error
        """
        try:
            # Convert interval string to tradingview-ta Interval enum
            tv_interval = self.intervals.get(interval, Interval.INTERVAL_1_HOUR)
            
            # Handle the symbol format (some exchanges use different formats)
            if exchange.upper() == "BINANCE":
                if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
                    if "USD" in symbol:
                        # Leave as is for pairs like BTC/USD
                        pass
                    else:
                        # Assume it's a crypto pair and add USDT
                        symbol = f"{symbol}USDT"
            
            # Initialize TA Handler
            handler = TA_Handler(
                symbol=symbol,
                exchange=exchange,
                screener=screener,
                interval=tv_interval,
                timeout=10
            )
            
            # This is a CPU-bound operation, run in a thread pool
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(None, handler.get_analysis)
            
            # Extract and format the data
            result = self._format_analysis(analysis, symbol)
            self.logger.info(f"Successfully fetched analysis for {symbol} on {exchange}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching analysis for {symbol}: {str(e)}")
            return None
    
    async def get_multiple_analysis(self, symbols: List[str], exchange: str = "BINANCE", 
                                  screener: str = "crypto", interval: str = "1h") -> Dict[str, Any]:
        """
        Get technical analysis for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            exchange: Exchange name 
            screener: Screener to use
            interval: Time interval
            
        Returns:
            Dict containing technical analysis data for each symbol
        """
        results = {}
        
        # Process each symbol and collect results
        for symbol in symbols:
            analysis = await self.get_analysis(symbol, exchange, screener, interval)
            if analysis:
                results[symbol] = analysis
        
        return results
    
    def _format_analysis(self, analysis, symbol: str) -> Dict[str, Any]:
        """
        Format the analysis data into a standardized structure.
        
        Args:
            analysis: Analysis object from tradingview-ta
            symbol: Symbol being analyzed
            
        Returns:
            Dict with formatted analysis data
        """
        # Extract indicators
        indicators = analysis.indicators
        
        # Extract oscillators and moving averages summaries
        oscillators = analysis.oscillators
        moving_averages = analysis.moving_averages
        
        # Format the response
        return {
            "symbol": symbol,
            "exchange": analysis.exchange,
            "interval": analysis.interval,
            "time": analysis.time,
            "summary": {
                "recommendation": analysis.summary["RECOMMENDATION"],
                "buy": analysis.summary["BUY"],
                "sell": analysis.summary["SELL"],
                "neutral": analysis.summary["NEUTRAL"]
            },
            "oscillators": {
                "recommendation": oscillators["RECOMMENDATION"],
                "buy": oscillators["BUY"],
                "sell": oscillators["SELL"],
                "neutral": oscillators["NEUTRAL"]
            },
            "moving_averages": {
                "recommendation": moving_averages["RECOMMENDATION"],
                "buy": moving_averages["BUY"],
                "sell": moving_averages["SELL"],
                "neutral": moving_averages["NEUTRAL"]
            },
            "indicators": {
                # Price data
                "close": indicators.get("close", None),
                "open": indicators.get("open", None),
                "high": indicators.get("high", None),
                "low": indicators.get("low", None),
                
                # Volume
                "volume": indicators.get("volume", None),
                
                # Trend indicators
                "rsi": indicators.get("RSI", None),
                "rsi[1]": indicators.get("RSI[1]", None),
                "stoch_k": indicators.get("Stoch.K", None),
                "stoch_d": indicators.get("Stoch.D", None),
                "cci": indicators.get("CCI", None),
                "adx": indicators.get("ADX", None),
                "macd_macd": indicators.get("MACD.macd", None),
                "macd_signal": indicators.get("MACD.signal", None),
                
                # Moving Averages
                "ma_20": indicators.get("SMA20", None),
                "ma_50": indicators.get("SMA50", None),
                "ma_100": indicators.get("SMA100", None),
                "ma_200": indicators.get("SMA200", None),
                "ema_20": indicators.get("EMA20", None),
                "ema_50": indicators.get("EMA50", None),
                
                # Bollinger Bands
                "bb_upper": indicators.get("BB.upper", None),
                "bb_lower": indicators.get("BB.lower", None),
                "bb_middle": indicators.get("BB.middle", None),
                
                # Additional indicators
                "psar": indicators.get("P.SAR", None),
                "vwma": indicators.get("VWMA", None),
                "mom": indicators.get("MOM", None)
            }
        }