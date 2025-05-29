# Phase 3: Advanced AI Capabilities - TDD Anchor Specifications

## Overview

This document provides comprehensive Test-Driven Development (TDD) anchor specifications for all Phase 3 Advanced AI Capabilities components, ensuring complete test coverage and validation of AI-driven trading functionality.

## Testing Strategy

### Test Categories
1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: Component interaction and data flow
3. **Performance Tests**: Latency, throughput, and scalability
4. **Security Tests**: Input validation and attack prevention
5. **AI Model Tests**: Prediction accuracy and confidence validation
6. **End-to-End Tests**: Complete workflow validation

### Test Data Management
- **Mock Data**: Synthetic market data for predictable testing
- **Historical Data**: Real market data for backtesting
- **Live Data**: Real-time data for integration testing
- **Edge Case Data**: Extreme scenarios and error conditions

## Predictive Models System - TDD Anchors

### Core Test Requirements

```python
class TestPredictiveModelsManager:
    """Comprehensive test suite for PredictiveModelsManager"""
    
    def test_manager_initialization_with_valid_config(self):
        """TEST: Manager initializes with valid configuration"""
        config = create_valid_predictive_config()
        manager = PredictiveModelsManager(config, mock_event_bus)
        
        assert manager.config == config
        assert manager.engines == {}
        assert manager.cache is not None
        assert manager.performance_tracker is not None
    
    def test_engine_initialization_success(self):
        """TEST: All configured engines initialize successfully"""
        manager = create_test_manager()
        
        with patch_engine_connections(success=True):
            result = await manager.initialize_engines()
            
        assert result is True
        assert len(manager.engines) == len(manager.config.engines)
    
    def test_token_success_prediction_valid_request(self):
        """TEST: Token success prediction with valid request"""
        manager = create_initialized_manager()
        request = create_valid_prediction_request()
        
        result = await manager.predict_token_success(request)
        
        assert isinstance(result, PredictionResult)
        assert 0 <= result.confidence <= 100
        assert 0 <= result.prediction.success_probability <= 100
    
    def test_prediction_cache_hit_returns_cached_result(self):
        """TEST: Cache hit returns cached result within TTL"""
        manager = create_initialized_manager()
        request = create_valid_prediction_request()
        
        # First prediction
        result1 = await manager.predict_token_success(request)
        
        # Second prediction should hit cache
        with patch_engine_calls() as mock_engines:
            result2 = await manager.predict_token_success(request)
            
        assert result1.result_id == result2.result_id
        assert not mock_engines.called
    
    def test_prediction_aggregation_with_multiple_engines(self):
        """TEST: Prediction aggregation handles multiple engines"""
        manager = create_manager_with_multiple_engines()
        request = create_valid_prediction_request()
        
        with patch_multiple_engine_responses():
            result = await manager.predict_token_success(request)
            
        assert result.engine_id == "ensemble"
        assert len(result.metadata.data_sources) > 1
    
    def test_insufficient_predictions_error(self):
        """TEST: Ensemble aggregation requires minimum predictions"""
        manager = create_initialized_manager()
        request = create_valid_prediction_request()
        
        with patch_all_engines_fail():
            with pytest.raises(InsufficientPredictionsError):
                await manager.predict_token_success(request)
    
    def test_market_trend_analysis_valid_input(self):
        """TEST: Market trend analysis with valid inputs"""
        manager = create_initialized_manager()
        token_address = "0x1234567890123456789012345678901234567890"
        timeframes = ["1h", "4h", "1d"]
        
        result = await manager.analyze_market_trends(token_address, timeframes)
        
        assert isinstance(result, TrendAnalysis)
        assert result.token_address == token_address
        assert len(result.timeframe_analysis) == len(timeframes)
    
    def test_risk_assessment_valid_portfolio(self):
        """TEST: Risk assessment with valid portfolio data"""
        manager = create_initialized_manager()
        portfolio_data = create_valid_portfolio_data()
        position_size = 10000.0
        
        result = await manager.assess_risk(portfolio_data, position_size)
        
        assert isinstance(result, RiskAssessment)
        assert result.optimal_position_size > 0
        assert 0 <= result.risk_score <= 1

class TestAPIBasedEngine:
    """Test suite for API-based prediction engines"""
    
    def test_api_prediction_success(self):
        """TEST: API prediction with successful response"""
        engine = create_test_api_engine()
        request = create_valid_prediction_request()
        
        with patch_api_success_response():
            result = await engine.predict(request)
            
        assert isinstance(result, PredictionResult)
        assert result.engine_id == engine.engine_id
        assert result.confidence > 0
    
    def test_api_rate_limiting_compliance(self):
        """TEST: Rate limiting prevents API abuse"""
        engine = create_test_api_engine()
        requests = [create_valid_prediction_request() for _ in range(10)]
        
        start_time = time.time()
        for request in requests:
            await engine.predict(request)
        elapsed_time = time.time() - start_time
        
        expected_min_time = len(requests) / engine.rate_limiter.max_rate
        assert elapsed_time >= expected_min_time
    
    def test_api_timeout_handling(self):
        """TEST: API timeout handling with appropriate error"""
        engine = create_test_api_engine()
        request = create_valid_prediction_request()
        
        with patch_api_timeout():
            with pytest.raises(PredictionTimeoutError):
                await engine.predict(request)

class TestLocalModelEngine:
    """Test suite for local ML model engines"""
    
    def test_local_prediction_success(self):
        """TEST: Local model prediction with valid input"""
        engine = create_test_local_engine()
        request = create_valid_prediction_request()
        
        result = await engine.predict(request)
        
        assert isinstance(result, PredictionResult)
        assert result.engine_id == engine.engine_id
        assert result.metadata.model_version is not None
    
    def test_feature_extraction_validation(self):
        """TEST: Feature extraction from request"""
        engine = create_test_local_engine()
        request = create_valid_prediction_request()
        
        features = await engine.feature_extractor.extract_features(request)
        
        assert features is not None
        assert len(features) > 0
        assert all(isinstance(f, (int, float)) for f in features)
```

