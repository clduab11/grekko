# Phase 3: Market Making Bot TDD Specifications

## Overview

This document provides comprehensive Test-Driven Development (TDD) anchor specifications for the Market Making Bot System, following London School TDD principles with outside-in development and extensive use of test doubles for trading logic, strategy execution, risk management, order book management, and performance tracking.

## Test Categories

### 1. Unit Tests for Core Functions

#### MarketMakingBot Unit Tests

```python
class TestMarketMakingBot:
    """Unit tests for MarketMakingBot core functionality"""
    
    def setup_method(self):
        """Setup test doubles and dependencies"""
        self.mock_config = Mock(spec=MarketMakingConfig)
        self.mock_wallet_provider = Mock(spec=WalletProvider)
        self.mock_event_bus = Mock(spec=EventBus)
        self.mock_strategy_engine = Mock(spec=StrategyEngine)
        self.mock_inventory_manager = Mock(spec=InventoryManager)
        self.mock_risk_manager = Mock(spec=MarketMakingRiskManager)
        self.mock_order_manager = Mock(spec=OrderManager)
        self.mock_performance_tracker = Mock(spec=PerformanceTracker)
        
        # Configure mock config
        self.mock_config.bot_id = "test_bot_001"
        self.mock_config.exchanges = [Mock(spec=ExchangeConfig)]
        self.mock_config.monitoring_interval = 5
        self.mock_config.error_recovery_delay = 10
        self.mock_config.min_order_size = 10.0
        self.mock_config.max_order_size = 10000.0
        
    def test_bot_initialization_with_valid_config(self):
        """GIVEN valid market making configuration
        WHEN MarketMakingBot is initialized
        THEN bot should initialize with correct dependencies"""
        
        with patch('validate_market_making_config', return_value=self.mock_config):
            bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
            
            assert bot.config == self.mock_config
            assert bot.bot_id == "test_bot_001"
            assert bot.wallet_provider == self.mock_wallet_provider
            assert bot.event_bus == self.mock_event_bus
            assert isinstance(bot.exchanges, dict)
            assert isinstance(bot.active_positions, dict)
            assert bot.is_active is False
    
    def test_bot_initialization_with_invalid_config(self):
        """GIVEN invalid market making configuration
        WHEN MarketMakingBot is initialized
        THEN should raise ConfigurationError"""
        
        with patch('validate_market_making_config', side_effect=ConfigurationError("Invalid config")):
            with pytest.raises(ConfigurationError):
                MarketMakingBot(None, self.mock_wallet_provider, self.mock_event_bus)
    
    @pytest.mark.asyncio
    async def test_initialize_exchanges_success(self):
        """GIVEN valid exchange configurations
        WHEN initialize_exchanges is called
        THEN all exchanges should be connected successfully"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        mock_exchange.exchange_id = "test_exchange"
        mock_exchange.validate_connection.return_value = True
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        with patch.object(bot, '_create_exchange_client', return_value=mock_exchange):
            result = await bot.initialize_exchanges()
            
            assert result is True
            assert "test_exchange" in bot.exchanges
            self.mock_event_bus.emit.assert_called()
    
    @pytest.mark.asyncio
    async def test_initialize_exchanges_connection_failure(self):
        """GIVEN exchange with failed connection
        WHEN initialize_exchanges is called
        THEN exchange should not be registered"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        mock_exchange.validate_connection.return_value = False
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        with patch.object(bot, '_create_exchange_client', return_value=mock_exchange):
            result = await bot.initialize_exchanges()
            
            assert len(bot.exchanges) == 0
    
    @pytest.mark.asyncio
    async def test_start_market_making_success(self):
        """GIVEN valid trading pairs and risk conditions
        WHEN start_market_making is called
        THEN should initialize positions and start monitoring"""
        
        trading_pairs = ["BTC/USDT", "ETH/USDT"]
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        bot.risk_manager = self.mock_risk_manager
        bot.inventory_manager = self.mock_inventory_manager
        bot.strategy_engine = self.mock_strategy_engine
        
        # Configure mocks
        self.mock_risk_manager.validate_startup_conditions.return_value = True
        self.mock_inventory_manager.assess_initial_inventory.return_value = None
        self.mock_strategy_engine.create_strategy.return_value = Mock(spec=MarketMakingStrategy)
        
        with patch.object(bot, '_validate_trading_pair', return_value=True):
            with patch.object(bot, '_place_initial_orders') as mock_place_orders:
                with patch('asyncio.create_task') as mock_create_task:
                    result = await bot.start_market_making(trading_pairs)
                    
                    assert result is True
                    assert bot.is_active is True
                    assert len(bot.active_positions) == 2
                    mock_place_orders.assert_called()
                    mock_create_task.assert_called_once()
                    self.mock_event_bus.emit.assert_called()
    
    @pytest.mark.asyncio
    async def test_start_market_making_invalid_pairs(self):
        """GIVEN invalid trading pairs
        WHEN start_market_making is called
        THEN should raise InvalidTradingPairsError"""
        
        invalid_pairs = ["INVALID/PAIR", "ANOTHER/INVALID"]
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        with patch.object(bot, '_validate_trading_pair', return_value=False):
            with pytest.raises(InvalidTradingPairsError):
                await bot.start_market_making(invalid_pairs)
    
    @pytest.mark.asyncio
    async def test_start_market_making_risk_limit_violation(self):
        """GIVEN risk limit violations
        WHEN start_market_making is called
        THEN should raise RiskLimitViolationError"""
        
        trading_pairs = ["BTC/USDT"]
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        bot.risk_manager = self.mock_risk_manager
        
        self.mock_risk_manager.validate_startup_conditions.return_value = False
        
        with patch.object(bot, '_validate_trading_pair', return_value=True):
            with pytest.raises(RiskLimitViolationError):
                await bot.start_market_making(trading_pairs)
    
    @pytest.mark.asyncio
    async def test_stop_market_making_success(self):
        """GIVEN active market making bot
        WHEN stop_market_making is called
        THEN should cancel orders and generate performance summary"""
        
        # Setup active position
        mock_position = Mock(spec=LiquidityPosition)
        mock_position.position_id = "pos_001"
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        bot.is_active = True
        bot.active_positions = {"BTC/USDT": mock_position}
        bot.inventory_manager = self.mock_inventory_manager
        bot.performance_tracker = self.mock_performance_tracker
        
        # Configure mocks
        mock_final_inventory = {"BTC": 1.5, "USDT": 50000}
        mock_performance_summary = {"total_profit": 1250.50, "trades": 150}
        
        self.mock_inventory_manager.get_final_inventory.return_value = mock_final_inventory
        self.mock_performance_tracker.generate_summary.return_value = mock_performance_summary
        
        with patch.object(bot, '_cancel_position_orders') as mock_cancel:
            result = await bot.stop_market_making()
            
            assert result is True
            assert bot.is_active is False
            mock_cancel.assert_called_once_with(mock_position)
            self.mock_event_bus.emit.assert_called()
    
    def test_validate_trading_pair_valid_format(self):
        """GIVEN valid trading pair format
        WHEN _validate_trading_pair is called
        THEN should return True if supported by exchanges"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        mock_exchange.supports_trading_pair.return_value = True
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        bot.exchanges = {"test_exchange": mock_exchange}
        
        result = bot._validate_trading_pair("BTC/USDT")
### 2. Trading Logic and Strategy Execution Tests

#### StrategyEngine Unit Tests

```python
class TestStrategyEngine:
    """Tests for strategy engine and strategy selection"""
    
    def setup_method(self):
        """Setup strategy engine configuration and mocks"""
        self.mock_config = Mock(spec=StrategyConfig)
        self.mock_config.high_volatility_threshold = 0.05
        self.mock_config.low_liquidity_threshold = 1000.0
        self.mock_config.strong_trend_threshold = 0.7
        
        self.mock_strategy_factory = Mock(spec=StrategyFactory)
        self.mock_performance_analyzer = Mock(spec=StrategyPerformanceAnalyzer)
        
    def test_strategy_engine_initialization(self):
        """GIVEN valid strategy configuration
        WHEN StrategyEngine is initialized
        THEN should set up components correctly"""
        
        engine = StrategyEngine(self.mock_config)
        
        assert engine.config == self.mock_config
        assert isinstance(engine.strategies, dict)
        assert hasattr(engine, 'strategy_factory')
        assert hasattr(engine, 'performance_analyzer')
    
    @pytest.mark.asyncio
    async def test_create_strategy_success(self):
        """GIVEN valid trading pair and market analysis
        WHEN create_strategy is called
        THEN should create and validate strategy"""
        
        trading_pair = "BTC/USDT"
        mock_market_analysis = Mock(spec=MarketAnalysis)
        mock_market_analysis.volatility = 0.03
        mock_market_analysis.liquidity = 5000.0
        mock_market_analysis.trend_strength = 0.5
        
        mock_strategy = Mock(spec=MarketMakingStrategy)
        mock_strategy.validate_parameters.return_value = True
        
        engine = StrategyEngine(self.mock_config)
        engine.strategy_factory = self.mock_strategy_factory
        
        self.mock_strategy_factory.create_strategy.return_value = mock_strategy
        
        with patch.object(engine, '_analyze_market_characteristics', return_value=mock_market_analysis):
            with patch.object(engine, '_select_strategy_type', return_value="GRID_TRADING"):
                result = await engine.create_strategy(trading_pair)
                
                assert result == mock_strategy
                assert trading_pair in engine.strategies
                self.mock_strategy_factory.create_strategy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_strategy_invalid_parameters(self):
        """GIVEN strategy with invalid parameters
        WHEN create_strategy is called
        THEN should raise InvalidStrategyError"""
        
        trading_pair = "BTC/USDT"
        mock_market_analysis = Mock(spec=MarketAnalysis)
        mock_strategy = Mock(spec=MarketMakingStrategy)
        mock_strategy.validate_parameters.return_value = False
        
        engine = StrategyEngine(self.mock_config)
        engine.strategy_factory = self.mock_strategy_factory
        
        self.mock_strategy_factory.create_strategy.return_value = mock_strategy
        
        with patch.object(engine, '_analyze_market_characteristics', return_value=mock_market_analysis):
            with patch.object(engine, '_select_strategy_type', return_value="GRID_TRADING"):
                with pytest.raises(InvalidStrategyError):
                    await engine.create_strategy(trading_pair)
    
    def test_select_strategy_type_high_volatility(self):
        """GIVEN high volatility market conditions
        WHEN _select_strategy_type is called
        THEN should return VOLATILITY_ADAPTIVE strategy"""
        
        mock_market_analysis = Mock(spec=MarketAnalysis)
        mock_market_analysis.volatility = 0.08  # Above threshold
        mock_market_analysis.liquidity = 5000.0
        mock_market_analysis.trend_strength = 0.5
        
        engine = StrategyEngine(self.mock_config)
        
        result = engine._select_strategy_type(mock_market_analysis)
        
        assert result == "VOLATILITY_ADAPTIVE"
    
    def test_select_strategy_type_low_liquidity(self):
        """GIVEN low liquidity market conditions
        WHEN _select_strategy_type is called
        THEN should return INVENTORY_BASED strategy"""
        
        mock_market_analysis = Mock(spec=MarketAnalysis)
        mock_market_analysis.volatility = 0.02  # Below volatility threshold
        mock_market_analysis.liquidity = 500.0  # Below liquidity threshold
        mock_market_analysis.trend_strength = 0.5
        
        engine = StrategyEngine(self.mock_config)
        
        result = engine._select_strategy_type(mock_market_analysis)
        
        assert result == "INVENTORY_BASED"
    
    def test_select_strategy_type_strong_trend(self):
        """GIVEN strong trend market conditions
        WHEN _select_strategy_type is called
        THEN should return TREND_FOLLOWING strategy"""
        
        mock_market_analysis = Mock(spec=MarketAnalysis)
        mock_market_analysis.volatility = 0.02  # Below volatility threshold
        mock_market_analysis.liquidity = 5000.0  # Above liquidity threshold
        mock_market_analysis.trend_strength = 0.8  # Above trend threshold
        
        engine = StrategyEngine(self.mock_config)
        
        result = engine._select_strategy_type(mock_market_analysis)
        
        assert result == "TREND_FOLLOWING"
    
    def test_select_strategy_type_default(self):
        """GIVEN normal market conditions
        WHEN _select_strategy_type is called
        THEN should return GRID_TRADING strategy"""
        
        mock_market_analysis = Mock(spec=MarketAnalysis)
        mock_market_analysis.volatility = 0.02  # Below volatility threshold
        mock_market_analysis.liquidity = 5000.0  # Above liquidity threshold
        mock_market_analysis.trend_strength = 0.5  # Below trend threshold
        
        engine = StrategyEngine(self.mock_config)
        
        result = engine._select_strategy_type(mock_market_analysis)
        
        assert result == "GRID_TRADING"
