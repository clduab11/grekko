import logging

class RiskManager:
    def __init__(self, capital):
        self.capital = capital
        self.logger = logging.getLogger(__name__)

    def calculate_position_size(self, risk_per_trade, stop_loss_distance):
        position_size = (self.capital * risk_per_trade) / stop_loss_distance
        return position_size

    def enforce_risk_limits(self, trade_amount):
        max_risk_per_trade = 0.015 * self.capital
        if trade_amount > max_risk_per_trade:
            self.logger.warning(f"Trade amount {trade_amount} exceeds max risk per trade {max_risk_per_trade}. Reducing trade amount.")
            trade_amount = max_risk_per_trade
        return trade_amount

    def time_weighted_order_slicing(self, total_amount, slices, interval):
        slice_amount = total_amount / slices
        for i in range(slices):
            self.logger.info(f"Executing slice {i+1}/{slices} of amount {slice_amount}")
            # Execute the slice order here
            time.sleep(interval)
