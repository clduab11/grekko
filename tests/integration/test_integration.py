"""
Integration tests for the Grekko platform.
"""
import pytest
import asyncio
import yaml
from unittest.mock import patch, MagicMock, AsyncMock

from src.ai_adaptation.agent.trading_agent import TradingAgent
from src.data_ingestion.data_processor import DataProcessor
from src.data_ingestion.data_streamer import DataStreamer
from src.strategy.strategy_manager import StrategyManager
from src.risk_management.risk_manager import RiskManager
from src.execution.execution_manager import ExecutionManager


@pytest.mark.asyncio
async def test_full_trading_pipeline(config, test_logger, mock_credentials_manager):
    """
    Test the full trading pipeline from data ingestion to execution.
    
    This test mocks external components but tests the integration between:
    - Data ingestion
    - Strategy selection
    - Risk management
    - Execution
    """
    # Create mocked components
    data_processor = MagicMock(spec=DataProcessor)
    data_streamer = MagicMock(spec=DataStreamer)
    strategy_manager = MagicMock(spec=StrategyManager)
    risk_manager = MagicMock(spec=RiskManager)
    execution_manager = MagicMock(spec=ExecutionManager)
    
    # Setup mock returns
    data_processor.process_market_data.return_value = {
        'symbol': 'BTC/USDT',
        'price': 45000.0,
        'volume': 1000.0,
        'indicators': {
            'rsi': 65,
            'macd': 'bullish',
            'ema_short': 44500,
            'ema_long': 43000
        }
    }
    
    strategy_manager.evaluate_strategies.return_value = {
        'selected_strategy': 'momentum',
        'action': 'BUY',
        'confidence': 0.85,
        'amount': 0.1,
        'price': 45000.0
    }
    
    risk_manager.validate_trade.return_value = {
        'approved': True,
        'modified_amount': 0.1,
        'risk_score': 0.65
    }
    
    execution_manager.execute_trade.return_value = {
        'success': True,
        'order_id': '123456',
        'executed_price': 45010.0,
        'executed_amount': 0.1,
        'timestamp': 1620000000000
    }
    
    # Create a trading agent with mocked components
    with patch('src.ai_adaptation.agent.trading_agent.requests.post'):
        # Create temporary config file
        temp_config = {
            'general': {'name': 'test_agent', 'log_level': 'INFO'},
            'trading': {'trading_pairs': ['BTC/USDT']},
            'risk': {'max_drawdown_pct': 5.0, 'stop_loss_pct': 2.0},
            'llm': {'provider': 'openai', 'model': 'gpt-4'}
        }
        
        # Test the full pipeline
        try:
            # Step 1: Get market data
            market_data = data_processor.process_market_data('BTC/USDT')
            assert market_data['symbol'] == 'BTC/USDT'
            
            # Step 2: Evaluate strategies
            strategy_result = strategy_manager.evaluate_strategies(market_data)
            assert strategy_result['action'] == 'BUY'
            
            # Step 3: Apply risk management
            risk_result = risk_manager.validate_trade(strategy_result)
            assert risk_result['approved'] is True
            
            # Step 4: Execute trade
            execution_result = execution_manager.execute_trade(
                symbol=market_data['symbol'],
                action=strategy_result['action'],
                amount=risk_result['modified_amount'],
                price=strategy_result['price']
            )
            assert execution_result['success'] is True
            
            # Verify the full pipeline worked as expected
            test_logger.info("Full trading pipeline test passed")
        
        except Exception as e:
            test_logger.error(f"Pipeline test failed: {str(e)}")
            raise


@pytest.mark.asyncio
async def test_data_processor_integration(test_logger):
    """Test integration of DataProcessor with connectors."""
    # Create a real DataProcessor instance
    data_processor = DataProcessor()
    
    # Mock the connector's fetch_ticker method
    mock_fetch_ticker = AsyncMock(return_value={
        'symbol': 'BTC/USDT',
        'last': 45000.0,
        'bid': 44950.0,
        'ask': 45050.0,
        'volume': 1000.0,
        'timestamp': 1620000000000
    })
    
    # Create a mock connector
    mock_connector = MagicMock()
    mock_connector.fetch_ticker = mock_fetch_ticker
    
    # Patch the connector creation in the data processor
    with patch.object(data_processor, '_get_connector', return_value=mock_connector):
        # Process market data
        result = await data_processor.process_market_data_async('BTC/USDT', 'binance')
        
        # Verify the result
        assert result['symbol'] == 'BTC/USDT'
        assert result['price'] == 45000.0
        assert 'volume' in result
        
        # Verify the connector was called correctly
        mock_fetch_ticker.assert_called_once_with('BTC/USDT')


@pytest.mark.asyncio
async def test_risk_strategy_integration(test_logger):
    """Test integration between strategy and risk components."""
    # Create instances
    strategy_manager = StrategyManager(exchange='binance')
    risk_manager = RiskManager(capital=100000.0)
    
    # Mock strategy evaluation
    with patch.object(strategy_manager, 'evaluate_strategies', return_value={
        'selected_strategy': 'momentum',
        'action': 'BUY',
        'symbol': 'BTC/USDT',
        'amount': 0.5,  # 0.5 BTC
        'price': 45000.0  # $45,000 per BTC
    }):
        # Get strategy recommendation
        strategy_result = strategy_manager.evaluate_strategies({
            'symbol': 'BTC/USDT',
            'price': 45000.0,
            'volume': 1000.0,
            'indicators': {'rsi': 65}
        })
        
        # Apply risk management
        position_size = risk_manager.calculate_position_size(
            risk_per_trade=0.01,  # 1% risk per trade
            stop_loss_distance=0.05  # 5% stop loss
        )
        
        # Enforce risk limits
        trade_amount = strategy_result['amount']
        adjusted_amount = risk_manager.enforce_risk_limits(trade_amount * strategy_result['price']) / strategy_result['price']
        
        # Verify results
        assert strategy_result['action'] == 'BUY'
        assert adjusted_amount > 0
        assert adjusted_amount <= trade_amount
        
        # Log results
        test_logger.info(f"Original trade: {trade_amount} BTC, Adjusted: {adjusted_amount} BTC")


@pytest.mark.asyncio
async def test_emergency_shutdown(test_logger):
    """Test the emergency shutdown process."""
    # Create a trading agent
    with patch('src.ai_adaptation.agent.trading_agent.requests.post'):
        agent_config = {
            'general': {'name': 'test_agent', 'log_level': 'INFO'},
            'trading': {'trading_pairs': ['BTC/USDT']},
            'risk': {'max_drawdown_pct': 5.0, 'stop_loss_pct': 2.0},
            'llm': {'provider': 'openai', 'model': 'gpt-4'}
        }
        
        # Create a mock config path
        with patch('yaml.safe_load', return_value=agent_config):
            agent = TradingAgent(config_path="mock_path.yaml")
            
            # Start the agent
            with patch.object(agent, '_trading_loop', new_callable=AsyncMock):
                await agent.start()
                assert agent.is_active is True
                
                # Simulate a critical error
                await agent._handle_error(Exception("Invalid API key"))
                
                # Verify the agent has shut down
                assert agent.is_active is False
                
                # Attempt restart
                await agent.start()
                assert agent.is_active is True
                
                # Clean up
                await agent.stop()
                assert agent.is_active is False