```

#### MarketMakingStrategy Unit Tests

```python
class TestMarketMakingStrategy:
    """Tests for market making strategy implementations"""
    
    def setup_method(self):
        """Setup strategy test environment"""
        self.mock_config = Mock(spec=StrategyConfig)
        self.mock_config.grid_levels = 10
        self.mock_config.spread_percentage = 0.002
        self.mock_config.inventory_target_ratio = 0.5
        
    def test_grid_trading_strategy_initialization(self):
        """GIVEN valid grid trading configuration
        WHEN GridTradingStrategy is initialized
        THEN should set up grid parameters correctly"""
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        assert strategy.trading_pair == "BTC/USDT"
        assert strategy.grid_levels == 10
        assert strategy.spread_percentage == 0.002
        assert strategy.target_ratio == 0.5
    
    @pytest.mark.asyncio
    async def test_calculate_orders_balanced_inventory(self):
        """GIVEN balanced inventory and market data
        WHEN calculate_orders is called
        THEN should generate symmetric bid/ask orders"""
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        mock_market_data = Mock(spec=MarketData)
        mock_market_data.mid_price = 50000.0
        mock_market_data.bid_price = 49950.0
        mock_market_data.ask_price = 50050.0
        mock_market_data.spread = 100.0
        
        mock_inventory = Mock(spec=InventoryState)
        mock_inventory.current_ratio = 0.5  # Balanced
        mock_inventory.base_balance = Mock()
        mock_inventory.base_balance.available = 1.0
        mock_inventory.quote_balance = Mock()
        mock_inventory.quote_balance.available = 50000.0
        
        mock_risk_limits = Mock(spec=RiskLimits)
        mock_risk_limits.max_order_size = 1000.0
        
        order_params = await strategy.calculate_orders(
            market_data=mock_market_data,
            inventory=mock_inventory,
            risk_limits=mock_risk_limits
        )
        
        # Should generate both bid and ask orders
        bid_orders = [o for o in order_params if o.side == "BUY"]
        ask_orders = [o for o in order_params if o.side == "SELL"]
        
        assert len(bid_orders) > 0
        assert len(ask_orders) > 0
        assert len(bid_orders) == len(ask_orders)  # Symmetric for balanced inventory
    
    @pytest.mark.asyncio
    async def test_calculate_orders_imbalanced_inventory(self):
        """GIVEN imbalanced inventory (excess base)
        WHEN calculate_orders is called
        THEN should favor sell orders to rebalance"""
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        mock_market_data = Mock(spec=MarketData)
        mock_market_data.mid_price = 50000.0
        mock_market_data.bid_price = 49950.0
        mock_market_data.ask_price = 50050.0
        
        mock_inventory = Mock(spec=InventoryState)
        mock_inventory.current_ratio = 0.8  # Excess base (BTC)
        mock_inventory.base_balance = Mock()
        mock_inventory.base_balance.available = 2.0
        mock_inventory.quote_balance = Mock()
        mock_inventory.quote_balance.available = 25000.0
        
        mock_risk_limits = Mock(spec=RiskLimits)
        mock_risk_limits.max_order_size = 1000.0
        
        order_params = await strategy.calculate_orders(
            market_data=mock_market_data,
            inventory=mock_inventory,
            risk_limits=mock_risk_limits
        )
        
        bid_orders = [o for o in order_params if o.side == "BUY"]
        ask_orders = [o for o in order_params if o.side == "SELL"]
        
        # Should favor sell orders to reduce base inventory
        assert len(ask_orders) > len(bid_orders)
    
    @pytest.mark.asyncio
    async def test_should_adapt_high_volatility(self):
        """GIVEN high volatility market conditions
        WHEN should_adapt is called
        THEN should return True"""
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        mock_market_conditions = Mock(spec=MarketConditions)
        mock_market_conditions.volatility = 0.08  # High volatility
        mock_market_conditions.liquidity = 5000.0
        mock_market_conditions.trend_strength = 0.3
        
        result = await strategy.should_adapt(mock_market_conditions)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_adapt_stable_conditions(self):
        """GIVEN stable market conditions
        WHEN should_adapt is called
        THEN should return False"""
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        mock_market_conditions = Mock(spec=MarketConditions)
        mock_market_conditions.volatility = 0.02  # Low volatility
        mock_market_conditions.liquidity = 5000.0
        mock_market_conditions.trend_strength = 0.3
        
        result = await strategy.should_adapt(mock_market_conditions)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_adapt_to_conditions_increase_spreads(self):
        """GIVEN high volatility conditions
        WHEN adapt_to_conditions is called
        THEN should increase spreads for risk management"""
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        mock_market_conditions = Mock(spec=MarketConditions)
        mock_market_conditions.volatility = 0.08  # High volatility
        mock_market_conditions.liquidity = 5000.0
        mock_market_conditions.trend_strength = 0.3
        
        original_spread = strategy.spread_percentage
        
        new_params = await strategy.adapt_to_conditions(mock_market_conditions)
        
        assert new_params.spread_percentage > original_spread
        assert new_params.grid_levels <= strategy.grid_levels  # May reduce levels
    
    def test_validate_parameters_valid(self):
        """GIVEN valid strategy parameters
        WHEN validate_parameters is called
        THEN should return True"""
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        result = strategy.validate_parameters()
        
        assert result is True
    
    def test_validate_parameters_invalid_spread(self):
        """GIVEN invalid spread percentage
        WHEN validate_parameters is called
        THEN should return False"""
        
        self.mock_config.spread_percentage = -0.001  # Invalid negative spread
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        result = strategy.validate_parameters()
        
        assert result is False
    
    def test_validate_parameters_invalid_grid_levels(self):
        """GIVEN invalid grid levels
        WHEN validate_parameters is called
        THEN should return False"""
        
        self.mock_config.grid_levels = 0  # Invalid zero levels
        
        strategy = GridTradingStrategy("BTC/USDT", self.mock_config)
        
        result = strategy.validate_parameters()
        
        assert result is False
