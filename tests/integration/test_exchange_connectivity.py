import pytest
import ccxt.pro as ccxt
from src.data_ingestion.connectors.exchange_connectors.binance_connector import BinanceConnector
from src.data_ingestion.connectors.exchange_connectors.coinbase_connector import CoinbaseConnector

@pytest.mark.asyncio
async def test_ccxt_pro_integration():
    binance = ccxt.binance()
    coinbase = ccxt.coinbasepro()
    assert binance.has['fetchTicker']
    assert coinbase.has['fetchTicker']

@pytest.mark.asyncio
async def test_binance_triangular_arbitrage():
    binance_connector = BinanceConnector(api_key='[REDACTED]', api_secret='[REDACTED]')
    result = await binance_connector.triangular_arbitrage('BTC', 'USDT', 'ETH')
    assert result is not None

@pytest.mark.asyncio
async def test_twap_execution():
    binance_connector = BinanceConnector(api_key='[REDACTED]', api_secret='[REDACTED]')
    result = await binance_connector.twap_execution('BTC/USDT', 'limit', 'buy', 1, 50000, interval=10, slices=5)
    assert result is not None

@pytest.mark.asyncio
async def test_exchange_specific_error_handling():
    binance_connector = BinanceConnector(api_key='[REDACTED]', api_secret='[REDACTED]')
    try:
        await binance_connector.create_order('INVALID_SYMBOL', 'limit', 'buy', 1, 50000)
    except Exception as e:
        assert 'INVALID_SYMBOL' in str(e)
