"""
Unit tests for the TradingAgent component.
"""
import pytest
import os
import yaml
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.ai_adaptation.agent.trading_agent import TradingAgent


class TestTradingAgent:
    """Test suite for TradingAgent"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock agent configuration"""
        return {
            "llm": {
                "model_name": "gpt-4",
                "temperature": 0.1,
                "timeout": 30
            },
            "risk": {
                "profile": "moderate",
                "initial_capital": 100000.0,
                "max_drawdown": 0.10,
                "max_position_size": 0.20,
                "min_confidence": 0.70,
                "max_open_positions": 5
            },
            "default_exchange": "binance",
            "trading_pairs": ["BTC/USDT", "ETH/USDT"],
            "execution": {
                "default_order_type": "market",
                "use_stop_loss": True,
                "use_take_profit": True
            }
        }

    @pytest.fixture
    def mock_openai_response(self):
        """Create a mock OpenAI API response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "action": "buy",
            "confidence": 0.85,
            "size": 0.15,
            "target_price": 44000,
            "stop_loss": 42000,
            "reasoning": "Strong bullish signals with increasing volume and positive sentiment."
        })
        return mock_response

    @pytest.fixture
    def mock_openai_client(self, mock_openai_response):
        """Create a mock OpenAI client"""
        with patch('openai.OpenAI') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock the chat.completions.create method
            mock_client.chat = MagicMock()
            mock_client.chat.completions = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

            yield mock_client

    @pytest.fixture
    def trading_agent(self, mock_config, mock_openai_client):
        """Create a TradingAgent instance with mocked dependencies"""
        with patch('src.ai_adaptation.agent.trading_agent.TradingAgent._load_config', return_value=mock_config):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "mock_api_key"}):
                # Mock dependent components
                with patch('src.ai_adaptation.agent.trading_agent.StrategyManager'):
                    with patch('src.ai_adaptation.agent.trading_agent.RiskManager'):
                        with patch('src.ai_adaptation.agent.trading_agent.ExecutionManager'):
                            with patch('src.ai_adaptation.agent.trading_agent.DataProcessor'):
                                agent = TradingAgent(config_path="mock_config.yaml")
                                agent.risk_manager.get_available_capital = MagicMock(return_value=100000.0)
                                agent._get_current_price = MagicMock(return_value=43250.0)
                                agent._get_portfolio_value = MagicMock(return_value=100000.0)
                                yield agent

    def test_init(self, trading_agent, mock_config):
        """Test initialization of TradingAgent"""
        assert trading_agent.config == mock_config
        assert trading_agent.api_key == "mock_api_key"
        assert trading_agent.model == "gpt-4"
        assert trading_agent.is_active is False
        assert trading_agent.trading_history == []
        assert trading_agent.current_positions == {}
        assert trading_agent.pending_decisions == []

    @pytest.mark.asyncio
    async def test_start_stop(self, trading_agent):
        """Test starting and stopping the agent"""
        # Patch the trading loop to prevent execution
        with patch.object(trading_agent, '_trading_loop', AsyncMock()):
            # Start the agent
            await trading_agent.start()
            assert trading_agent.is_active is True

            # Stop the agent
            await trading_agent.stop()
            assert trading_agent.is_active is False

    @pytest.mark.asyncio
    async def test_start_already_active(self, trading_agent):
        """Test starting an already active agent"""
        # Patch the trading loop to prevent execution
        with patch.object(trading_agent, '_trading_loop', AsyncMock()):
            # Start the agent
            await trading_agent.start()
            assert trading_agent.is_active is True

            # Try to start again
            await trading_agent.start()
            # Should still be active and log a warning (would check logs in a real test)
            assert trading_agent.is_active is True

            # Clean up
            await trading_agent.stop()

    @pytest.mark.asyncio
    async def test_stop_already_stopped(self, trading_agent):
        """Test stopping an already stopped agent"""
        # Agent starts inactive
        assert trading_agent.is_active is False

        # Try to stop
        await trading_agent.stop()
        # Should still be inactive and log a warning
        assert trading_agent.is_active is False

    @pytest.mark.asyncio
    async def test_trading_loop_error_handling(self, trading_agent):
        """Test error handling in the trading loop"""
        # Mock gather_market_data to raise an exception
        trading_agent._gather_market_data = AsyncMock(side_effect=Exception("Test error"))

        # Mock is_critical_error to return False so loop continues
        trading_agent._is_critical_error = MagicMock(return_value=False)

        # Set agent to active
        trading_agent.is_active = True

        # Create a task for the trading loop
        task = asyncio.create_task(trading_agent._trading_loop())

        # Give it a moment to execute
        await asyncio.sleep(0.1)

        # Set agent to inactive to stop the loop
        trading_agent.is_active = False

        # Wait for the task to complete
        await task

        # The agent should have continued despite the error
        trading_agent._gather_market_data.assert_called_once()
        trading_agent._is_critical_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_trading_loop_critical_error(self, trading_agent):
        """Test critical error handling in the trading loop"""
        # Mock gather_market_data to raise an exception
        trading_agent._gather_market_data = AsyncMock(side_effect=Exception("authentication failed"))

        # Set agent to active
        trading_agent.is_active = True

        # Create a task for the trading loop
        task = asyncio.create_task(trading_agent._trading_loop())

        # Give it a moment to execute
        await asyncio.sleep(0.1)

        # Wait for the task to complete
        await task

        # The agent should have stopped due to critical error
        assert trading_agent.is_active is False

    @pytest.mark.asyncio
    async def test_gather_market_data(self, trading_agent):
        """Test gathering market data"""
        # Mock the fetch methods
        trading_agent._fetch_technical_analysis = AsyncMock(return_value={
            "indicators": {"rsi": 65},
            "price": {"current": 43250.0}
        })
        trading_agent._fetch_additional_data = AsyncMock(return_value={
            "sentiment": {"social_score": 72.5},
            "on_chain": {"exchange_inflow": -250.5}
        })

        # Get market data
        market_data = await trading_agent._gather_market_data()

        # Check result
        assert len(market_data) == 2  # Two trading pairs
        assert "BTC/USDT" in market_data
        assert "ETH/USDT" in market_data
        assert "indicators" in market_data["BTC/USDT"]
        assert "sentiment" in market_data["BTC/USDT"]

        # Check that the fetch methods were called
        assert trading_agent._fetch_technical_analysis.call_count == 2
        assert trading_agent._fetch_additional_data.call_count == 2

    @pytest.mark.asyncio
    async def test_make_trading_decisions(self, trading_agent):
        """Test making trading decisions with LLM"""
        # Mock market data
        market_data = {
            "BTC/USDT": {
                "indicators": {"rsi": 65},
                "price": {"current": 43250.0},
                "sentiment": {"social_score": 72.5},
                "on_chain": {"exchange_inflow": -250.5}
            }
        }

        # Mock format_decision_prompt
        trading_agent._format_decision_prompt = MagicMock(return_value="mock prompt")

        # Call the method
        decisions = await trading_agent._make_trading_decisions(market_data)

        # Check result
        assert len(decisions) == 1
        assert decisions[0]["action"] == "buy"
        assert decisions[0]["confidence"] == 0.85
        assert decisions[0]["trading_pair"] == "BTC/USDT"
        assert "timestamp" in decisions[0]

        # Check that the prompt was formatted
        trading_agent._format_decision_prompt.assert_called_once_with("BTC/USDT", market_data["BTC/USDT"])

        # Check that the LLM was queried
        trading_agent.client.chat.completions.create.assert_called_once()

    def test_format_decision_prompt(self, trading_agent):
        """Test formatting the decision prompt for LLM"""
        # Mock market data
        market_data = {
            "indicators": {
                "rsi": 65.5,
                "macd": {"value": 0.002, "signal": 0.001, "histogram": 0.001},
                "ma_200": 42000.0,
                "ma_50": 43500.0,
                "bollinger_bands": {"upper": 44500.0, "middle": 43200.0, "lower": 41900.0}
            },
            "price": {
                "current": 43250.0,
                "high_24h": 43800.0,
                "low_24h": 42800.0,
                "volume_24h": 1250000000.0
            },
            "sentiment": {
                "social_score": 72.5,
                "news_sentiment": 0.65,
                "fear_greed_index": 58
            },
            "on_chain": {
                "exchange_inflow": -250.5,
                "active_addresses": 12500,
                "large_transactions": 450
            }
        }

        # Call the method
        prompt = trading_agent._format_decision_prompt("BTC/USDT", market_data)

        # Check the result
        assert "BTC/USDT" in prompt
        assert "RSI: 65.5" in prompt
        assert "Current Price: 43250.0" in prompt
        assert "Social Score: 72.5" in prompt
        assert "Exchange Inflow: -250.5" in prompt
        assert 'Based on this information, make a trading decision' in prompt

    @pytest.mark.asyncio
    async def test_query_llm(self, trading_agent):
        """Test querying the LLM"""
        # Call the method
        result = await trading_agent._query_llm("Test prompt")

        # Check the result
        assert result == trading_agent.client.chat.completions.create.return_value.choices[0].message.content

        # Check that the client was called correctly
        trading_agent.client.chat.completions.create.assert_called_once_with(
            model=trading_agent.model,
            messages=[
                {"role": "system", "content": "You are Grekko, an advanced cryptocurrency trading AI that provides reasoning in JSON format."},
                {"role": "user", "content": "Test prompt"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

    def test_apply_risk_rules(self, trading_agent):
        """Test applying risk rules to trading decisions"""
        # Create test decisions
        decisions = [
            {
                "trading_pair": "BTC/USDT",
                "action": "buy",
                "confidence": 0.85,  # Above threshold
                "size": 0.15,
                "target_price": 44000,
                "stop_loss": 42000,
                "reasoning": "Strong bullish signals"
            },
            {
                "trading_pair": "ETH/USDT",
                "action": "buy",
                "confidence": 0.65,  # Below threshold
                "size": 0.15,
                "target_price": 3000,
                "stop_loss": 2800,
                "reasoning": "Moderate bullish signals"
            },
            {
                "trading_pair": "LINK/USDT",
                "action": "buy",
                "confidence": 0.75,  # Above threshold
                "size": 0.25,  # Above max position size
                "target_price": 15,
                "stop_loss": 13,
                "reasoning": "Strong bullish signals"
            }
        ]

        # Call the method
        filtered = trading_agent._apply_risk_rules(decisions)

        # Check the result
        assert len(filtered) == 2  # One decision was filtered out (ETH)
        assert filtered[0]["trading_pair"] == "BTC/USDT"  # First decision passed
        assert filtered[1]["trading_pair"] == "LINK/USDT"  # Third decision passed but was modified
        assert filtered[1]["size"] == 0.20  # Size was capped at max position size

    @pytest.mark.asyncio
    async def test_execute_decision_buy(self, trading_agent):
        """Test executing a buy decision"""
        # Mock execution_manager
        mock_order = {
            "symbol": "BTC/USDT",
            "side": "buy",
            "type": "market",
            "amount": 3000.0,
            "price": 43250.0,
            "status": "executed"
        }
        trading_agent.execution_manager.create_order = AsyncMock(return_value=mock_order)

        # Create test decision
        decision = {
            "trading_pair": "BTC/USDT",
            "action": "buy",
            "confidence": 0.85,
            "size": 0.15,
            "target_price": 44000,
            "stop_loss": 42000,
            "reasoning": "Strong bullish signals"
        }

        # Call the method
        await trading_agent._execute_decision(decision)

        # Check that the order was created
        trading_agent.execution_manager.create_order.assert_called_once_with(
            symbol="BTC/USDT",
            order_type="market",
            side="buy",
            amount=15000.0  # 0.15 * 100000
        )

        # Check that the position was updated
        assert "BTC/USDT" in trading_agent.current_positions
        assert trading_agent.current_positions["BTC/USDT"]["entry_price"] == 43250.0
        assert trading_agent.current_positions["BTC/USDT"]["amount"] == 3000.0
        assert trading_agent.current_positions["BTC/USDT"]["stop_loss"] == 42000
        assert trading_agent.current_positions["BTC/USDT"]["target_price"] == 44000

    @pytest.mark.asyncio
    async def test_execute_decision_sell(self, trading_agent):
        """Test executing a sell decision"""
        # Add a position
        trading_agent.current_positions["BTC/USDT"] = {
            "entry_price": 42000.0,
            "amount": 0.5,
            "timestamp": "2025-05-15T12:00:00",
            "stop_loss": 41000,
            "target_price": 44000
        }

        # Mock execution_manager
        mock_order = {
            "symbol": "BTC/USDT",
            "side": "sell",
            "type": "market",
            "amount": 0.5,
            "price": 43250.0,
            "status": "executed"
        }
        trading_agent.execution_manager.create_order = AsyncMock(
            return_value=mock_order
        )

        # Create test decision
        decision = {
            "trading_pair": "BTC/USDT",
            "action": "sell",
            "confidence": 0.85,
            "size": 1.0,
            "target_price": None,
            "stop_loss": None,
            "reasoning": "Take profit triggered"
        }

        # Call the method
        await trading_agent._execute_decision(decision)

        # Check that the order was created
        trading_agent.execution_manager.create_order.assert_called_once_with(
            symbol="BTC/USDT",
            order_type="market",
            side="sell",
            amount=0.5
        )

        # Check that the position was removed
        assert "BTC/USDT" not in trading_agent.current_positions

        # Check that the trade was recorded in history
        assert len(trading_agent.trading_history) == 1
        trade = trading_agent.trading_history[0]
        assert trade["pair"] == "BTC/USDT"
        assert trade["entry_price"] == 42000.0
        assert trade["exit_price"] == 43250.0
        assert trade["amount"] == 0.5
        assert trade["profit_loss"] == (43250.0 - 42000.0) * 0.5  # 625

    @pytest.mark.asyncio
    async def test_execute_decision_hold(self, trading_agent):
        """Test executing a hold decision"""
        # Create test decision
        decision = {
            "trading_pair": "BTC/USDT",
            "action": "hold",
            "confidence": 0.85,
            "size": 0.0,
            "target_price": None,
            "stop_loss": None,
            "reasoning": "Market is consolidating"
        }

        # Call the method
        await trading_agent._execute_decision(decision)

        # Check that no order was created
        trading_agent.execution_manager.create_order.assert_not_called()

    def test_update_agent_state_stop_loss(self, trading_agent):
        """Test updating agent state with stop loss trigger"""
        # Add a position
        trading_agent.current_positions["BTC/USDT"] = {
            "entry_price": 43000.0,
            "amount": 0.5,
            "timestamp": "2025-05-15T12:00:00",
            "stop_loss": 42500,  # Stop loss above current price
            "target_price": 44000
        }

        # Mock current price below stop loss
        trading_agent._get_current_price = MagicMock(return_value=42400.0)

        # Call the method
        trading_agent._update_agent_state()

        # Check that a sell decision was added to pending decisions
        assert len(trading_agent.pending_decisions) == 1
        decision = trading_agent.pending_decisions[0]
        assert decision["trading_pair"] == "BTC/USDT"
        assert decision["action"] == "sell"
        assert decision["reasoning"] == "Stop loss triggered"

    def test_update_agent_state_take_profit(self, trading_agent):
        """Test updating agent state with take profit trigger"""
        # Add a position
        trading_agent.current_positions["BTC/USDT"] = {
            "entry_price": 43000.0,
            "amount": 0.5,
            "timestamp": "2025-05-15T12:00:00",
            "stop_loss": 42000,
            "target_price": 44000  # Take profit below current price
        }

        # Mock current price above target
        trading_agent._get_current_price = MagicMock(return_value=44100.0)

        # Call the method
        trading_agent._update_agent_state()

        # Check that a sell decision was added to pending decisions
        assert len(trading_agent.pending_decisions) == 1
        decision = trading_agent.pending_decisions[0]
        assert decision["trading_pair"] == "BTC/USDT"
        assert decision["action"] == "sell"
        assert decision["reasoning"] == "Take profit triggered"

    def test_should_emergency_stop_exceeds_drawdown(self, trading_agent):
        """Test emergency stop when drawdown exceeds limit"""
        # Mock portfolio value below drawdown limit
        trading_agent._get_portfolio_value = MagicMock(
            return_value=85000.0)  # 15% drawdown

        # Call the method
        result = trading_agent._should_emergency_stop()

        # Should return True (stop trading)
        assert result is True

    def test_should_emergency_stop_no_drawdown(self, trading_agent):
        """Test emergency stop with no drawdown"""
        # Mock portfolio value above drawdown limit
        trading_agent._get_portfolio_value = MagicMock(
            return_value=95000.0)  # 5% drawdown

        # Call the method
        result = trading_agent._should_emergency_stop()

        # Should return False (continue trading)
        assert result is False

    def test_is_critical_error(self, trading_agent):
        """Test critical error detection"""
        # Test critical errors
        assert trading_agent._is_critical_error(
            Exception("Authentication failed")
        ) is True
        assert trading_agent._is_critical_error(
            Exception("Insufficient funds")
        ) is True
        assert trading_agent._is_critical_error(
            Exception("Connection error")
        ) is True

        # Test non-critical errors
        assert trading_agent._is_critical_error(
            Exception("Some minor error")
        ) is False
        assert trading_agent._is_critical_error(
            Exception("Operation timed out")
        ) is False

    def test_report_status(self, trading_agent):
        """Test generating a status report"""
        # Add some data
        trading_agent.current_positions["BTC/USDT"] = {
            "entry_price": 43000.0,
            "amount": 0.5,
            "timestamp": "2025-05-15T12:00:00",
            "stop_loss": 42000,
            "target_price": 44000
        }

        trading_agent.trading_history = [
            {
                "pair": "ETH/USDT",
                "entry_price": 2800.0,
                "exit_price": 3000.0,
                "amount": 5.0,
                "profit_loss": 1000.0,
                "entry_time": "2025-05-10T10:00:00",
                "exit_time": "2025-05-15T10:00:00"
            },
            {
                "pair": "LINK/USDT",
                "entry_price": 15.0,
                "exit_price": 14.0,
                "amount": 100.0,
                "profit_loss": -100.0,
                "entry_time": "2025-05-12T10:00:00",
                "exit_time": "2025-05-14T10:00:00"
            }
        ]

        # Call the method
        report = trading_agent._report_status()

        # Check the report
        assert report["active"] is False
        assert report["portfolio_value"] == 100000.0
        assert report["initial_capital"] == 100000.0
        assert report["open_positions"] == trading_agent.current_positions
        assert report["completed_trades"] == 2
        assert report["profitable_trades"] == 1
        assert report["total_profit_loss"] == 900.0  # 1000 - 100
        assert report["total_profit_loss"] == 900.0  # 1000 - 100