## Sentiment Integration Engine - TDD Anchors

### Core Test Requirements

```python
class TestSentimentIntegrationEngine:
    """Test suite for SentimentIntegrationEngine"""
    
    def test_engine_initialization_with_sources(self):
        """TEST: Engine initializes with valid configuration"""
        config = create_sentiment_config()
        engine = SentimentIntegrationEngine(config, mock_event_bus)
        
        assert engine.config == config
        assert engine.sources == {}
        assert engine.analyzers == {}
        assert engine.spam_filter is not None
    
    def test_source_initialization_success(self):
        """TEST: All configured sources initialize successfully"""
        engine = create_test_sentiment_engine()
        
        with patch_source_connections(success=True):
            result = engine.initialize_sources()
            
        assert result is True
        assert len(engine.sources) == len(engine.config.sources)
    
    def test_token_sentiment_analysis_valid_token(self):
        """TEST: Sentiment analysis for valid token"""
        engine = create_initialized_sentiment_engine()
        token_address = "0x1234567890123456789012345678901234567890"
        
        with patch_sentiment_data_collection():
            result = await engine.analyze_token_sentiment(token_address)
            
        assert isinstance(result, SentimentAnalysis)
        assert result.token_address == token_address
        assert -1 <= result.aggregated_sentiment <= 1
        assert result.trend is not None
    
    def test_sentiment_cache_functionality(self):
        """TEST: Cache check for recent analysis"""
        engine = create_initialized_sentiment_engine()
        token_address = "0x1234567890123456789012345678901234567890"
        
        # First analysis
        result1 = await engine.analyze_token_sentiment(token_address)
        
        # Second analysis should hit cache
        with patch_sentiment_collection() as mock_collection:
            result2 = await engine.analyze_token_sentiment(token_address)
            
        assert result1.analysis_id == result2.analysis_id
        assert not mock_collection.called
    
    def test_spam_filtering_removes_low_quality_content(self):
        """TEST: Spam filtering removes low-quality content"""
        engine = create_initialized_sentiment_engine()
        
        raw_data = create_mixed_quality_sentiment_data()
        filtered_data = await engine.spam_filter.filter_data(raw_data)
        
        assert len(filtered_data) < len(raw_data)
        assert all(data.quality_score > engine.config.min_quality_threshold 
                  for data in filtered_data)
    
    def test_viral_content_detection(self):
        """TEST: Viral content detection across platforms"""
        engine = create_initialized_sentiment_engine()
        
        with patch_viral_content_sources():
            viral_content = await engine.monitor_viral_content()
            
        assert isinstance(viral_content, list)
        assert all(isinstance(content, ViralContent) for content in viral_content)
        assert all(content.virality_score > 0 for content in viral_content)
    
    def test_influencer_activity_tracking(self):
        """TEST: Influencer activity tracking with valid IDs"""
        engine = create_initialized_sentiment_engine()
        influencer_ids = ["influencer1", "influencer2", "influencer3"]
        
        with patch_influencer_data():
            activities = await engine.track_influencer_activity(influencer_ids)
            
        assert isinstance(activities, list)
        assert all(isinstance(activity, InfluencerActivity) for activity in activities)
        assert all(activity.impact_score >= 0 for activity in activities)
    
    def test_crypto_relevance_detection(self):
        """TEST: Crypto relevance detection using keywords and patterns"""
        engine = create_initialized_sentiment_engine()
        
        crypto_content = "Bitcoin is pumping! $BTC to the moon 🚀"
        non_crypto_content = "I love pizza and movies"
        
        assert engine._is_crypto_relevant(crypto_content) is True
        assert engine._is_crypto_relevant(non_crypto_content) is False

class TestTwitterSentimentSource:
    """Test suite for Twitter sentiment data collection"""
    
    def test_twitter_data_collection_success(self):
        """TEST: Twitter data collection with valid query"""
        source = create_test_twitter_source()
        query = "bitcoin OR $BTC"
        
        with patch_twitter_api_success():
            data = await source.collect_data(query, "1h", 100)
            
        assert isinstance(data, list)
        assert len(data) <= 100
        assert all(isinstance(item, RawSentimentData) for item in data)
    
    def test_twitter_rate_limiting(self):
        """TEST: Rate limiting prevents API abuse"""
        source = create_test_twitter_source()
        
        start_time = time.time()
        for _ in range(5):
            await source.rate_limiter.acquire()
        elapsed_time = time.time() - start_time
        
        assert elapsed_time >= source.rate_limiter.min_interval * 4
    
    def test_viral_content_detection_twitter(self):
        """TEST: Viral content detection with trending topics"""
        source = create_test_twitter_source()
        
        with patch_twitter_trending_topics():
            viral_candidates = await source.detect_viral_content(24)
            
        assert isinstance(viral_candidates, list)
        assert all(candidate.platform == "twitter" for candidate in viral_candidates)
```

