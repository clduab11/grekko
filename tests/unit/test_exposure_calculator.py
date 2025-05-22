"""
Unit tests for the ExposureCalculator component.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.risk_management.exposure_calculator import ExposureCalculator


class TestExposureCalculator:
    """Test suite for ExposureCalculator"""
    
    @pytest.fixture
    def exposure_calculator(self):
        """Create an ExposureCalculator instance for testing"""
        return ExposureCalculator(
            max_asset_exposure=0.20,
            max_sector_exposure=0.40,
            max_exchange_exposure=0.70,
            max_long_exposure=1.0,
            max_short_exposure=0.50
        )
    
    def test_init(self, exposure_calculator):
        """Test initialization of ExposureCalculator"""
        assert exposure_calculator.max_asset_exposure == 0.20
        assert exposure_calculator.max_sector_exposure == 0.40
        assert exposure_calculator.max_exchange_exposure == 0.70
        assert exposure_calculator.max_long_exposure == 1.0
        assert exposure_calculator.max_short_exposure == 0.50
        assert exposure_calculator.positions == {}
    
    def test_add_position(self, exposure_calculator):
        """Test adding a position"""
        # Add a position
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0,
            sector='Cryptocurrency',
            exchange='Binance'
        )
        
        # Check that position was added correctly
        assert 'BTC/USDT' in exposure_calculator.positions
        position = exposure_calculator.positions['BTC/USDT']
        assert position['amount'] == 1.0
        assert position['price'] == 40000.0
        assert position['value'] == 40000.0
        assert position['sector'] == 'Cryptocurrency'
        assert position['exchange'] == 'Binance'
    
    def test_remove_position(self, exposure_calculator):
        """Test removing a position"""
        # Add a position
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0
        )
        
        # Remove the position
        result = exposure_calculator.remove_position('BTC/USDT')
        
        # Check that position was removed
        assert result is True
        assert 'BTC/USDT' not in exposure_calculator.positions
        
        # Try to remove a non-existent position
        result = exposure_calculator.remove_position('ETH/USDT')
        assert result is False
    
    def test_update_position(self, exposure_calculator):
        """Test updating a position"""
        # Add a position
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0
        )
        
        # Update amount only
        result = exposure_calculator.update_position(
            asset='BTC/USDT',
            amount=2.0
        )
        
        # Check that position was updated
        assert result is True
        position = exposure_calculator.positions['BTC/USDT']
        assert position['amount'] == 2.0
        assert position['price'] == 40000.0
        assert position['value'] == 80000.0
        
        # Update price only
        result = exposure_calculator.update_position(
            asset='BTC/USDT',
            price=45000.0
        )
        
        # Check that position was updated
        assert result is True
        position = exposure_calculator.positions['BTC/USDT']
        assert position['amount'] == 2.0
        assert position['price'] == 45000.0
        assert position['value'] == 90000.0
        
        # Update both amount and price
        result = exposure_calculator.update_position(
            asset='BTC/USDT',
            amount=1.5,
            price=50000.0
        )
        
        # Check that position was updated
        assert result is True
        position = exposure_calculator.positions['BTC/USDT']
        assert position['amount'] == 1.5
        assert position['price'] == 50000.0
        assert position['value'] == 75000.0
        
        # Try to update a non-existent position
        result = exposure_calculator.update_position(
            asset='ETH/USDT',
            amount=1.0,
            price=3000.0
        )
        assert result is False
    
    def test_get_total_exposure_empty(self, exposure_calculator):
        """Test getting total exposure with no positions"""
        long_exposure, short_exposure, net_exposure = exposure_calculator.get_total_exposure()
        assert long_exposure == 0.0
        assert short_exposure == 0.0
        assert net_exposure == 0.0
    
    def test_get_total_exposure_long_only(self, exposure_calculator):
        """Test getting total exposure with long positions only"""
        # Add long positions
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0
        )
        
        # Check total exposure
        long_exposure, short_exposure, net_exposure = exposure_calculator.get_total_exposure()
        assert long_exposure == 70000.0  # 40000 + 30000
        assert short_exposure == 0.0
        assert net_exposure == 70000.0
    
    def test_get_total_exposure_short_only(self, exposure_calculator):
        """Test getting total exposure with short positions only"""
        # Add short positions
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=-0.5,
            price=40000.0
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=-5.0,
            price=3000.0
        )
        
        # Check total exposure
        long_exposure, short_exposure, net_exposure = exposure_calculator.get_total_exposure()
        assert long_exposure == 0.0
        assert short_exposure == 35000.0  # 20000 + 15000
        assert net_exposure == -35000.0
    
    def test_get_total_exposure_mixed(self, exposure_calculator):
        """Test getting total exposure with both long and short positions"""
        # Add mixed positions
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=-5.0,
            price=3000.0
        )
        
        # Check total exposure
        long_exposure, short_exposure, net_exposure = exposure_calculator.get_total_exposure()
        assert long_exposure == 40000.0
        assert short_exposure == 15000.0
        assert net_exposure == 25000.0
    
    def test_get_asset_exposure_nonexistent(self, exposure_calculator):
        """Test getting exposure to a non-existent asset"""
        exposure = exposure_calculator.get_asset_exposure('BTC/USDT')
        assert exposure == 0.0
    
    def test_get_asset_exposure_empty(self, exposure_calculator):
        """Test getting asset exposure with empty portfolio"""
        # Add a position but with zero value
        exposure_calculator.positions['BTC/USDT'] = {
            'amount': 0.0,
            'price': 40000.0,
            'value': 0.0
        }
        
        exposure = exposure_calculator.get_asset_exposure('BTC/USDT')
        assert exposure == 0.0
    
    def test_get_asset_exposure(self, exposure_calculator):
        """Test getting asset exposure"""
        # Add positions
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0
        )
        
        # Check asset exposure
        btc_exposure = exposure_calculator.get_asset_exposure('BTC/USDT')
        eth_exposure = exposure_calculator.get_asset_exposure('ETH/USDT')
        
        assert btc_exposure == 40000.0 / 70000.0  # 40000 / (40000 + 30000)
        assert eth_exposure == 30000.0 / 70000.0  # 30000 / (40000 + 30000)
    
    def test_get_sector_exposure_empty(self, exposure_calculator):
        """Test getting sector exposure with no positions"""
        sector_exposure = exposure_calculator.get_sector_exposure()
        assert sector_exposure == {}
    
    def test_get_sector_exposure(self, exposure_calculator):
        """Test getting sector exposure"""
        # Add positions with sectors
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0,
            sector='Cryptocurrency'
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0,
            sector='Cryptocurrency'
        )
        exposure_calculator.add_position(
            asset='LINK/USDT',
            amount=100.0,
            price=200.0,
            sector='Oracle'
        )
        
        # Check sector exposure
        sector_exposure = exposure_calculator.get_sector_exposure()
        
        assert len(sector_exposure) == 2
        assert 'Cryptocurrency' in sector_exposure
        assert 'Oracle' in sector_exposure
        
        crypto_exposure = sector_exposure['Cryptocurrency']
        oracle_exposure = sector_exposure['Oracle']
        
        total_value = 40000.0 + 30000.0 + 20000.0
        assert crypto_exposure == (40000.0 + 30000.0) / total_value
        assert oracle_exposure == 20000.0 / total_value
    
    def test_get_exchange_exposure_empty(self, exposure_calculator):
        """Test getting exchange exposure with no positions"""
        exchange_exposure = exposure_calculator.get_exchange_exposure()
        assert exchange_exposure == {}
    
    def test_get_exchange_exposure(self, exposure_calculator):
        """Test getting exchange exposure"""
        # Add positions with exchanges
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0,
            exchange='Binance'
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0,
            exchange='Binance'
        )
        exposure_calculator.add_position(
            asset='LINK/USDT',
            amount=100.0,
            price=200.0,
            exchange='Coinbase'
        )
        
        # Check exchange exposure
        exchange_exposure = exposure_calculator.get_exchange_exposure()
        
        assert len(exchange_exposure) == 2
        assert 'Binance' in exchange_exposure
        assert 'Coinbase' in exchange_exposure
        
        binance_exposure = exchange_exposure['Binance']
        coinbase_exposure = exchange_exposure['Coinbase']
        
        total_value = 40000.0 + 30000.0 + 20000.0
        assert binance_exposure == (40000.0 + 30000.0) / total_value
        assert coinbase_exposure == 20000.0 / total_value
    
    def test_check_asset_limit_no_existing_position_no_price(self, exposure_calculator):
        """Test checking asset limit for non-existent position without price"""
        result = exposure_calculator.check_asset_limit('BTC/USDT', 1.0)
        assert result is False  # Should fail without price
    
    def test_check_asset_limit_no_existing_position(self, exposure_calculator):
        """Test checking asset limit for non-existent position"""
        # With no existing positions, a new position would be 100% of the portfolio
        # This would exceed the 20% limit
        result = exposure_calculator.check_asset_limit('BTC/USDT', 1.0, 40000.0)
        assert result is False
        
        # Add some other positions to dilute the exposure
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0
        )
        exposure_calculator.add_position(
            asset='LINK/USDT',
            amount=100.0,
            price=200.0
        )
        
        # Now check again (should be within limit)
        # BTC would be 40000 / (30000 + 20000 + 40000) = 44.4%
        # This exceeds the 20% limit
        result = exposure_calculator.check_asset_limit('BTC/USDT', 1.0, 40000.0)
        assert result is False
        
        # Try with a smaller position that would be within limit
        # BTC would be 10000 / (30000 + 20000 + 10000) = 16.7%
        result = exposure_calculator.check_asset_limit('BTC/USDT', 0.25, 40000.0)
        assert result is True
    
    def test_check_asset_limit_existing_position(self, exposure_calculator):
        """Test checking asset limit for existing position"""
        # Add positions
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=0.25,
            price=40000.0
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0
        )
        exposure_calculator.add_position(
            asset='LINK/USDT',
            amount=100.0,
            price=200.0
        )
        
        # Current BTC exposure is 10000 / (10000 + 30000 + 20000) = 16.7%
        # Adding 0.1 BTC would make it 14000 / (14000 + 30000 + 20000) = 21.9%
        # This exceeds the 20% limit
        result = exposure_calculator.check_asset_limit('BTC/USDT', 0.1)
        assert result is False
        
        # Adding 0.05 BTC would make it 12000 / (12000 + 30000 + 20000) = 19.4%
        # This is within the 20% limit
        result = exposure_calculator.check_asset_limit('BTC/USDT', 0.05)
        assert result is True
    
    def test_validate_trade(self, exposure_calculator):
        """Test validating a trade against all limits"""
        # Add some initial positions
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0,
            sector='Cryptocurrency',
            exchange='Binance'
        )
        exposure_calculator.add_position(
            asset='LINK/USDT',
            amount=100.0,
            price=200.0,
            sector='Oracle',
            exchange='Coinbase'
        )
        
        # Valid trade (within all limits)
        result = exposure_calculator.validate_trade(
            asset='BTC/USDT',
            amount=0.2,
            price=40000.0,
            sector='Cryptocurrency',
            exchange='Binance'
        )
        assert result is True
        
        # Invalid trade (exceeds asset limit)
        result = exposure_calculator.validate_trade(
            asset='BTC/USDT',
            amount=1.0,
            price=40000.0,
            sector='Cryptocurrency',
            exchange='Binance'
        )
        assert result is False
    
    def test_get_portfolio_stats_empty(self, exposure_calculator):
        """Test getting portfolio stats with no positions"""
        stats = exposure_calculator.get_portfolio_stats()
        
        assert stats['total_value'] == 0
        assert stats['long_exposure'] == 0
        assert stats['short_exposure'] == 0
        assert stats['net_exposure'] == 0
        assert stats['asset_count'] == 0
        assert stats['sector_count'] == 0
        assert stats['exchange_count'] == 0
        assert stats['highest_concentration'] == 0
        assert stats['sector_exposure'] == {}
        assert stats['exchange_exposure'] == {}
    
    def test_get_portfolio_stats(self, exposure_calculator):
        """Test getting comprehensive portfolio stats"""
        # Add some positions
        exposure_calculator.add_position(
            asset='BTC/USDT',
            amount=0.25,
            price=40000.0,
            sector='Cryptocurrency',
            exchange='Binance'
        )
        exposure_calculator.add_position(
            asset='ETH/USDT',
            amount=10.0,
            price=3000.0,
            sector='Cryptocurrency',
            exchange='Binance'
        )
        exposure_calculator.add_position(
            asset='LINK/USDT',
            amount=-100.0,
            price=200.0,
            sector='Oracle',
            exchange='Coinbase'
        )
        
        # Get portfolio stats
        stats = exposure_calculator.get_portfolio_stats()
        
        # Check basic stats
        assert stats['total_value'] == 60000.0  # 10000 + 30000 + 20000
        assert stats['long_exposure'] == 40000.0  # 10000 + 30000
        assert stats['short_exposure'] == 20000.0
        assert stats['net_exposure'] == 20000.0  # 40000 - 20000
        assert stats['asset_count'] == 3
        assert stats['sector_count'] == 2
        assert stats['exchange_count'] == 2
        
        # Check exposure percentages
        assert abs(stats['long_pct'] - 0.6667) < 0.001  # 40000 / 60000
        assert abs(stats['short_pct'] - 0.3333) < 0.001  # 20000 / 60000
        
        # Check asset exposures
        assert abs(stats['asset_exposures']['BTC/USDT'] - 0.1667) < 0.001  # 10000 / 60000
        assert abs(stats['asset_exposures']['ETH/USDT'] - 0.5) < 0.001  # 30000 / 60000
        assert abs(stats['asset_exposures']['LINK/USDT'] - 0.3333) < 0.001  # 20000 / 60000
        
        # Check highest concentration
        assert abs(stats['highest_concentration'] - 0.5) < 0.001  # ETH at 50%
        
        # Check sector exposure
        assert len(stats['sector_exposure']) == 2
        assert abs(stats['sector_exposure']['Cryptocurrency'] - 0.6667) < 0.001  # (10000 + 30000) / 60000
        assert abs(stats['sector_exposure']['Oracle'] - 0.3333) < 0.001  # 20000 / 60000
        
        # Check exchange exposure
        assert len(stats['exchange_exposure']) == 2
        assert abs(stats['exchange_exposure']['Binance'] - 0.6667) < 0.001  # (10000 + 30000) / 60000
        assert abs(stats['exchange_exposure']['Coinbase'] - 0.3333) < 0.001  # 20000 / 60000