```

### 3. Risk Management and Position Sizing Tests

#### MarketMakingRiskManager Unit Tests

```python
class TestMarketMakingRiskManager:
    """Tests for market making risk management"""
    
    def setup_method(self):
        """Setup risk manager configuration and test data"""
        self.mock_risk_limits = Mock(spec=RiskLimits)
        self.mock_risk_limits.max_position_size = 100000.0
        self.mock_risk_limits.max_daily_loss = 1000.0
        self.mock_risk_limits.max_drawdown = 0.1
        self.mock_risk_limits.inventory_deviation_limit = 0.3
        self.mock_risk_limits.volatility_pause_threshold = 0.1
        
        self.risk_manager = MarketMakingRiskManager(self.mock_risk_limits)
    
    @pytest.mark.asyncio
    async def test_validate_startup_conditions_success(self):
        """GIVEN acceptable risk conditions
        WHEN validate_startup_conditions is called
        THEN should return True"""
        
        with patch.object(self.risk_manager, '_check_position_limits', return_value=True):
            with patch.object(self.risk_manager, '_check_daily_loss_limits', return_value=True):
                with patch.object(self.risk_manager, '_check_market_volatility', return_value=True):
                    result = await self.risk_manager.validate_startup_conditions()
                    
                    assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_startup_conditions_position_limit_exceeded(self):
        """GIVEN position limits exceeded
        WHEN validate_startup_conditions is called
        THEN should return False"""
        
        with patch.object(self.risk_manager, '_check_position_limits', return_value=False):
            result = await self.risk_manager.validate_startup_conditions()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_assess_current_risk_no_action_needed(self):
        """GIVEN normal risk conditions
        WHEN assess_current_risk is called
        THEN should return status with no action required"""
        
        with patch.object(self.risk_manager, '_calculate_current_exposure', return_value=50000.0):
            with patch.object(self.risk_manager, '_calculate_daily_pnl', return_value=250.0):
                with patch.object(self.risk_manager, '_calculate_inventory_deviation', return_value=0.15):
                    risk_status = await self.risk_manager.assess_current_risk()
                    
                    assert risk_status.requires_action is False
                    assert risk_status.risk_level == "NORMAL"
    
    @pytest.mark.asyncio
    async def test_assess_current_risk_position_limit_exceeded(self):
        """GIVEN position limits exceeded
        WHEN assess_current_risk is called
        THEN should return status requiring action"""
        
        with patch.object(self.risk_manager, '_calculate_current_exposure', return_value=150000.0):  # Exceeds limit
            with patch.object(self.risk_manager, '_calculate_daily_pnl', return_value=250.0):
                with patch.object(self.risk_manager, '_calculate_inventory_deviation', return_value=0.15):
                    risk_status = await self.risk_manager.assess_current_risk()
                    
                    assert risk_status.requires_action is True
                    assert risk_status.event_type == "POSITION_LIMIT_EXCEEDED"
                    assert risk_status.risk_level == "HIGH"
    
    @pytest.mark.asyncio
    async def test_assess_current_risk_daily_loss_limit(self):
        """GIVEN daily loss limit exceeded
        WHEN assess_current_risk is called
        THEN should return status requiring immediate action"""
        
        with patch.object(self.risk_manager, '_calculate_current_exposure', return_value=50000.0):
            with patch.object(self.risk_manager, '_calculate_daily_pnl', return_value=-1500.0):  # Exceeds loss limit
                with patch.object(self.risk_manager, '_calculate_inventory_deviation', return_value=0.15):
                    risk_status = await self.risk_manager.assess_current_risk()
                    
                    assert risk_status.requires_action is True
                    assert risk_status.event_type == "DAILY_LOSS_LIMIT"
                    assert risk_status.risk_level == "CRITICAL"
    
    @pytest.mark.asyncio
    async def test_assess_current_risk_inventory_imbalance(self):
        """GIVEN inventory imbalance beyond limits
        WHEN assess_current_risk is called
        THEN should return status requiring rebalancing"""
        
        with patch.object(self.risk_manager, '_calculate_current_exposure', return_value=50000.0):
            with patch.object(self.risk_manager, '_calculate_daily_pnl', return_value=250.0):
                with patch.object(self.risk_manager, '_calculate_inventory_deviation', return_value=0.4):  # Exceeds limit
                    risk_status = await self.risk_manager.assess_current_risk()
                    
                    assert risk_status.requires_action is True
                    assert risk_status.event_type == "INVENTORY_IMBALANCE"
                    assert risk_status.risk_level == "MEDIUM"
    
    def test_get_pair_limits(self):
        """GIVEN trading pair
        WHEN get_pair_limits is called
        THEN should return appropriate risk limits"""
        
        trading_pair = "BTC/USDT"
        
        limits = self.risk_manager.get_pair_limits(trading_pair)
        
        assert limits.max_position_size <= self.mock_risk_limits.max_position_size
        assert limits.max_order_size > 0
        assert limits.min_spread > 0
    
    def test_calculate_position_size_normal_conditions(self):
        """GIVEN normal market conditions
        WHEN calculate_position_size is called
        THEN should return appropriate position size"""
        
        mock_market_data = Mock(spec=MarketData)
        mock_market_data.volatility = 0.03
        mock_market_data.liquidity = 5000.0
        
        mock_inventory = Mock(spec=InventoryState)
        mock_inventory.current_ratio = 0.5
        
        position_size = self.risk_manager.calculate_position_size(
            mock_market_data, mock_inventory, "BTC/USDT"
        )
        
        assert position_size > 0
        assert position_size <= self.mock_risk_limits.max_position_size
    
    def test_calculate_position_size_high_volatility(self):
        """GIVEN high volatility conditions
        WHEN calculate_position_size is called
        THEN should return reduced position size"""
        
        mock_market_data_normal = Mock(spec=MarketData)
        mock_market_data_normal.volatility = 0.03
        mock_market_data_normal.liquidity = 5000.0
        
        mock_market_data_volatile = Mock(spec=MarketData)
        mock_market_data_volatile.volatility = 0.08  # High volatility
        mock_market_data_volatile.liquidity = 5000.0
        
        mock_inventory = Mock(spec=InventoryState)
        mock_inventory.current_ratio = 0.5
        
        normal_size = self.risk_manager.calculate_position_size(
            mock_market_data_normal, mock_inventory, "BTC/USDT"
        )
        volatile_size = self.risk_manager.calculate_position_size(
            mock_market_data_volatile, mock_inventory, "BTC/USDT"
        )
        
        assert volatile_size < normal_size
