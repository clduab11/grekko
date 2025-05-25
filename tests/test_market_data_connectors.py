"""
Tests for the market data connectors and aggregator.

These tests verify that the TradingView, CoinGecko, and Alpha Vantage
connectors are working properly and that the market data aggregator
can combine data from all three sources.
"""

import pytest
import asyncio
from typing import Dict, Any

from src.data_ingestion.connectors.offchain_connectors.tradingview_connector import TradingViewConnector
from src.data_ingestion.connectors.offchain_connectors.coingecko_connector import CoinGeckoConnector
from src.data_ingestion.connectors.offchain_connectors.alphavantage_connector import AlphaVantageConnector
from src.data_ingestion.market_data_aggregator import MarketDataAggregator

# Test trading pair
TEST_PAIR = "BTCUSDT"

@pytest.mark.asyncio
async def test_tradingview_connector():
    """Test that the TradingView connector can fetch data."""
    connector = TradingViewConnector()
    analysis = await connector.get_analysis(TEST_PAIR)
    
    # Basic validation
    assert analysis is not None
    assert "indicators" in analysis
    assert "summary" in analysis
    
    # Print sample of data for manual verification
    print(f"\nTradingView data sample for {TEST_PAIR}:")
    if "indicators" in analysis:
        indicators = analysis["indicators"]
        print(f"  RSI: {indicators.get('rsi')}")
        print(f"  MACD: {indicators.get('macd_macd')}")
        print(f"  Signal: {indicators.get('macd_signal')}")
        
    if "summary" in analysis:
        summary = analysis["summary"]
        print(f"  Recommendation: {summary.get('recommendation')}")
        print(f"  Buy signals: {summary.get('buy')}")
        print(f"  Sell signals: {summary.get('sell')}")

@pytest.mark.asyncio
async def test_coingecko_connector():
    """Test that the CoinGecko connector can fetch data."""
    connector = CoinGeckoConnector()
    
    # Convert trading pair to CoinGecko format
    coin_id = await connector.convert_trading_pair(TEST_PAIR)
    assert coin_id is not None
    
    # Test price data
    price_data = await connector.get_price(
        [coin_id], 
        ["usd"], 
        include_market_cap=True, 
        include_24hr_vol=True, 
        include_24hr_change=True
    )
    
    # Basic validation
    assert price_data is not None
    assert coin_id in price_data
    
    # Print sample of data for manual verification
    print(f"\nCoinGecko data sample for {TEST_PAIR} (coin_id: {coin_id}):")
    if price_data and coin_id in price_data:
        coin_data = price_data[coin_id]
        print(f"  Price (USD): {coin_data.get('usd')}")
        print(f"  Market Cap: {coin_data.get('usd_market_cap')}")
        print(f"  24h Volume: {coin_data.get('usd_24h_vol')}")
        print(f"  24h Change: {coin_data.get('usd_24h_change')}%")

@pytest.mark.asyncio
async def test_alphavantage_connector():
    """Test that the Alpha Vantage connector can fetch data using demo key."""
    connector = AlphaVantageConnector("demo")
    
    # Convert trading pair to Alpha Vantage format
    symbol = await connector.convert_symbol(TEST_PAIR)
    assert symbol is not None
    
    # Note: With demo key, real data might not be returned, but we can test the API call
    # Test with a known symbol for demo mode
    forex_data = await connector.get_forex_rate("BTC", "USD")
    
    # Print result for manual verification
    print(f"\nAlpha Vantage API call response (demo key, may be limited):")
    if forex_data:
        if "Error Message" in forex_data:
            print(f"  Error: {forex_data['Error Message']}")
        elif "Note" in forex_data:
            print(f"  Note: {forex_data['Note']}")
        else:
            print(f"  Response: {forex_data}")
    else:
        print("  No response or error")

@pytest.mark.asyncio
async def test_market_data_aggregator():
    """Test that the market data aggregator can combine data from multiple sources."""
    # Configure aggregator with demo keys
    config = {
        "alphavantage": {
            "api_key": "demo"
        }
    }
    
    aggregator = MarketDataAggregator(config)
    
    # Fetch technical analysis
    analysis = await aggregator.get_technical_analysis(TEST_PAIR)
    
    # Basic validation
    assert analysis is not None
    assert "indicators" in analysis
    assert "price" in analysis
    assert "sources" in analysis
    
    # Print result for manual verification
    print(f"\nMarket Data Aggregator results for {TEST_PAIR}:")
    print(f"  Data sources used: {', '.join(analysis['sources'])}")
    
    if "price" in analysis:
        price = analysis["price"]
        print(f"  Current price: {price.get('current')}")
        print(f"  24h High: {price.get('high_24h')}")
        print(f"  24h Low: {price.get('low_24h')}")
        print(f"  24h Volume: {price.get('volume_24h')}")
    
    if "indicators" in analysis:
        indicators = analysis["indicators"]
        print(f"  RSI: {indicators.get('rsi')}")
        if "macd" in indicators:
            macd = indicators["macd"]
            print(f"  MACD: {macd.get('value')}")
            print(f"  MACD Signal: {macd.get('signal')}")
            print(f"  MACD Histogram: {macd.get('histogram')}")
        
        if "bollinger_bands" in indicators:
            bb = indicators["bollinger_bands"]
            print(f"  Bollinger Upper: {bb.get('upper')}")
            print(f"  Bollinger Middle: {bb.get('middle')}")
            print(f"  Bollinger Lower: {bb.get('lower')}")

if __name__ == "__main__":
    # Run tests manually
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_tradingview_connector())
    loop.run_until_complete(test_coingecko_connector())
    loop.run_until_complete(test_alphavantage_connector())
    loop.run_until_complete(test_market_data_aggregator())