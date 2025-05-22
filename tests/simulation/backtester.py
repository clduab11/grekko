"""
Backtesting framework for evaluating trading strategies.

The Backtester class allows testing trading strategies against historical data
to evaluate their performance under different market conditions.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt


class Backtester:
    """
    Backtester for evaluating trading strategies.
    
    Attributes:
        data (pd.DataFrame): Historical market data with OHLCV columns
        initial_capital (float): Starting capital for backtesting
        current_capital (float): Current capital during backtesting
        current_position (float): Current position size (positive for long, negative for short)
        current_position_value (float): Value of current position
        trades (list): List of executed trades
        portfolio_value (pd.Series): Portfolio value over time
        trading_fee (float): Trading fee as a percentage (0.001 = 0.1%)
    """
    
    def __init__(self, data, initial_capital=100000.0, trading_fee=0.001):
        """
        Initialize the backtester.
        
        Args:
            data (pd.DataFrame): Historical market data with OHLCV columns
            initial_capital (float): Starting capital for backtesting
            trading_fee (float): Trading fee as a percentage (0.001 = 0.1%)
        """
        self.data = data
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.current_position = 0.0
        self.current_position_value = 0.0
        self.trades = []
        self.portfolio_value = pd.Series()
        self.trading_fee = trading_fee
    
    def run(self, strategy, risk_manager=None, position_size_pct=0.1, 
            use_stop_loss=False, stop_loss_pct=0.05, take_profit_pct=0.15):
        """
        Run the backtest.
        
        Args:
            strategy: The trading strategy to test
            risk_manager: Risk manager to apply to trades (optional)
            position_size_pct (float): Position size as percentage of capital
            use_stop_loss (bool): Whether to use stop loss
            stop_loss_pct (float): Stop loss percentage
            take_profit_pct (float): Take profit percentage
            
        Returns:
            dict: Backtest results including trades, portfolio value, and metrics
        """
        # Reset state for new backtest
        self.current_capital = self.initial_capital
        self.current_position = 0.0
        self.current_position_value = 0.0
        self.trades = []
        self.portfolio_value = pd.Series(index=self.data.index)
        
        # Initialize with buy price at open
        current_price = self.data['open'].iloc[0]
        entry_price = 0.0
        
        # Prepare return series for strategy
        self.data['returns'] = self.data['close'].pct_change()
        
        # Track portfolio value
        portfolio_values = []
        
        # Run the backtest
        for i, (date, row) in enumerate(self.data.iterrows()):
            # Current market data
            current_price = row['close']
            
            # Update position value
            self.current_position_value = self.current_position * current_price
            
            # Calculate portfolio value
            portfolio_value = self.current_capital + self.current_position_value
            self.portfolio_value[date] = portfolio_value
            portfolio_values.append(portfolio_value)
            
            # Check stop loss and take profit
            if self.current_position > 0 and use_stop_loss:
                # Check stop loss (long position)
                if current_price <= entry_price * (1 - stop_loss_pct):
                    self._execute_trade(date, 'sell', current_price, self.current_position, 'Stop Loss')
                    entry_price = 0.0
                
                # Check take profit (long position)
                elif current_price >= entry_price * (1 + take_profit_pct):
                    self._execute_trade(date, 'sell', current_price, self.current_position, 'Take Profit')
                    entry_price = 0.0
            
            elif self.current_position < 0 and use_stop_loss:
                # Check stop loss (short position)
                if current_price >= entry_price * (1 + stop_loss_pct):
                    self._execute_trade(date, 'buy', current_price, abs(self.current_position), 'Stop Loss')
                    entry_price = 0.0
                
                # Check take profit (short position)
                elif current_price <= entry_price * (1 - take_profit_pct):
                    self._execute_trade(date, 'buy', current_price, abs(self.current_position), 'Take Profit')
                    entry_price = 0.0
            
            # Skip first few days until we have enough data for the strategy
            if i < strategy.lookback_period:
                continue
            
            # Get strategy signal
            lookback_data = self.data.iloc[i-strategy.lookback_period:i+1]
            signal = strategy.generate_signal(lookback_data)
            
            # Calculate position size
            position_size = (self.current_capital * position_size_pct) / current_price
            if risk_manager:
                # Apply risk management
                risk_adjusted_capital = risk_manager.enforce_risk_limits(
                    self.current_capital * position_size_pct)
                position_size = risk_adjusted_capital / current_price
            
            # Execute trades based on signal
            if signal == 'buy' and self.current_position <= 0:
                if self.current_position < 0:
                    # Close short position
                    self._execute_trade(date, 'buy', current_price, abs(self.current_position), 'Close Short')
                
                # Open long position
                self._execute_trade(date, 'buy', current_price, position_size, 'New Long')
                entry_price = current_price
                
            elif signal == 'sell' and self.current_position >= 0:
                if self.current_position > 0:
                    # Close long position
                    self._execute_trade(date, 'sell', current_price, self.current_position, 'Close Long')
                
                # Open short position
                self._execute_trade(date, 'sell', current_price, position_size, 'New Short')
                entry_price = current_price
        
        # Close any remaining position at the end
        if self.current_position != 0:
            last_date = self.data.index[-1]
            last_price = self.data['close'].iloc[-1]
            trade_type = 'sell' if self.current_position > 0 else 'buy'
            position_size = abs(self.current_position)
            self._execute_trade(last_date, trade_type, last_price, position_size, 'Close Final')
        
        # Calculate performance metrics
        metrics = self._calculate_metrics()
        
        # Return results
        return {
            'trades': self.trades,
            'portfolio_value': self.portfolio_value,
            'performance_metrics': metrics
        }
    
    def _execute_trade(self, date, trade_type, price, size, reason=''):
        """
        Execute a trade in the backtest.
        
        Args:
            date (datetime): Trade date
            trade_type (str): 'buy' or 'sell'
            price (float): Trade price
            size (float): Trade size
            reason (str): Reason for the trade
        """
        # Calculate trade value and fee
        trade_value = price * size
        fee = trade_value * self.trading_fee
        
        if trade_type == 'buy':
            # Buying - deduct capital
            self.current_capital -= (trade_value + fee)
            self.current_position += size
        else:  # sell
            # Selling - add to capital
            self.current_capital += (trade_value - fee)
            self.current_position -= size
        
        # Record the trade
        self.trades.append({
            'date': date,
            'type': trade_type,
            'price': price,
            'size': size,
            'value': trade_value,
            'fee': fee,
            'reason': reason
        })
    
    def _calculate_metrics(self):
        """
        Calculate performance metrics for the backtest.
        
        Returns:
            dict: Performance metrics
        """
        # Get portfolio values
        portfolio_values = self.portfolio_value.dropna()
        
        if len(portfolio_values) < 2:
            return {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0
            }
        
        # Calculate returns
        returns = portfolio_values.pct_change().dropna()
        
        # Calculate total return
        total_return = (portfolio_values.iloc[-1] - portfolio_values.iloc[0]) / portfolio_values.iloc[0]
        
        # Calculate annualized return
        days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
        annualized_return = (1 + total_return) ** (365 / max(days, 1)) - 1
        
        # Calculate Sharpe ratio (assume 0% risk-free rate)
        sharpe_ratio = 0.0
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5)  # Annualized
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdowns = (cumulative_returns / running_max) - 1
        max_drawdown = abs(drawdowns.min()) if len(drawdowns) > 0 else 0.0
        
        # Calculate win rate
        winners = 0
        losers = 0
        
        # Track trades to calculate P&L
        buy_trades = {}
        for trade in self.trades:
            if trade['type'] == 'buy':
                # Buying - record the trade
                key = f"{trade['date']}_{trade['price']}"
                buy_trades[key] = trade
            else:  # sell
                # Find the matching buy trade if this is a sell
                for buy_key, buy_trade in list(buy_trades.items()):
                    # Match the size (approximately)
                    if abs(buy_trade['size'] - trade['size']) < 1e-6:
                        # Calculate profit/loss
                        buy_price = buy_trade['price']
                        sell_price = trade['price']
                        profit = (sell_price - buy_price) * trade['size'] - buy_trade['fee'] - trade['fee']
                        
                        if profit > 0:
                            winners += 1
                        else:
                            losers += 1
                        
                        # Remove the buy trade
                        buy_trades.pop(buy_key)
                        break
        
        # Calculate win rate
        total_trades = winners + losers
        win_rate = winners / total_trades if total_trades > 0 else 0.0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades
        }
    
    def plot_results(self, results=None):
        """
        Plot backtest results.
        
        Args:
            results (dict): Results from the backtest run
        """
        if results is None:
            # Use the current state
            portfolio_values = self.portfolio_value
            trades = self.trades
        else:
            portfolio_values = results['portfolio_value']
            trades = results['trades']
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Plot portfolio value
        plt.subplot(2, 1, 1)
        plt.plot(portfolio_values.index, portfolio_values.values)
        plt.title('Portfolio Value Over Time')
        plt.xlabel('Date')
        plt.ylabel('Value ($)')
        plt.grid(True)
        
        # Mark buy and sell points on the chart
        buy_dates = [trade['date'] for trade in trades if trade['type'] == 'buy']
        buy_values = [portfolio_values.loc[date] if date in portfolio_values.index else None for date in buy_dates]
        buy_values = [val for val in buy_values if val is not None]
        
        sell_dates = [trade['date'] for trade in trades if trade['type'] == 'sell']
        sell_values = [portfolio_values.loc[date] if date in portfolio_values.index else None for date in sell_dates]
        sell_values = [val for val in sell_values if val is not None]
        
        if buy_dates and buy_values:
            plt.scatter(buy_dates[:len(buy_values)], buy_values, color='green', marker='^', label='Buy')
        if sell_dates and sell_values:
            plt.scatter(sell_dates[:len(sell_values)], sell_values, color='red', marker='v', label='Sell')
        
        plt.legend()
        
        # Plot trades
        plt.subplot(2, 1, 2)
        trade_dates = [trade['date'] for trade in trades]
        trade_prices = [trade['price'] for trade in trades]
        trade_types = [trade['type'] for trade in trades]
        
        # Get price data from original data
        plt.plot(self.data.index, self.data['close'], label='Price', alpha=0.5)
        
        # Plot buy and sell points on price chart
        buy_indices = [i for i, t in enumerate(trade_types) if t == 'buy']
        sell_indices = [i for i, t in enumerate(trade_types) if t == 'sell']
        
        if buy_indices:
            buy_dates = [trade_dates[i] for i in buy_indices]
            buy_prices = [trade_prices[i] for i in buy_indices]
            plt.scatter(buy_dates, buy_prices, color='green', marker='^', label='Buy')
        
        if sell_indices:
            sell_dates = [trade_dates[i] for i in sell_indices]
            sell_prices = [trade_prices[i] for i in sell_indices]
            plt.scatter(sell_dates, sell_prices, color='red', marker='v', label='Sell')
        
        plt.title('Trade Execution on Price Chart')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        plt.show()
        
        # Print performance metrics
        if results and 'performance_metrics' in results:
            metrics = results['performance_metrics']
            print("\nPerformance Metrics:")
            print(f"Total Return: {metrics['total_return']:.2%}")
            print(f"Annualized Return: {metrics['annualized_return']:.2%}")
            print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
            print(f"Win Rate: {metrics['win_rate']:.2%}")
            print(f"Total Trades: {metrics['total_trades']}")