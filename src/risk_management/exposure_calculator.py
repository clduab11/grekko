"""
Exposure calculator module for the Grekko trading system.

This module calculates various forms of exposure and concentration risks
to help ensure the trading portfolio remains within acceptable risk limits.
"""
import numpy as np
import logging
from collections import defaultdict


class ExposureCalculator:
    """
    Calculates and monitors exposures across various dimensions.
    
    This class tracks exposure by asset, sector, market cap, exchange, and more,
    providing insights into concentration risks and enforcing exposure limits.
    
    Attributes:
        max_asset_exposure (float): Maximum allowed exposure to a single asset (%)
        max_sector_exposure (float): Maximum allowed exposure to a single sector (%)
        max_exchange_exposure (float): Maximum allowed exposure to a single exchange (%)
        max_long_exposure (float): Maximum allowed total long exposure (%)
        max_short_exposure (float): Maximum allowed total short exposure (%)
        positions (dict): Current positions with exposures
        logger (logging.Logger): Logger for risk events
    """
    
    def __init__(self, 
                 max_asset_exposure=0.20,
                 max_sector_exposure=0.40,
                 max_exchange_exposure=0.70,
                 max_long_exposure=1.0,
                 max_short_exposure=0.50):
        """
        Initialize the exposure calculator.
        
        Args:
            max_asset_exposure (float): Maximum single asset exposure (default: 20%)
            max_sector_exposure (float): Maximum single sector exposure (default: 40%)
            max_exchange_exposure (float): Maximum single exchange exposure (default: 70%)
            max_long_exposure (float): Maximum total long exposure (default: 100%)
            max_short_exposure (float): Maximum total short exposure (default: 50%)
        """
        self.max_asset_exposure = max_asset_exposure
        self.max_sector_exposure = max_sector_exposure
        self.max_exchange_exposure = max_exchange_exposure
        self.max_long_exposure = max_long_exposure
        self.max_short_exposure = max_short_exposure
        
        self.positions = {}
        self.logger = logging.getLogger(__name__)
    
    def add_position(self, asset, amount, price, sector=None, exchange=None):
        """
        Add or update a position in the portfolio.
        
        Args:
            asset (str): Asset identifier (e.g., 'BTC/USDT')
            amount (float): Position size (positive for long, negative for short)
            price (float): Current asset price
            sector (str, optional): Asset sector (e.g., 'DeFi', 'Layer1')
            exchange (str, optional): Exchange where the position is held
        """
        value = amount * price
        
        self.positions[asset] = {
            'amount': amount,
            'price': price,
            'value': value,
            'sector': sector,
            'exchange': exchange
        }
    
    def remove_position(self, asset):
        """
        Remove a position from the portfolio.
        
        Args:
            asset (str): Asset identifier to remove
            
        Returns:
            bool: True if position was removed, False if not found
        """
        if asset in self.positions:
            del self.positions[asset]
            return True
        return False
    
    def update_position(self, asset, amount=None, price=None):
        """
        Update an existing position's amount or price.
        
        Args:
            asset (str): Asset identifier to update
            amount (float, optional): New position size
            price (float, optional): New asset price
            
        Returns:
            bool: True if position was updated, False if not found
        """
        if asset not in self.positions:
            return False
            
        position = self.positions[asset]
        
        if amount is not None:
            position['amount'] = amount
            
        if price is not None:
            position['price'] = price
            
        # Recalculate value
        position['value'] = position['amount'] * position['price']
        return True
    
    def get_total_exposure(self):
        """
        Calculate total portfolio exposure.
        
        Returns:
            tuple: (Total long exposure, Total short exposure, Net exposure)
        """
        long_exposure = 0.0
        short_exposure = 0.0
        
        for asset, position in self.positions.items():
            value = position['value']
            if value > 0:
                long_exposure += value
            else:
                short_exposure += abs(value)
        
        net_exposure = long_exposure - short_exposure
        return (long_exposure, short_exposure, net_exposure)
    
    def get_asset_exposure(self, asset):
        """
        Calculate exposure to a specific asset.
        
        Args:
            asset (str): Asset identifier
            
        Returns:
            float: Exposure to the asset as a percentage of total exposure
        """
        if asset not in self.positions:
            return 0.0
            
        total_exposure = sum(abs(p['value']) for p in self.positions.values())
        if total_exposure == 0:
            return 0.0
            
        return abs(self.positions[asset]['value']) / total_exposure
    
    def get_sector_exposure(self):
        """
        Calculate exposure by sector.
        
        Returns:
            dict: Sector exposures as percentages of total exposure
        """
        sector_values = defaultdict(float)
        total_exposure = 0.0
        
        for position in self.positions.values():
            value = abs(position['value'])
            sector = position.get('sector', 'Unknown')
            sector_values[sector] += value
            total_exposure += value
        
        if total_exposure == 0:
            return {}
            
        return {sector: value / total_exposure 
                for sector, value in sector_values.items()}
    
    def get_exchange_exposure(self):
        """
        Calculate exposure by exchange.
        
        Returns:
            dict: Exchange exposures as percentages of total exposure
        """
        exchange_values = defaultdict(float)
        total_exposure = 0.0
        
        for position in self.positions.values():
            value = abs(position['value'])
            exchange = position.get('exchange', 'Unknown')
            exchange_values[exchange] += value
            total_exposure += value
        
        if total_exposure == 0:
            return {}
            
        return {exchange: value / total_exposure 
                for exchange, value in exchange_values.items()}
    
    def check_asset_limit(self, asset, additional_amount=0, price=None):
        """
        Check if adding to a position would exceed asset exposure limit.
        
        Args:
            asset (str): Asset identifier
            additional_amount (float): Additional amount to add (positive or negative)
            price (float, optional): Current price (uses stored price if None)
            
        Returns:
            bool: True if within limits, False if would exceed
        """
        # Get current position data
        current_amount = 0
        current_price = price
        
        if asset in self.positions:
            current_amount = self.positions[asset]['amount']
            if price is None:
                current_price = self.positions[asset]['price']
        
        if current_price is None:
            self.logger.error(f"No price available for {asset}")
            return False
        
        # Calculate new position value
        new_amount = current_amount + additional_amount
        new_value = new_amount * current_price
        
        # Calculate total exposure with this change
        total_exposure = sum(abs(p['value']) for p in self.positions.values())
        if asset in self.positions:
            # Remove current position from total
            total_exposure -= abs(self.positions[asset]['value'])
        
        # Add new position to total
        total_exposure += abs(new_value)
        
        if total_exposure == 0:
            return True
            
        # Calculate new exposure percentage
        new_exposure = abs(new_value) / total_exposure
        
        # Check against limit
        within_limit = new_exposure <= self.max_asset_exposure
        
        if not within_limit:
            self.logger.warning(
                f"Asset exposure limit exceeded: {asset} would be {new_exposure:.2%} (limit: {self.max_asset_exposure:.2%})"
            )
            
        return within_limit
    
    def check_sector_limit(self, sector, additional_value):
        """
        Check if adding exposure would exceed sector exposure limit.
        
        Args:
            sector (str): Sector identifier
            additional_value (float): Additional exposure value (absolute)
            
        Returns:
            bool: True if within limits, False if would exceed
        """
        if sector is None:
            # Can't check unknown sector
            return True
            
        # Get current sector exposures
        sector_values = defaultdict(float)
        for position in self.positions.values():
            pos_sector = position.get('sector')
            if pos_sector:
                sector_values[pos_sector] += abs(position['value'])
        
        # Add additional value
        sector_values[sector] += additional_value
        
        # Calculate total exposure
        total_exposure = sum(sector_values.values())
        
        if total_exposure == 0:
            return True
            
        # Calculate new exposure percentage
        new_exposure = sector_values[sector] / total_exposure
        
        # Check against limit
        within_limit = new_exposure <= self.max_sector_exposure
        
        if not within_limit:
            self.logger.warning(
                f"Sector exposure limit exceeded: {sector} would be {new_exposure:.2%} (limit: {self.max_sector_exposure:.2%})"
            )
            
        return within_limit
    
    def check_exchange_limit(self, exchange, additional_value):
        """
        Check if adding exposure would exceed exchange exposure limit.
        
        Args:
            exchange (str): Exchange identifier
            additional_value (float): Additional exposure value (absolute)
            
        Returns:
            bool: True if within limits, False if would exceed
        """
        if exchange is None:
            # Can't check unknown exchange
            return True
            
        # Get current exchange exposures
        exchange_values = defaultdict(float)
        for position in self.positions.values():
            pos_exchange = position.get('exchange')
            if pos_exchange:
                exchange_values[pos_exchange] += abs(position['value'])
        
        # Add additional value
        exchange_values[exchange] += additional_value
        
        # Calculate total exposure
        total_exposure = sum(exchange_values.values())
        
        if total_exposure == 0:
            return True
            
        # Calculate new exposure percentage
        new_exposure = exchange_values[exchange] / total_exposure
        
        # Check against limit
        within_limit = new_exposure <= self.max_exchange_exposure
        
        if not within_limit:
            self.logger.warning(
                f"Exchange exposure limit exceeded: {exchange} would be {new_exposure:.2%} (limit: {self.max_exchange_exposure:.2%})"
            )
            
        return within_limit
    
    def check_long_short_limit(self, additional_value):
        """
        Check if adding exposure would exceed long/short exposure limits.
        
        Args:
            additional_value (float): Additional exposure value (positive for long, negative for short)
            
        Returns:
            bool: True if within limits, False if would exceed
        """
        # Get current exposures
        long_exposure, short_exposure, _ = self.get_total_exposure()
        
        # Adjust based on additional value
        if additional_value > 0:
            new_long_exposure = long_exposure + additional_value
            new_short_exposure = short_exposure
        else:
            new_long_exposure = long_exposure
            new_short_exposure = short_exposure + abs(additional_value)
        
        # Calculate total portfolio value (for percentage calculation)
        total_value = new_long_exposure + new_short_exposure
        
        if total_value == 0:
            return True
            
        # Calculate exposure percentages
        long_pct = new_long_exposure / total_value
        short_pct = new_short_exposure / total_value
        
        # Check against limits
        long_within_limit = long_pct <= self.max_long_exposure
        short_within_limit = short_pct <= self.max_short_exposure
        
        if not long_within_limit:
            self.logger.warning(
                f"Long exposure limit exceeded: would be {long_pct:.2%} (limit: {self.max_long_exposure:.2%})"
            )
            
        if not short_within_limit:
            self.logger.warning(
                f"Short exposure limit exceeded: would be {short_pct:.2%} (limit: {self.max_short_exposure:.2%})"
            )
            
        return long_within_limit and short_within_limit
    
    def validate_trade(self, asset, amount, price, sector=None, exchange=None):
        """
        Validate a proposed trade against all exposure limits.
        
        Args:
            asset (str): Asset identifier
            amount (float): Amount to trade (positive for buy, negative for sell)
            price (float): Current asset price
            sector (str, optional): Asset sector
            exchange (str, optional): Exchange for the trade
            
        Returns:
            bool: True if trade is within all limits, False otherwise
        """
        # Value of the trade
        trade_value = amount * price
        absolute_value = abs(trade_value)
        
        # Check if trade exceeds any limits
        asset_ok = self.check_asset_limit(asset, amount, price)
        sector_ok = self.check_sector_limit(sector, absolute_value)
        exchange_ok = self.check_exchange_limit(exchange, absolute_value)
        exposure_ok = self.check_long_short_limit(trade_value)
        
        # All checks must pass
        return asset_ok and sector_ok and exchange_ok and exposure_ok
    
    def get_portfolio_stats(self):
        """
        Get comprehensive portfolio exposure statistics.
        
        Returns:
            dict: Portfolio statistics including total exposure, 
                  concentrations, diversification metrics, etc.
        """
        if not self.positions:
            return {
                'total_value': 0,
                'long_exposure': 0,
                'short_exposure': 0,
                'net_exposure': 0,
                'asset_count': 0,
                'sector_count': 0,
                'exchange_count': 0,
                'highest_concentration': 0,
                'sector_exposure': {},
                'exchange_exposure': {},
            }
        
        # Get total exposures
        long_exposure, short_exposure, net_exposure = self.get_total_exposure()
        total_value = long_exposure + short_exposure
        
        # Get asset exposures
        asset_exposures = {
            asset: abs(position['value']) / total_value
            for asset, position in self.positions.items()
        } if total_value > 0 else {}
        
        # Get sector and exchange exposures
        sector_exposure = self.get_sector_exposure()
        exchange_exposure = self.get_exchange_exposure()
        
        # Calculate highest concentration
        highest_concentration = max(asset_exposures.values()) if asset_exposures else 0
        
        # Count unique sectors and exchanges
        sectors = set(position.get('sector') for position in self.positions.values() if position.get('sector'))
        exchanges = set(position.get('exchange') for position in self.positions.values() if position.get('exchange'))
        
        return {
            'total_value': total_value,
            'long_exposure': long_exposure,
            'short_exposure': short_exposure,
            'net_exposure': net_exposure,
            'long_pct': long_exposure / total_value if total_value > 0 else 0,
            'short_pct': short_exposure / total_value if total_value > 0 else 0,
            'asset_count': len(self.positions),
            'sector_count': len(sectors),
            'exchange_count': len(exchanges),
            'highest_concentration': highest_concentration,
            'asset_exposures': asset_exposures,
            'sector_exposure': sector_exposure,
            'exchange_exposure': exchange_exposure,
        }