```

### 4. Order Book Management and Spread Optimization Tests

#### OrderManager Unit Tests

```python
class TestOrderManager:
THEN should return increased spread"""
        
        mock_market_data_normal = Mock(spec=MarketData)
        mock_market_data_normal.volatility = 0.02
        mock_market_data_normal.liquidity = 5000.0
        mock_market_data_normal.current_spread = 0.001
        
        mock_market_data_volatile = Mock(spec=MarketData)
        mock_market_data_volatile.volatility = 0.08  # High volatility
        mock_market_data_volatile.liquidity = 5000.0
        mock_market_data_volatile.current_spread = 0.001
        
        normal_spread = self.order_manager.calculate_optimal_spread(mock_market_data_normal)
        volatile_spread = self.order_manager.calculate_optimal_spread(mock_market_data_volatile)
        
        assert volatile_spread > normal_spread
```

### 5. Performance Metrics and Profitability Tracking Tests

#### PerformanceTracker Unit Tests

```python
class TestPerformanceTracker:
    """Tests for performance tracking and metrics calculation"""
    
    def setup_method(self):
        """Setup performance tracker test environment"""
        self.performance_tracker = PerformanceTracker()
        
    def test_performance_tracker_initialization(self):
        """GIVEN new performance tracker
        WHEN initialized
        THEN should set up tracking structures"""
        
        assert hasattr(self.performance_tracker, 'trades')
        assert hasattr(self.performance_tracker, 'positions')
        assert hasattr(self.performance_tracker, 'daily_pnl')
        assert hasattr(self.performance_tracker, 'start_time')
        assert isinstance(self.performance_tracker.trades, list)
        assert isinstance(self.performance_tracker.positions, dict)
    
    def test_record_trade_success(self):
        """GIVEN completed trade
        WHEN record_trade is called
        THEN should track trade metrics"""
        
        mock_trade = Mock(spec=Trade)
        mock_trade.trade_id = "trade_001"
        mock_trade.trading_pair = "BTC/USDT"
        mock_trade.side = "BUY"
        mock_trade.size = 0.1
        mock_trade.price = 50000.0
        mock_trade.fee = 5.0
        mock_trade.pnl = 100.0
        mock_trade.executed_at = datetime.utcnow()
        
        self.performance_tracker.record_trade(mock_trade)
        
        assert len(self.performance_tracker.trades) == 1
        assert self.performance_tracker.trades[0] == mock_trade
    
    def test_update_metrics_single_position(self):
        """GIVEN single active position
        WHEN update_metrics is called
        THEN should calculate position metrics"""
        
        mock_position = Mock(spec=LiquidityPosition)
        mock_position.position_id = "pos_001"
        mock_position.trading_pair = "BTC/USDT"
        mock_position.unrealized_pnl = 250.0
        mock_position.realized_pnl = 150.0
        mock_position.total_volume = 10000.0
        mock_position.trade_count = 25
        
        positions = {"BTC/USDT": mock_position}
        
        self.performance_tracker.update_metrics(positions)
        
        assert "BTC/USDT" in self.performance_tracker.positions
        assert self.performance_tracker.positions["BTC/USDT"]["unrealized_pnl"] == 250.0
        assert self.performance_tracker.positions["BTC/USDT"]["realized_pnl"] == 150.0
    
    def test_update_metrics_multiple_positions(self):
        """GIVEN multiple active positions
        WHEN update_metrics is called
        THEN should aggregate metrics across positions"""
        
        mock_position_1 = Mock(spec=LiquidityPosition)
        mock_position_1.position_id = "pos_001"
        mock_position_1.trading_pair = "BTC/USDT"
        mock_position_1.unrealized_pnl = 250.0
        mock_position_1.realized_pnl = 150.0
        mock_position_1.total_volume = 10000.0
        mock_position_1.trade_count = 25
        
        mock_position_2 = Mock(spec=LiquidityPosition)
        mock_position_2.position_id = "pos_002"
        mock_position_2.trading_pair = "ETH/USDT"
        mock_position_2.unrealized_pnl = 180.0
        mock_position_2.realized_pnl = 120.0
        mock_position_2.total_volume = 8000.0
        mock_position_2.trade_count = 20
        
        positions = {
            "BTC/USDT": mock_position_1,
            "ETH/USDT": mock_position_2
        }
        
        self.performance_tracker.update_metrics(positions)
        
        assert len(self.performance_tracker.positions) == 2
        # Should track both positions separately
        assert self.performance_tracker.positions["BTC/USDT"]["unrealized_pnl"] == 250.0
        assert self.performance_tracker.positions["ETH/USDT"]["unrealized_pnl"] == 180.0
    
    def test_calculate_total_pnl(self):
        """GIVEN positions with realized and unrealized PnL
        WHEN calculate_total_pnl is called
        THEN should return combined PnL"""
        
        # Setup position data
        self.performance_tracker.positions = {
            "BTC/USDT": {
                "realized_pnl": 150.0,
                "unrealized_pnl": 250.0
            },
            "ETH/USDT": {
                "realized_pnl": 120.0,
                "unrealized_pnl": 180.0
            }
        }
        
        total_pnl = self.performance_tracker.calculate_total_pnl()
        
        # Total: (150 + 250) + (120 + 180) = 700
        assert total_pnl == 700.0
    
    def test_calculate_total_volume(self):
        """GIVEN positions with trading volume
        WHEN calculate_total_volume is called
        THEN should return aggregated volume"""
        
        self.performance_tracker.positions = {
            "BTC/USDT": {"total_volume": 10000.0},
            "ETH/USDT": {"total_volume": 8000.0}
        }
        
        total_volume = self.performance_tracker.calculate_total_volume()
        
        assert total_volume == 18000.0
    
    def test_calculate_win_rate(self):
        """GIVEN profitable and losing trades
        WHEN calculate_win_rate is called
        THEN should return correct win percentage"""
        
        # Setup trades with mixed results
        profitable_trade_1 = Mock(spec=Trade)
        profitable_trade_1.pnl = 100.0
        
        profitable_trade_2 = Mock(spec=Trade)
        profitable_trade_2.pnl = 50.0
        
        losing_trade = Mock(spec=Trade)
        losing_trade.pnl = -25.0
        
        self.performance_tracker.trades = [
            profitable_trade_1,
            profitable_trade_2,
            losing_trade
        ]
        
        win_rate = self.performance_tracker.calculate_win_rate()
        
        # 2 profitable out of 3 trades = 66.67%
        assert abs(win_rate - 66.67) < 0.01
    
    def test_calculate_win_rate_no_trades(self):
        """GIVEN no trades
        WHEN calculate_win_rate is called
        THEN should return 0"""
        
        win_rate = self.performance_tracker.calculate_win_rate()
        
        assert win_rate == 0.0
    
    def test_calculate_sharpe_ratio(self):
        """GIVEN daily returns data
        WHEN calculate_sharpe_ratio is called
        THEN should return risk-adjusted return metric"""
        
        # Setup daily PnL data
        self.performance_tracker.daily_pnl = [
            100.0, 150.0, -50.0, 200.0, 75.0,
            -25.0, 125.0, 180.0, -75.0, 90.0
        ]
        
        sharpe_ratio = self.performance_tracker.calculate_sharpe_ratio()
        
        # Should return a reasonable Sharpe ratio
        assert isinstance(sharpe_ratio, float)
        assert sharpe_ratio > 0  # Positive returns should yield positive Sharpe
    
    def test_calculate_max_drawdown(self):
        """GIVEN equity curve with drawdowns
        WHEN calculate_max_drawdown is called
        THEN should return maximum drawdown percentage"""
        
        # Setup equity curve with peak and trough
        self.performance_tracker.daily_pnl = [
            100.0, 150.0, 200.0,  # Peak at 450 cumulative
            -50.0, -100.0,        # Drawdown to 300
            75.0, 125.0           # Recovery
        ]
        
        max_drawdown = self.performance_tracker.calculate_max_drawdown()
        
        # Max drawdown: (450 - 300) / 450 = 33.33%
        assert abs(max_drawdown - 33.33) < 0.01
    
    def test_generate_summary(self):
        """GIVEN performance tracking data
        WHEN generate_summary is called
        THEN should return comprehensive performance summary"""
        
        # Setup test data
        self.performance_tracker.positions = {
            "BTC/USDT": {
                "realized_pnl": 150.0,
                "unrealized_pnl": 250.0,
                "total_volume": 10000.0,
                "trade_count": 25
            }
        }
        
        profitable_trade = Mock(spec=Trade)
        profitable_trade.pnl = 100.0
        losing_trade = Mock(spec=Trade)
        losing_trade.pnl = -25.0
        
        self.performance_tracker.trades = [profitable_trade, losing_trade]
        self.performance_tracker.daily_pnl = [100.0, -25.0, 75.0]
        
        summary = self.performance_tracker.generate_summary()
        
        assert "total_pnl" in summary
        assert "total_volume" in summary
        assert "total_trades" in summary
        assert "win_rate" in summary
        assert "sharpe_ratio" in summary
        assert "max_drawdown" in summary
        assert "active_positions" in summary
        
        assert summary["total_pnl"] == 400.0  # 150 + 250
        assert summary["total_volume"] == 10000.0
        assert summary["total_trades"] == 2
        assert summary["active_positions"] == 1
    
    def test_reset_daily_metrics(self):
        """GIVEN accumulated daily metrics
        WHEN reset_daily_metrics is called
        THEN should clear daily tracking data"""
        
        # Setup daily data
        self.performance_tracker.daily_pnl = [100.0, 150.0, -50.0]
        
        self.performance_tracker.reset_daily_metrics()
        
        assert len(self.performance_tracker.daily_pnl) == 0
```

### 6. Integration Tests for System Interactions

#### Market Making Integration Tests

```python
class TestMarketMakingIntegration:
    """Integration tests for market making system components"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.mock_config = Mock(spec=MarketMakingConfig)
        self.mock_wallet_provider = Mock(spec=WalletProvider)
        self.mock_event_bus = Mock(spec=EventBus)
        
        # Configure realistic test data
        self.mock_config.bot_id = "integration_test_bot"
        self.mock_config.exchanges = [Mock(spec=ExchangeConfig)]
        self.mock_config.monitoring_interval = 1  # Fast for testing
        self.mock_config.min_order_size = 10.0
        self.mock_config.max_order_size = 1000.0
        
    @pytest.mark.asyncio
    async def test_end_to_end_market_making_workflow(self):
        """GIVEN complete market making setup
        WHEN full workflow is executed
        THEN should coordinate all components successfully"""
        
        # Setup mocks for full workflow
        mock_exchange = Mock(spec=ExchangeClient)
        mock_exchange.exchange_id = "test_exchange"
        mock_exchange.validate_connection.return_value = True
        mock_exchange.supports_trading_pair.return_value = True
        mock_exchange.place_order.return_value = Mock(spec=Order)
        
        mock_strategy = Mock(spec=MarketMakingStrategy)
        mock_strategy.calculate_orders.return_value = [Mock(spec=OrderParameters)]
        mock_strategy.should_adapt.return_value = False
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        # Mock all dependencies
        with patch.object(bot, '_create_exchange_client', return_value=mock_exchange):
            with patch.object(bot, '_validate_trading_pair', return_value=True):
                with patch.object(bot.strategy_engine, 'create_strategy', return_value=mock_strategy):
                    with patch.object(bot.risk_manager, 'validate_startup_conditions', return_value=True):
                        with patch.object(bot.inventory_manager, 'assess_initial_inventory'):
                            with patch.object(bot, '_get_market_data', return_value=Mock()):
                                with patch.object(bot, '_validate_order_parameters', return_value=True):
                                    
                                    # Execute workflow
                                    await bot.initialize_exchanges()
                                    result = await bot.start_market_making(["BTC/USDT"])
                                    
                                    # Verify workflow completion
                                    assert result is True
                                    assert bot.is_active is True
                                    assert len(bot.active_positions) == 1
                                    assert "BTC/USDT" in bot.active_positions
                                    
                                    # Verify event emissions
                                    assert self.mock_event_bus.emit.call_count >= 2  # Exchange connected + market making started
    
    @pytest.mark.asyncio
    async def test_risk_event_handling_integration(self):
        """GIVEN risk limit violation
        WHEN risk event occurs
        THEN should coordinate risk response across components"""
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        bot.is_active = True
        
        # Setup risk event
        mock_risk_status = Mock(spec=RiskStatus)
        mock_risk_status.requires_action = True
        mock_risk_status.event_type = "POSITION_LIMIT_EXCEEDED"
        mock_risk_status.risk_level = "HIGH"
        mock_risk_status.action_taken = "REDUCE_POSITIONS"
        
        # Mock position with orders to cancel
        mock_position = Mock(spec=LiquidityPosition)
        mock_position.active_orders = [Mock(spec=Order), Mock(spec=Order)]
        bot.active_positions = {"BTC/USDT": mock_position}
        
        with patch.object(bot, '_reduce_position_sizes') as mock_reduce:
            await bot._handle_risk_event(mock_risk_status)
            
            # Verify risk response
            mock_reduce.assert_called_once()
            self.mock_event_bus.emit.assert_called()
    
    @pytest.mark.asyncio
    async def test_inventory_rebalancing_integration(self):
        """GIVEN inventory imbalance
        WHEN rebalancing is triggered
        THEN should coordinate rebalancing across components"""
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        # Setup inventory manager with rebalancing need
        mock_current_inventory = {
            "BTC/USDT": Mock(current_ratio=0.8, target_ratio=0.5)  # Imbalanced
        }
        mock_target_inventory = {
            "BTC/USDT": Mock(base_value=25000, quote_value=25000)
        }
        mock_rebalancing_trades = [
            Mock(spec=RebalancingTrade, trading_pair="BTC/USDT", side="SELL", size=0.5)
        ]
        
        bot.inventory_manager.get_current_inventory.return_value = mock_current_inventory
        bot.inventory_manager.calculate_target_inventory.return_value = mock_target_inventory
        bot.inventory_manager.calculate_rebalancing_trades.return_value = mock_rebalancing_trades
        bot.inventory_manager.update_inventory.return_value = None
        
        with patch.object(bot, '_execute_rebalancing_trade', return_value=Mock()) as mock_execute:
            await bot._rebalance_inventory()
            
            # Verify rebalancing execution
            mock_execute.assert_called_once()
            bot.inventory_manager.update_inventory.assert_called_once()
            self.mock_event_bus.emit.assert_called()
    
    @pytest.mark.asyncio
    async def test_strategy_adaptation_integration(self):
        """GIVEN changing market conditions
        WHEN strategy adaptation is triggered
        THEN should coordinate strategy updates across components"""
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        # Setup position with strategy that needs adaptation
        mock_strategy = Mock(spec=MarketMakingStrategy)
        mock_strategy.should_adapt.return_value = True
        mock_strategy.adapt_to_conditions.return_value = Mock(spec=StrategyParameters)
        
        mock_position = Mock(spec=LiquidityPosition)
        mock_position.trading_pair = "BTC/USDT"
        mock_position.strategy = mock_strategy
        mock_position.active_orders = [Mock(spec=Order), Mock(spec=Order)]
        
        mock_market_conditions = Mock(spec=MarketConditions)
        
        with patch.object(bot, '_assess_market_conditions', return_value=mock_market_conditions):
            with patch.object(bot, '_orders_need_adjustment', return_value=True):
                with patch.object(bot, '_adjust_orders') as mock_adjust:
                    await bot._adjust_position_strategy(mock_position)
                    
                    # Verify strategy adaptation
                    mock_strategy.should_adapt.assert_called_once_with(mock_market_conditions)
                    mock_strategy.adapt_to_conditions.assert_called_once_with(mock_market_conditions)
                    mock_adjust.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_order_fill_handling_integration(self):
        """GIVEN filled orders
        WHEN order fills are detected
        THEN should coordinate order replacement across components"""
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        # Setup position with filled orders
        mock_filled_order = Mock(spec=Order)
        mock_filled_order.order_id = "filled_order_1"
        mock_filled_order.filled_size = 100.0
        mock_filled_order.side = "BUY"
        
        mock_position = Mock(spec=LiquidityPosition)
        mock_position.trading_pair = "BTC/USDT"
        mock_position.active_orders = [mock_filled_order]
        
        mock_replacement_order = Mock(spec=Order)
        
        with patch.object(bot, '_check_filled_orders', return_value=[mock_filled_order]):
            with patch.object(bot, '_replace_filled_orders') as mock_replace:
                await bot._adjust_position_strategy(mock_position)
                
                # Verify order replacement
                mock_replace.assert_called_once_with(mock_position, [mock_filled_order])