## Market Making Bot - TDD Anchors

### Core Test Requirements

```python
class TestMarketMakingBot:
    """Test suite for MarketMakingBot"""
    
    def test_bot_initialization_with_config(self):
        """TEST: Bot initializes with valid configuration"""
        config = create_market_making_config()
        bot = MarketMakingBot(config, mock_wallet_provider, mock_event_bus)
        
        assert bot.config == config
        assert bot.bot_id == config.bot_id
        assert bot.strategy_engine is not None
        assert bot.inventory_manager is not None
        assert bot.risk_manager is not None
    
    def test_exchange_initialization_success(self):
        """TEST: All configured exchanges initialize successfully"""
        bot = create_test_market_making_bot()
        
        with patch_exchange_connections(success=True):
            result = await bot.initialize_exchanges()
            
        assert result is True
        assert len(bot.exchanges) == len(bot.config.exchanges)
    
    def test_market_making_startup_success(self):
        """TEST: Market making starts successfully with valid pairs"""
        bot = create_initialized_bot()
        trading_pairs = ["ETH/USDC", "BTC/USDT"]
        
        with patch_market_data_and_orders():
            result = await bot.start_market_making(trading_pairs)
            
        assert result is True
        assert bot.is_active is True
        assert len(bot.active_positions) == len(trading_pairs)
    
    def test_trading_pairs_validation(self):
        """TEST: Trading pairs validation rejects invalid inputs"""
        bot = create_initialized_bot()
        invalid_pairs = ["INVALID", "ETH-USDC", ""]
        
        with pytest.raises(InvalidTradingPairsError):
            await bot.start_market_making(invalid_pairs)
    
    def test_risk_limits_validation_before_startup(self):
        """TEST: Risk limits validation before starting"""
        bot = create_initialized_bot()
        trading_pairs = ["ETH/USDC"]
        
        with patch_risk_limit_violation():
            with pytest.raises(RiskLimitViolationError):
                await bot.start_market_making(trading_pairs)
    
    def test_initial_order_placement(self):
        """TEST: Initial order placement for position"""
        bot = create_initialized_bot()
        position = create_test_liquidity_position()
        
        with patch_market_data_and_strategy():
            await bot._place_initial_orders(position)
            
        assert len(position.active_orders) > 0
        assert all(order.position_id == position.position_id 
                  for order in position.active_orders)
    
    def test_order_adjustment_based_on_market_conditions(self):
        """TEST: Order adjustment if needed"""
        bot = create_active_bot()
        position = create_position_with_orders()
        
        with patch_changed_market_conditions():
            await bot._adjust_position_strategy(position)
            
        assert len(position.active_orders) > 0
    
    def test_inventory_rebalancing_execution(self):
        """TEST: Inventory rebalancing when needed"""
        bot = create_active_bot()
        
        with patch_inventory_imbalance():
            await bot._rebalance_inventory()
            
        assert bot.inventory_manager.last_rebalance is not None
    
    def test_risk_event_handling(self):
        """TEST: Risk event handling and appropriate action"""
        bot = create_active_bot()
        risk_status = create_risk_event("POSITION_LIMIT_EXCEEDED")
        
        await bot._handle_risk_event(risk_status)
        
        assert risk_status.action_taken is not None
    
    def test_graceful_shutdown_process(self):
        """TEST: Graceful shutdown process"""
        bot = create_active_bot()
        
        result = await bot.stop_market_making()
        
        assert result is True
        assert bot.is_active is False
        assert all(len(pos.active_orders) == 0 
                  for pos in bot.active_positions.values())

class TestStrategyEngine:
    """Test suite for StrategyEngine"""
    
    def test_strategy_creation_for_trading_pair(self):
        """TEST: Strategy creation with optimized parameters"""
        engine = create_test_strategy_engine()
        trading_pair = "ETH/USDC"
        
        with patch_market_analysis():
            strategy = await engine.create_strategy(trading_pair)
            
        assert isinstance(strategy, MarketMakingStrategy)
        assert strategy.trading_pair == trading_pair
        assert strategy.validate_parameters() is True
    
    def test_strategy_type_selection_logic(self):
        """TEST: Strategy selection logic"""
        engine = create_test_strategy_engine()
        
        # High volatility market
        high_vol_analysis = create_market_analysis(volatility=0.1)
        strategy_type = engine._select_strategy_type(high_vol_analysis)
        assert strategy_type == "VOLATILITY_ADAPTIVE"
        
        # Low liquidity market
        low_liq_analysis = create_market_analysis(liquidity=500)
        strategy_type = engine._select_strategy_type(low_liq_analysis)
        assert strategy_type == "INVENTORY_BASED"

class TestInventoryManager:
    """Test suite for InventoryManager"""
    
    def test_initial_inventory_assessment(self):
        """TEST: Initial inventory assessment"""
        manager = create_test_inventory_manager()
        trading_pairs = ["ETH/USDC", "BTC/USDT"]
        
        with patch_asset_balances():
            await manager.assess_initial_inventory(trading_pairs)
            
        assert len(manager.current_inventory) == len(trading_pairs)
        assert all(0 <= inv.current_ratio <= 1 
                  for inv in manager.current_inventory.values())
    
    def test_rebalancing_need_assessment(self):
        """TEST: Rebalancing need assessment"""
        manager = create_inventory_manager_with_imbalance()
        
        needs_rebalancing = await manager.needs_rebalancing()
        
        assert needs_rebalancing is True
    
    def test_rebalancing_trade_calculation(self):
        """TEST: Rebalancing trade calculation"""
        manager = create_test_inventory_manager()
        current_inventory = create_imbalanced_inventory()
        target_inventory = create_target_inventory()
        
        trades = manager.calculate_rebalancing_trades(current_inventory, target_inventory)
        
        assert isinstance(trades, list)
        assert all(isinstance(trade, RebalancingTrade) for trade in trades)
        assert all(trade.size > manager.config.min_trade_value for trade in trades)
```

