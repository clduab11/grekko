"""
Unit tests for the BinanceConnector component.
"""
import pytest
import ccxt
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from src.data_ingestion.connectors.exchange_connectors.binance_connector import BinanceConnector


class TestBinanceConnector:
    """Test suite for BinanceConnector"""
    
    @pytest.fixture
    def mock_ccxt(self):
        """Create a mock CCXT Binance exchange"""
        with patch('src.data_ingestion.connectors.exchange_connectors.binance_connector.ccxt') as mock_ccxt:
            # Create a mock exchange instance
            mock_exchange = AsyncMock()
            mock_ccxt.binance.return_value = mock_exchange
            
            # Configure mock responses
            mock_exchange.fetch_ticker.return_value = {
                'symbol': 'BTC/USDT',
                'last': 50000.0,
                'bid': 49900.0,
                'ask': 50100.0,
                'volume': 1000.0,
                'timestamp': 1630000000000
            }
            
            mock_exchange.fetch_order_book.return_value = {
                'symbol': 'BTC/USDT',
                'bids': [[49900.0, 1.0], [49800.0, 2.0]],
                'asks': [[50100.0, 1.0], [50200.0, 2.0]],
                'timestamp': 1630000000000
            }
            
            mock_exchange.create_order.return_value = {
                'id': '12345',
                'symbol': 'BTC/USDT',
                'type': 'limit',
                'side': 'buy',
                'price': 50000.0,
                'amount': 1.0,
                'status': 'open'
            }
            
            mock_exchange.cancel_order.return_value = {
                'id': '12345',
                'status': 'canceled'
            }
            
            mock_exchange.fetch_balance.return_value = {
                'BTC': {'free': 1.0, 'used': 0.5, 'total': 1.5},
                'USDT': {'free': 50000.0, 'used': 25000.0, 'total': 75000.0}
            }
            
            mock_exchange.fetch_ohlcv.return_value = [
                [1630000000000, 50000.0, 51000.0, 49000.0, 50500.0, 1000.0],
                [1630001000000, 50500.0, 52000.0, 50000.0, 51000.0, 1200.0]
            ]
            
            mock_exchange.load_markets.return_value = {
                'BTC/USDT': {
                    'symbol': 'BTC/USDT',
                    'base': 'BTC',
                    'quote': 'USDT',
                    'active': True
                },
                'ETH/USDT': {
                    'symbol': 'ETH/USDT',
                    'base': 'ETH',
                    'quote': 'USDT',
                    'active': True
                }
            }
            
            mock_exchange.fetch_open_orders.return_value = [
                {
                    'id': '12345',
                    'symbol': 'BTC/USDT',
                    'type': 'limit',
                    'side': 'buy',
                    'price': 50000.0,
                    'amount': 1.0,
                    'status': 'open'
                }
            ]
            
            yield mock_ccxt
    
    @pytest.fixture
    def binance_connector(self, mock_ccxt):
        """Create a BinanceConnector instance with mocked dependencies"""
        return BinanceConnector(api_key='test_api_key', api_secret='test_api_secret')
    
    @pytest.mark.asyncio
    async def test_init(self, binance_connector, mock_ccxt):
        """Test initialization of BinanceConnector"""
        assert binance_connector.api_key == 'test_api_key'
        assert binance_connector.api_secret == 'test_api_secret'
        
        # Check that ccxt.binance was called with the correct parameters
        mock_ccxt.binance.assert_called_once_with({
            'apiKey': 'test_api_key',
            'secret': 'test_api_secret',
            'enableRateLimit': True
        })
    
    @pytest.mark.asyncio
    async def test_init_with_testnet(self, mock_ccxt):
        """Test initialization with testnet option"""
        connector = BinanceConnector(
            api_key='test_api_key',
            api_secret='test_api_secret',
            testnet=True
        )
        
        # Check that ccxt.binance was called with the test parameter
        mock_ccxt.binance.assert_called_once_with({
            'apiKey': 'test_api_key',
            'secret': 'test_api_secret',
            'enableRateLimit': True,
            'test': True
        })
    
    @pytest.mark.asyncio
    async def test_fetch_ticker(self, binance_connector):
        """Test fetching ticker data"""
        ticker = await binance_connector.fetch_ticker('BTC/USDT')
        
        assert ticker is not None
        assert ticker['symbol'] == 'BTC/USDT'
        assert ticker['last'] == 50000.0
        assert ticker['bid'] == 49900.0
        assert ticker['ask'] == 50100.0
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.fetch_ticker.assert_called_once_with('BTC/USDT')
    
    @pytest.mark.asyncio
    async def test_fetch_ticker_network_error(self, binance_connector):
        """Test handling of network error when fetching ticker"""
        binance_connector.exchange.fetch_ticker.side_effect = ccxt.NetworkError("Network error")
        
        ticker = await binance_connector.fetch_ticker('BTC/USDT')
        
        assert ticker is None
        binance_connector.exchange.fetch_ticker.assert_called_once_with('BTC/USDT')
    
    @pytest.mark.asyncio
    async def test_fetch_ticker_exchange_error(self, binance_connector):
        """Test handling of exchange error when fetching ticker"""
        binance_connector.exchange.fetch_ticker.side_effect = ccxt.ExchangeError("Exchange error")
        
        ticker = await binance_connector.fetch_ticker('BTC/USDT')
        
        assert ticker is None
        binance_connector.exchange.fetch_ticker.assert_called_once_with('BTC/USDT')
    
    @pytest.mark.asyncio
    async def test_fetch_order_book(self, binance_connector):
        """Test fetching order book"""
        order_book = await binance_connector.fetch_order_book('BTC/USDT', 20)
        
        assert order_book is not None
        assert order_book['symbol'] == 'BTC/USDT'
        assert len(order_book['bids']) == 2
        assert len(order_book['asks']) == 2
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.fetch_order_book.assert_called_once_with('BTC/USDT', 20)
    
    @pytest.mark.asyncio
    async def test_create_order(self, binance_connector):
        """Test creating an order"""
        order = await binance_connector.create_order(
            symbol='BTC/USDT',
            order_type='limit',
            side='buy',
            amount=1.0,
            price=50000.0
        )
        
        assert order is not None
        assert order['id'] == '12345'
        assert order['symbol'] == 'BTC/USDT'
        assert order['type'] == 'limit'
        assert order['side'] == 'buy'
        assert order['price'] == 50000.0
        assert order['amount'] == 1.0
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.create_order.assert_called_once_with(
            'BTC/USDT', 'limit', 'buy', 1.0, 50000.0
        )
    
    @pytest.mark.asyncio
    async def test_create_order_with_retries(self, binance_connector):
        """Test order creation with retries on network error"""
        # First call raises an error, second call succeeds
        binance_connector.exchange.create_order.side_effect = [
            ccxt.NetworkError("Network error"),
            {
                'id': '12345',
                'symbol': 'BTC/USDT',
                'type': 'limit',
                'side': 'buy',
                'price': 50000.0,
                'amount': 1.0,
                'status': 'open'
            }
        ]
        
        # Mock asyncio.sleep to avoid waiting
        with patch('asyncio.sleep', AsyncMock()):
            order = await binance_connector.create_order(
                symbol='BTC/USDT',
                order_type='limit',
                side='buy',
                amount=1.0,
                price=50000.0
            )
        
        assert order is not None
        assert order['id'] == '12345'
        
        # Check that the exchange method was called twice
        assert binance_connector.exchange.create_order.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, binance_connector):
        """Test cancelling an order"""
        result = await binance_connector.cancel_order(
            order_id='12345',
            symbol='BTC/USDT'
        )
        
        assert result is not None
        assert result['id'] == '12345'
        assert result['status'] == 'canceled'
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.cancel_order.assert_called_once_with(
            '12345', 'BTC/USDT'
        )
    
    @pytest.mark.asyncio
    async def test_fetch_balance(self, binance_connector):
        """Test fetching account balance"""
        balance = await binance_connector.fetch_balance()
        
        assert balance is not None
        assert balance['BTC']['free'] == 1.0
        assert balance['BTC']['used'] == 0.5
        assert balance['BTC']['total'] == 1.5
        assert balance['USDT']['free'] == 50000.0
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.fetch_balance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv(self, binance_connector):
        """Test fetching OHLCV data"""
        ohlcv = await binance_connector.fetch_ohlcv(
            symbol='BTC/USDT',
            timeframe='1h',
            since=1630000000000,
            limit=10
        )
        
        assert ohlcv is not None
        assert len(ohlcv) == 2
        assert ohlcv[0][0] == 1630000000000  # timestamp
        assert ohlcv[0][1] == 50000.0        # open
        assert ohlcv[0][2] == 51000.0        # high
        assert ohlcv[0][3] == 49000.0        # low
        assert ohlcv[0][4] == 50500.0        # close
        assert ohlcv[0][5] == 1000.0         # volume
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.fetch_ohlcv.assert_called_once_with(
            'BTC/USDT', '1h', 1630000000000, 10
        )
    
    @pytest.mark.asyncio
    async def test_triangular_arbitrage(self, binance_connector):
        """Test triangular arbitrage detection"""
        # Set up return values for the three ticker calls
        binance_connector.exchange.fetch_ticker.side_effect = [
            # BTC/USDT - 1 BTC = 50000 USDT
            {'symbol': 'BTC/USDT', 'last': 50000.0},
            # ETH/BTC - 1 ETH = 0.075 BTC
            {'symbol': 'ETH/BTC', 'last': 0.075},
            # ETH/USDT - 1 ETH = 3900 USDT
            {'symbol': 'ETH/USDT', 'last': 3900.0}
        ]
        
        # This scenario creates an arbitrage opportunity:
        # 1. Convert 1 USDT -> 0.00002 BTC (1/50000)
        # 2. Convert 0.00002 BTC -> 0.000266666 ETH (0.00002/0.075)
        # 3. Convert 0.000266666 ETH -> 1.04 USDT (0.000266666*3900)
        # Profit: 4% (1.04 - 1.00)
        
        result = await binance_connector.triangular_arbitrage(
            base_symbol='BTC',
            quote_symbol='USDT',
            arbitrage_symbol='ETH'
        )
        
        assert result is not None
        assert result['profitable'] is True
        assert abs(result['profit_percentage'] - 4.0) < 0.1  # About 4% profit
        
        # Check that the exchange methods were called correctly
        assert binance_connector.exchange.fetch_ticker.call_count == 3
    
    @pytest.mark.asyncio
    async def test_triangular_arbitrage_no_opportunity(self, binance_connector):
        """Test triangular arbitrage with no profitable opportunity"""
        # Set up return values for the three ticker calls
        binance_connector.exchange.fetch_ticker.side_effect = [
            # BTC/USDT - 1 BTC = 50000 USDT
            {'symbol': 'BTC/USDT', 'last': 50000.0},
            # ETH/BTC - 1 ETH = 0.075 BTC
            {'symbol': 'ETH/BTC', 'last': 0.075},
            # ETH/USDT - 1 ETH = 3700 USDT (no profit opportunity)
            {'symbol': 'ETH/USDT', 'last': 3700.0}
        ]
        
        result = await binance_connector.triangular_arbitrage(
            base_symbol='BTC',
            quote_symbol='USDT',
            arbitrage_symbol='ETH'
        )
        
        assert result is not None
        assert result['profitable'] is False
        assert result['profit_percentage'] < 1.0  # Less than 1% profit threshold
    
    @pytest.mark.asyncio
    async def test_twap_execution(self, binance_connector):
        """Test TWAP order execution"""
        # Mock asyncio.sleep to avoid waiting
        with patch('asyncio.sleep', AsyncMock()):
            orders = await binance_connector.twap_execution(
                symbol='BTC/USDT',
                order_type='limit',
                side='buy',
                amount=1.0,
                price=50000.0,
                interval=1,
                slices=5
            )
        
        assert orders is not None
        assert len(orders) == 5
        assert orders[0]['id'] == '12345'
        
        # Check that create_order was called 5 times
        assert binance_connector.exchange.create_order.call_count == 5
        
        # Check that each call was for 0.2 BTC (1.0 / 5 slices)
        for call in binance_connector.exchange.create_order.call_args_list:
            args, kwargs = call
            assert args[0] == 'BTC/USDT'
            assert args[1] == 'limit'
            assert args[2] == 'buy'
            assert args[3] == 0.2  # 1.0 / 5
            assert args[4] == 50000.0
    
    @pytest.mark.asyncio
    async def test_twap_execution_without_price(self, binance_connector):
        """Test TWAP execution with price determined from market"""
        # Mock asyncio.sleep to avoid waiting
        with patch('asyncio.sleep', AsyncMock()):
            orders = await binance_connector.twap_execution(
                symbol='BTC/USDT',
                order_type='limit',
                side='buy',
                amount=1.0,
                price=None,  # No price provided, should fetch from market
                interval=1,
                slices=5
            )
        
        assert orders is not None
        assert len(orders) == 5
        
        # Check that fetch_ticker was called 5 times (once per slice)
        assert binance_connector.exchange.fetch_ticker.call_count == 5
        
        # Check that create_order was called with the ask price for buy orders
        for call in binance_connector.exchange.create_order.call_args_list:
            args, kwargs = call
            assert args[0] == 'BTC/USDT'
            assert args[1] == 'limit'
            assert args[2] == 'buy'
            assert args[3] == 0.2  # 1.0 / 5
            assert args[4] == 50100.0  # Ask price from mock ticker
    
    @pytest.mark.asyncio
    async def test_get_exchange_info(self, binance_connector):
        """Test getting exchange information"""
        exchange_info = await binance_connector.get_exchange_info()
        
        assert exchange_info is not None
        assert 'BTC/USDT' in exchange_info
        assert 'ETH/USDT' in exchange_info
        assert exchange_info['BTC/USDT']['base'] == 'BTC'
        assert exchange_info['BTC/USDT']['quote'] == 'USDT'
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.load_markets.assert_called_once_with(reload=True)
    
    @pytest.mark.asyncio
    async def test_fetch_open_orders(self, binance_connector):
        """Test fetching open orders"""
        open_orders = await binance_connector.fetch_open_orders('BTC/USDT')
        
        assert open_orders is not None
        assert len(open_orders) == 1
        assert open_orders[0]['id'] == '12345'
        assert open_orders[0]['symbol'] == 'BTC/USDT'
        
        # Check that the exchange method was called correctly
        binance_connector.exchange.fetch_open_orders.assert_called_once_with('BTC/USDT')