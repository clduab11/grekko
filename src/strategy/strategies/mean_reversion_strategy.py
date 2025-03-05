import logging
import pandas as pd

class MeanReversionStrategy:
    def __init__(self, lookback_period, entry_threshold, exit_threshold):
        self.logger = logging.getLogger(__name__)
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.data = pd.DataFrame()

    def add_data(self, price_data):
        self.data = self.data.append(price_data, ignore_index=True)
        if len(self.data) > self.lookback_period:
            self.data = self.data.iloc[-self.lookback_period:]

    def calculate_mean_reversion(self):
        mean_price = self.data['price'].mean()
        current_price = self.data['price'].iloc[-1]
        deviation = (current_price - mean_price) / mean_price
        return deviation

    def identify_trade_signal(self):
        deviation = self.calculate_mean_reversion()
        if deviation > self.entry_threshold:
            self.logger.info("Mean reversion signal: SELL")
            return "SELL"
        elif deviation < -self.entry_threshold:
            self.logger.info("Mean reversion signal: BUY")
            return "BUY"
        elif abs(deviation) < self.exit_threshold:
            self.logger.info("Mean reversion signal: EXIT")
            return "EXIT"
        else:
            self.logger.info("Mean reversion signal: HOLD")
            return "HOLD"

    def execute_trade(self, signal, amount):
        if signal == "BUY":
            self.logger.info(f"Executing BUY trade for amount: {amount}")
            # Implement buy logic here
        elif signal == "SELL":
            self.logger.info(f"Executing SELL trade for amount: {amount}")
            # Implement sell logic here
        elif signal == "EXIT":
            self.logger.info(f"Executing EXIT trade for amount: {amount}")
            # Implement exit logic here
        else:
            self.logger.info("No trade executed")