```

## Test Execution Framework

### Pytest Configuration

```python
# conftest.py
import pytest
import asyncio
from unittest.mock import Mock
from datetime import datetime, timedelta
from src.market_making.bot import MarketMakingBot
from src.market_making.config import MarketMakingConfig

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_market_making_config():
    """Provide mock market making configuration for tests"""
    config = Mock(spec=MarketMakingConfig)
    config.bot_id = "test_bot"
    config.exchanges = []
    config.monitoring_interval = 5
    config.error_recovery_delay = 10
    config.min_order_size = 10.0
    config.max_order_size = 10000.0
    return config

@pytest.fixture
def mock_wallet_provider():
    """Provide mock wallet provider for tests"""
    return Mock()

@pytest.fixture
def mock_event_bus():
    """Provide mock event bus for tests"""
    return Mock()

@pytest.fixture
def market_making_bot(mock_market_making_config, mock_wallet_provider, mock_event_bus):
    """Provide configured market making bot for tests"""
    return MarketMakingBot(mock_market_making_config, mock_wallet_provider, mock_event_bus)

@pytest.fixture
def sample_market_data():
    """Provide sample market data for tests"""
    return {
        "mid_price": 50000.0,
        "bid_price": 49950.0,
        "ask_price": 50050.0,
        "spread": 100.0,
        "volatility": 0.03,
        "liquidity": 5000.0,
        "volume_24h": 1000000.0
    }

