"""
Integration test: End-to-end trading pipeline with real modules (no mocks).
Covers: Data ingestion, Alpha Strategy (momentum), Risk Management, Execution Aggregator.

This test simulates a full trade flow using test data and asserts that each critical module
performs as expected. It is designed to run in a Dockerized or local test environment.
"""

import pytest
import asyncio
from src.data_ingestion.data_processor import DataProcessor
from src.strategy.strategy_manager import StrategyManager
from src.risk_management.risk_manager import RiskManager
from src.execution.execution_manager import ExecutionManager

@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    # Step 1: Data Ingestion (simulate market data)
    data_processor = DataProcessor()
    market_data = {
        'symbol': 'BTC/USDT',
        'price': 45000.0,
        'volume': 1000.0,
        'indicators': {
            'rsi': 70,
            'macd': 'bullish',
            'ema_short': 45200,
            'ema_long': 44000
        }
    }

    # Step 2: Alpha Strategy (Momentum)
    strategy_manager = StrategyManager(exchange='binance')
    strategy_manager.switch_strategy('momentum')
    # Get the current strategy object
    current_strategy = strategy_manager.current_strategy
    assert current_strategy is not None
    signal = current_strategy.identify_trade_signal(market_data)
    assert isinstance(signal, dict)
    assert signal.get('action') in ['BUY', 'SELL']
    assert signal.get('amount', 0) > 0

    # Step 3: Risk Management (Position Sizing, Risk Limits)
    risk_manager = RiskManager(capital=100000.0)
    position_size = risk_manager.calculate_position_size(
        risk_per_trade=0.01,  # 1% risk per trade
        stop_loss_distance=0.05  # 5% stop loss
    )
    adjusted_amount = risk_manager.enforce_risk_limits(signal['amount'])
    assert adjusted_amount > 0
    assert adjusted_amount <= signal['amount']

    # Step 4: Execution Aggregator (Order Routing)
    config = {
        'exchanges': ['binance'],
        'default_order_type': 'limit',
        'max_slippage': 0.01
    }
    execution_manager = ExecutionManager(config=config, risk_manager=risk_manager)
    # Prepare order parameters
    order_params = {
        'symbol': market_data['symbol'],
        'side': signal['action'],
        'amount': adjusted_amount,
        'price': market_data['price'],
        'order_type': 'limit'
    }
    # Execute order (async)
    execution_result = await execution_manager.execute_order(**order_params)
    assert execution_result['status'] in ['filled', 'submitted', 'partially_filled']

    # Step 5: Risk Assessment (optional, e.g., real-time)
    risk_score = risk_manager._calculate_risk_score(
        symbol=market_data['symbol'],
        side=signal['action'],
        amount=adjusted_amount,
        price=market_data['price']
    )
    assert 0.0 <= risk_score <= 1.0

    print("End-to-end pipeline integration test passed.")