## Flash Loan Strategies - TDD Anchors

### Core Test Requirements

```python
class TestFlashLoanStrategiesEngine:
    """Test suite for FlashLoanStrategiesEngine"""
    
    def test_engine_initialization_with_providers(self):
        """TEST: Engine initializes with valid configuration"""
        config = create_flash_loan_config()
        engine = FlashLoanStrategiesEngine(config, mock_wallet_provider, mock_event_bus)
        
        assert engine.config == config
        assert engine.opportunity_scanner is not None
        assert engine.strategy_executor is not None
        assert engine.mev_optimizer is not None
    
    def test_provider_initialization_success(self):
        """TEST: All configured providers initialize successfully"""
        engine = create_test_flash_loan_engine()
        
        with patch_provider_connections(success=True):
            result = await engine.initialize_providers()
            
        assert result is True
        assert len(engine.flash_loan_providers) == len(engine.config.providers)
    
    def test_opportunity_scanning_startup(self):
        """TEST: Opportunity scanning startup validation"""
        engine = create_initialized_flash_loan_engine()
        
        result = await engine.start_opportunity_scanning()
        
        assert result is True
        assert engine.is_active is True
    
    def test_opportunity_validation_checks(self):
        """TEST: Opportunity validation before execution"""
        engine = create_initialized_flash_loan_engine()
        
        valid_opportunity = create_valid_arbitrage_opportunity()
        invalid_opportunity = create_invalid_arbitrage_opportunity()
        
        assert await engine._validate_opportunity(valid_opportunity) is True
        assert await engine._validate_opportunity(invalid_opportunity) is False
    
    def test_flash_loan_execution_success(self):
        """TEST: Flash loan execution with successful result"""
        engine = create_initialized_flash_loan_engine()
        opportunity = create_profitable_opportunity()
        
        with patch_successful_execution():
            execution = await engine._execute_flash_loan_strategy(opportunity)
            
        assert execution.status == "SUCCESS"
        assert execution.profit > 0
        assert execution.transaction_hash is not None
    
    def test_gas_cost_validation(self):
        """TEST: Gas estimation and validation"""
        engine = create_initialized_flash_loan_engine()
        opportunity = create_high_gas_opportunity()
        
        with pytest.raises(GasCostTooHighError):
            await engine._execute_flash_loan_strategy(opportunity)
    
    def test_transaction_simulation_validation(self):
        """TEST: Transaction simulation to verify profitability"""
        engine = create_initialized_flash_loan_engine()
        transaction = create_test_flash_loan_transaction()
        
        with patch_simulation_success():
            result = await engine._simulate_transaction(transaction)
            
        assert result.success is True
        assert result.profit > 0
    
    def test_mev_protection_application(self):
        """TEST: MEV protection application"""
        engine = create_initialized_flash_loan_engine()
        strategy = create_test_execution_strategy()
        
        protected_strategy = await engine.mev_optimizer.apply_protection(strategy)
        
        assert protected_strategy.submission_method in ["PRIVATE_MEMPOOL", "BUNDLE_SUBMISSION"]
        assert protected_strategy != strategy
    
    def test_provider_selection_optimization(self):
        """TEST: Optimal provider selection for opportunity"""
        engine = create_engine_with_multiple_providers()
        opportunity = create_arbitrage_opportunity()
        
        optimal_provider = await engine._select_optimal_provider(opportunity)
        
        assert optimal_provider is not None
        assert optimal_provider.max_loan_amount >= opportunity.required_capital
    
    def test_opportunity_prioritization_logic(self):
        """TEST: Opportunity prioritization by profit potential and confidence"""
        engine = create_initialized_flash_loan_engine()
        opportunities = create_mixed_opportunities()
        
        prioritized = engine._prioritize_opportunities(opportunities)
        
        assert len(prioritized) == len(opportunities)
        assert prioritized[0].estimated_profit >= prioritized[-1].estimated_profit

class TestOpportunityScanner:
    """Test suite for OpportunityScanner"""
    
    def test_dex_arbitrage_scanning(self):
        """TEST: DEX arbitrage scanning"""
        scanner = create_initialized_scanner()
        
        with patch_dex_price_differences():
            opportunities = await scanner._scan_dex_arbitrage()
            
        assert isinstance(opportunities, list)
        assert all(isinstance(opp, ArbitrageOpportunity) for opp in opportunities)
        assert all(opp.estimated_profit > 0 for opp in opportunities)
    
    def test_liquidation_opportunity_scanning(self):
        """TEST: Liquidation opportunity scanning across lending protocols"""
        scanner = create_initialized_scanner()
        
        with patch_liquidatable_positions():
            opportunities = await scanner._scan_liquidations()
            
        assert isinstance(opportunities, list)
        assert all(opp.opportunity_type == "LIQUIDATION" for opp in opportunities)
    
    def test_price_comparison_across_dexes(self):
        """TEST: Price comparison across DEXes"""
        scanner = create_initialized_scanner()
        token_pair = "ETH/USDC"
        
        with patch_multiple_dex_prices():
            prices = {}
            for protocol in scanner.protocols.values():
                if protocol.supports_pair(token_pair):
                    price = await protocol.get_price(token_pair)
                    prices[protocol.protocol_id] = price
                    
        assert len(prices) >= 2
        assert all(price > 0 for price in prices.values())

class TestMEVOptimizer:
    """Test suite for MEVOptimizer"""
    
    def test_protection_method_selection(self):
        """TEST: Protection method selection"""
        optimizer = create_test_mev_optimizer()
        
        high_complexity_strategy = create_strategy(complexity=8)
        high_value_strategy = create_strategy(value=100000)
        
        assert optimizer._select_protection_method(high_complexity_strategy) == "BUNDLE_SUBMISSION"
        assert optimizer._select_protection_method(high_value_strategy) == "PRIVATE_MEMPOOL"
    
    def test_private_mempool_protection(self):
        """TEST: Private mempool protection application"""
        optimizer = create_test_mev_optimizer()
        strategy = create_test_execution_strategy()
        
        protected = await optimizer._apply_private_mempool_protection(strategy)
        
        assert protected.submission_method == "PRIVATE_MEMPOOL"
        assert protected.mempool_endpoint is not None
```