@pytest.fixture
def sample_order_parameters():
    """Provide sample order parameters for tests"""
    return [
        Mock(side="BUY", size=0.1, price=49900.0, order_type="LIMIT"),
        Mock(side="SELL", size=0.1, price=50100.0, order_type="LIMIT")
    ]
```

### Test Execution Commands

```bash
# Run all market making bot tests
pytest tests/test_market_making/ -v

# Run specific test categories
pytest tests/test_market_making/test_unit.py -v
pytest tests/test_market_making/test_integration.py -v
pytest tests/test_market_making/test_strategy.py -v
pytest tests/test_market_making/test_risk_management.py -v

# Run with coverage
pytest tests/test_market_making/ --cov=src.market_making --cov-report=html

# Run strategy tests
pytest tests/test_market_making/test_strategy.py -m strategy

# Run risk management tests
pytest tests/test_market_making/test_risk_management.py -m risk

# Run performance tests
pytest tests/test_market_making/test_performance.py -m performance
```

---

*This TDD specification provides comprehensive test coverage for the Market Making Bot System, ensuring robust validation of trading logic, strategy execution, risk management, order book management, and performance tracking for production-ready AI trading systems.*
    """Tests for order management and execution"""
    
    def setup_method(self):
        """Setup order manager test environment"""
        self.mock_config = Mock(spec=OrderConfig)
        self.mock_config.max_orders_per_side = 5
        self.mock_config.order_refresh_interval = 30
        self.mock_config.partial_fill_threshold = 0.1
        
        self.order_manager = OrderManager(self.mock_config)
    
    @pytest.mark.asyncio
    async def test_place_orders_success(self):
        """GIVEN valid order parameters
        WHEN place_orders is called
        THEN should place all orders successfully"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        mock_orders = [Mock(spec=Order) for _ in range(3)]
        mock_exchange.place_order.side_effect = mock_orders
        
        order_params = [
            Mock(spec=OrderParameters),
            Mock(spec=OrderParameters),
            Mock(spec=OrderParameters)
        ]
        
        results = await self.order_manager.place_orders(mock_exchange, order_params)
        
        assert len(results) == 3
        assert all(isinstance(order, Order) for order in results)
        assert mock_exchange.place_order.call_count == 3
    
    @pytest.mark.asyncio
    async def test_place_orders_partial_failure(self):
        """GIVEN some order placement failures
        WHEN place_orders is called
        THEN should handle failures gracefully"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        mock_order = Mock(spec=Order)
        
        # First order succeeds, second fails, third succeeds
        mock_exchange.place_order.side_effect = [
            mock_order,
            ExchangeError("Order failed"),
            mock_order
        ]
        
        order_params = [Mock(spec=OrderParameters) for _ in range(3)]
        
        with patch('logger.warning') as mock_logger:
            results = await self.order_manager.place_orders(mock_exchange, order_params)
            
            assert len(results) == 2  # Only successful orders
            mock_logger.assert_called()
    
    @pytest.mark.asyncio
    async def test_cancel_orders_success(self):
        """GIVEN active orders
        WHEN cancel_orders is called
        THEN should cancel all orders successfully"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        mock_exchange.cancel_order.return_value = True
        
        mock_orders = [
            Mock(spec=Order, order_id="order_1"),
            Mock(spec=Order, order_id="order_2"),
            Mock(spec=Order, order_id="order_3")
        ]
        
        results = await self.order_manager.cancel_orders(mock_exchange, mock_orders)
        
        assert len(results) == 3
        assert all(result is True for result in results)
        assert mock_exchange.cancel_order.call_count == 3
    
    @pytest.mark.asyncio
    async def test_cancel_orders_partial_failure(self):
        """GIVEN some cancellation failures
        WHEN cancel_orders is called
        THEN should handle failures gracefully"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        
        # First cancellation succeeds, second fails, third succeeds
        mock_exchange.cancel_order.side_effect = [
            True,
            ExchangeError("Cancel failed"),
            True
        ]
        
        mock_orders = [Mock(spec=Order) for _ in range(3)]
        
        with patch('logger.warning') as mock_logger:
            results = await self.order_manager.cancel_orders(mock_exchange, mock_orders)
            
            # Should return results for all attempts
            assert len(results) == 3
            mock_logger.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_order_fills_no_fills(self):
        """GIVEN orders with no fills
        WHEN check_order_fills is called
        THEN should return empty list"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        
        mock_orders = [
            Mock(spec=Order, order_id="order_1", filled_size=0, size=100),
            Mock(spec=Order, order_id="order_2", filled_size=0, size=200)
        ]
        
        mock_exchange.get_order_status.side_effect = [
            {"filled_size": 0, "status": "OPEN"},
            {"filled_size": 0, "status": "OPEN"}
        ]
        
        filled_orders = await self.order_manager.check_order_fills(mock_exchange, mock_orders)
        
        assert len(filled_orders) == 0
    
    @pytest.mark.asyncio
    async def test_check_order_fills_with_fills(self):
        """GIVEN orders with fills
        WHEN check_order_fills is called
        THEN should return filled orders"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        
        mock_orders = [
            Mock(spec=Order, order_id="order_1", filled_size=0, size=100),
            Mock(spec=Order, order_id="order_2", filled_size=0, size=200)
        ]
        
        mock_exchange.get_order_status.side_effect = [
            {"filled_size": 100, "status": "FILLED"},  # Fully filled
            {"filled_size": 50, "status": "PARTIALLY_FILLED"}  # Partially filled
        ]
        
        filled_orders = await self.order_manager.check_order_fills(mock_exchange, mock_orders)
        
        assert len(filled_orders) == 2
        assert filled_orders[0].filled_size == 100
        assert filled_orders[1].filled_size == 50
    
    @pytest.mark.asyncio
    async def test_check_order_fills_significant_partial_fill(self):
        """GIVEN order with significant partial fill
        WHEN check_order_fills is called
        THEN should include in filled orders"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        
        mock_order = Mock(spec=Order, order_id="order_1", filled_size=0, size=100)
        
        # 50% filled - above threshold
        mock_exchange.get_order_status.return_value = {
            "filled_size": 50, 
            "status": "PARTIALLY_FILLED"
        }
        
        filled_orders = await self.order_manager.check_order_fills(mock_exchange, [mock_order])
        
        assert len(filled_orders) == 1
        assert filled_orders[0].filled_size == 50
    
    @pytest.mark.asyncio
    async def test_check_order_fills_insignificant_partial_fill(self):
        """GIVEN order with insignificant partial fill
        WHEN check_order_fills is called
        THEN should not include in filled orders"""
        
        mock_exchange = Mock(spec=ExchangeClient)
        
        mock_order = Mock(spec=Order, order_id="order_1", filled_size=0, size=100)
        
        # 5% filled - below threshold
        mock_exchange.get_order_status.return_value = {
            "filled_size": 5, 
            "status": "PARTIALLY_FILLED"
        }
        
        filled_orders = await self.order_manager.check_order_fills(mock_exchange, [mock_order])
        
        assert len(filled_orders) == 0
    
    def test_should_refresh_orders_time_based(self):
        """GIVEN orders older than refresh interval
        WHEN should_refresh_orders is called
        THEN should return True"""
        
        old_time = datetime.utcnow() - timedelta(seconds=60)  # 60 seconds ago
        
        mock_orders = [
            Mock(spec=Order, created_at=old_time),
            Mock(spec=Order, created_at=old_time)
        ]
        
        result = self.order_manager.should_refresh_orders(mock_orders)
        
        assert result is True
    
    def test_should_refresh_orders_recent(self):
        """GIVEN recent orders
        WHEN should_refresh_orders is called
        THEN should return False"""
        
        recent_time = datetime.utcnow() - timedelta(seconds=10)  # 10 seconds ago
        
        mock_orders = [
            Mock(spec=Order, created_at=recent_time),
            Mock(spec=Order, created_at=recent_time)
        ]
        
        result = self.order_manager.should_refresh_orders(mock_orders)
        
        assert result is False
    
    def test_calculate_optimal_spread_normal_conditions(self):
        """GIVEN normal market conditions
        WHEN calculate_optimal_spread is called
        THEN should return base spread"""
        
        mock_market_data = Mock(spec=MarketData)
        mock_market_data.volatility = 0.02
        mock_market_data.liquidity = 5000.0
        mock_market_data.current_spread = 0.001
        
        spread = self.order_manager.calculate_optimal_spread(mock_market_data)
        
        assert spread > mock_market_data.current_spread
        assert spread < 0.01  # Reasonable upper bound
    
    def test_calculate_optimal_spread_high_volatility(self):
        """GIVEN high volatility conditions
        WHEN calculate_optimal_spread is called
        
        assert result is True
    
    def test_validate_trading_pair_invalid_format(self):
        """GIVEN invalid trading pair format
        WHEN _validate_trading_pair is called
        THEN should return False"""
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        result = bot._validate_trading_pair("invalid_pair")
        
        assert result is False
    
    def test_validate_order_parameters_valid(self):
        """GIVEN valid order parameters
        WHEN _validate_order_parameters is called
        THEN should return True"""
        
        mock_order_param = Mock(spec=OrderParameters)
        mock_order_param.size = 100.0
        mock_order_param.price = 50000.0
        
        self.mock_config.min_order_size = 10.0
        self.mock_config.max_order_size = 10000.0
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        result = bot._validate_order_parameters(mock_order_param)
        
        assert result is True
    
    def test_validate_order_parameters_invalid_size(self):
        """GIVEN order parameters with invalid size
        WHEN _validate_order_parameters is called
        THEN should return False"""
        
        mock_order_param = Mock(spec=OrderParameters)
        mock_order_param.size = 0  # Invalid size
        mock_order_param.price = 50000.0
        
        bot = MarketMakingBot(self.mock_config, self.mock_wallet_provider, self.mock_event_bus)
        
        result = bot._validate_order_parameters(mock_order_param)
        
        assert result is False