## Performance Testing Specifications

### Latency Requirements

```python
class TestPerformanceRequirements:
    """Performance testing for AI components"""
    
    @pytest.mark.performance
    def test_prediction_latency_under_threshold(self):
        """TEST: Prediction latency meets requirements"""
        manager = create_production_manager()
        request = create_standard_prediction_request()
        
        start_time = time.time()
        result = await manager.predict_token_success(request)
        latency = time.time() - start_time
        
        assert latency < 5.0  # 5 second max latency
        assert result.confidence > 0.7
    
    @pytest.mark.performance
    def test_sentiment_analysis_throughput(self):
        """TEST: Sentiment analysis throughput requirements"""
        engine = create_production_sentiment_engine()
        
        start_time = time.time()
        tasks = []
        for _ in range(100):
            task = engine.analyze_token_sentiment(create_random_token_address())
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time
        throughput = len(results) / elapsed_time
        
        assert throughput >= 10  # 10 analyses per second minimum
        assert all(isinstance(r, SentimentAnalysis) for r in results)
    
    @pytest.mark.performance
    def test_market_making_order_latency(self):
        """TEST: Market making order placement latency"""
        bot = create_production_market_making_bot()
        position = create_test_position()
        
        start_time = time.time()
        await bot._place_initial_orders(position)
        latency = time.time() - start_time
        
        assert latency < 1.0  # 1 second max for order placement
        assert len(position.active_orders) > 0
    
    @pytest.mark.performance
    def test_flash_loan_opportunity_detection_speed(self):
        """TEST: Flash loan opportunity detection speed"""
        scanner = create_production_scanner()
        
        start_time = time.time()
        opportunities = await scanner.scan_opportunities()
        detection_time = time.time() - start_time
        
        assert detection_time < 2.0  # 2 second max for full scan
        assert isinstance(opportunities, list)
```

## Security Testing Specifications

### Input Validation and Attack Prevention

```python
class TestSecurityRequirements:
    """Security testing for AI components"""
    
    def test_prediction_request_input_validation(self):
        """TEST: Prediction request input validation"""
        manager = create_test_manager()
        
        # Test SQL injection attempt
        malicious_request = create_prediction_request_with_sql_injection()
        with pytest.raises(InvalidTokenAddressError):
            await manager.predict_token_success(malicious_request)
        
        # Test XSS attempt
        xss_request = create_prediction_request_with_xss()
        with pytest.raises(InvalidTokenAddressError):
            await manager.predict_token_success(xss_request)
    
    def test_sentiment_data_sanitization(self):
        """TEST: Sentiment data sanitization"""
        engine = create_test_sentiment_engine()
        
        malicious_content = create_malicious_sentiment_data()
        sanitized_content = engine.spam_filter.sanitize_content(malicious_content)
        
        assert "<script>" not in sanitized_content
        assert "javascript:" not in sanitized_content
        assert len(sanitized_content) <= engine.config.max_content_length
    
    def test_flash_loan_transaction_validation(self):
        """TEST: Flash loan transaction validation"""
        engine = create_test_flash_loan_engine()
        
        # Test malicious transaction
        malicious_transaction = create_malicious_flash_loan_transaction()
        
        with pytest.raises(InvalidTransactionError):
            await engine._validate_transaction(malicious_transaction)
    
    def test_api_rate_limiting_protection(self):
        """TEST: API rate limiting protection"""
        engine = create_test_api_engine()
        
        # Attempt to exceed rate limits
        requests = [create_valid_prediction_request() for _ in range(1000)]
        
        start_time = time.time()
        successful_requests = 0
        
        for request in requests:
            try:
                await engine.predict(request)
                successful_requests += 1
            except PredictionRateLimitError:
                break
        
        elapsed_time = time.time() - start_time
        rate = successful_requests / elapsed_time
        
        assert rate <= engine.rate_limiter.max_rate * 1.1  # Allow 10% tolerance
```

## Integration Testing Specifications

### End-to-End Workflow Testing

```python
class TestIntegrationWorkflows:
    """Integration testing for complete AI workflows"""
    
    @pytest.mark.integration
    def test_complete_prediction_to_trading_workflow(self):
        """TEST: Complete workflow from prediction to trade execution"""
        # Initialize all components
        prediction_manager = create_production_prediction_manager()
        sentiment_engine = create_production_sentiment_engine()
