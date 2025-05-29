# Phase 2: DeFi Instruments Manager - Pseudocode Specification

## Overview

This module implements the DeFi Instruments Manager with automated yield farming optimization, liquidity provision management, cross-protocol yield aggregation, and impermanent loss protection strategies.

## Module Structure

```
DeFiInstrumentsManager/
├── DeFiManager (main orchestrator)
├── ProtocolIntegrator (DeFi protocol abstractions)
├── YieldOptimizer (strategy optimization)
├── LiquidityManager (LP position management)
├── ImpermanentLossCalculator (IL analysis and protection)
├── RebalancingEngine (dynamic allocation)
└── CompoundingManager (reward harvesting)
```

## Core Pseudocode

### DeFiManager (Main Orchestrator)

```python
class DeFiManager extends AssetManager:
    def __init__(self, wallet_provider, config):
        // TEST: DeFiManager initializes with valid wallet provider and config
        super().__init__(wallet_provider, config)
        self.protocol_integrator = ProtocolIntegrator(config.protocol_configs)
        self.yield_optimizer = YieldOptimizer(config.optimization_params)
        self.liquidity_manager = LiquidityManager(config.liquidity_config)
        self.il_calculator = ImpermanentLossCalculator()
        self.rebalancing_engine = RebalancingEngine(config.rebalance_config)
        self.compounding_manager = CompoundingManager(config.compound_config)
        self.active_positions = {}
        self.yield_strategies = {}
        
        // TEST: All components initialize successfully
        validate_configuration(config)
        initialize_protocol_connections()

    def optimize_yield_allocation(self, capital_amount, risk_tolerance):
        // TEST: Yield optimization returns valid allocation strategy
        // TEST: Yield optimization respects risk tolerance parameters
        // TEST: Yield optimization handles insufficient capital gracefully
        
        validate_input(capital_amount, risk_tolerance)
        
        if capital_amount < self.config.min_capital_threshold:
            raise InsufficientCapitalError("Capital below minimum threshold")
        
        opportunities = self.yield_optimizer.scan_yield_opportunities()
        suitable_opportunities = self.yield_optimizer.filter_by_risk(opportunities, risk_tolerance)
        
        if not suitable_opportunities:
            return OptimizationResult(success=False, reason="No suitable opportunities found")
        
        allocation_strategy = self.yield_optimizer.calculate_optimal_allocation(
            suitable_opportunities, capital_amount, risk_tolerance
        )
        
        if not self.risk_manager.validate_allocation(allocation_strategy):
            raise RiskLimitExceeded("Allocation exceeds risk limits")
        
        return allocation_strategy

    def execute_yield_strategy(self, allocation_strategy):
        // TEST: Strategy execution handles all protocol interactions
        // TEST: Strategy execution implements proper error recovery
        // TEST: Strategy execution tracks positions accurately
        
        strategy_id = generate_strategy_id()
        execution_results = []
        
        try:
            for allocation in allocation_strategy.allocations:
                position_result = self.enter_position(
                    allocation.protocol_id, allocation.amount, allocation.strategy_params
                )
                
                if position_result.success:
                    position = LiquidityPosition(
                        position_id=position_result.position_id,
                        protocol_id=allocation.protocol_id,
                        amount=allocation.amount,
                        entry_price=position_result.entry_price,
                        strategy_params=allocation.strategy_params,
                        created_at=current_timestamp()
                    )
                    
                    self.active_positions[position_result.position_id] = position
                    execution_results.append(position_result)
            
            strategy = YieldStrategy(
                strategy_id=strategy_id,
                allocations=allocation_strategy.allocations,
                positions=[r.position_id for r in execution_results if r.success],
                created_at=current_timestamp(),
                status=StrategyStatus.ACTIVE
            )
            
            self.yield_strategies[strategy_id] = strategy
            return StrategyExecutionResult(success=True, strategy_id=strategy_id, positions=execution_results)
            
        except Exception as e:
            self.rollback_partial_strategy(execution_results)
            raise

    def provide_liquidity(self, token_pair, amount, strategy_type):
        // TEST: Liquidity provision validates token pair and amount
        // TEST: Liquidity provision calculates optimal pool selection
        // TEST: Liquidity provision implements IL protection
        
        validate_token_pair(token_pair)
        validate_amount(amount)
        
        available_pools = self.protocol_integrator.find_liquidity_pools(token_pair)
        if not available_pools:
            raise NoPoolsAvailableError(f"No pools found for {token_pair}")
        
        pool_analysis = self.liquidity_manager.analyze_pools(available_pools, amount, strategy_type)
        selected_pool = pool_analysis.best_pool
        
        il_risk = self.il_calculator.calculate_il_risk(token_pair, amount, selected_pool.historical_data)
        
        if il_risk.max_il_percentage > self.config.max_acceptable_il:
            if strategy_type.enable_il_protection:
                protection_strategy = self.il_calculator.create_protection_strategy(token_pair, amount, il_risk)
                protection_result = self.execute_il_protection(protection_strategy)
                
                if not protection_result.success:
                    raise ILProtectionFailedError("Failed to establish IL protection")
        
        lp_result = self.liquidity_manager.provide_liquidity(selected_pool, amount, token_pair)
        
        if lp_result.success:
            lp_position = LiquidityPosition(
                position_id=lp_result.position_id,
                protocol_id=selected_pool.protocol_id,
                pool_address=selected_pool.address,
                token_pair=token_pair,
                liquidity_amount=amount,
                lp_tokens=lp_result.lp_tokens,
                entry_price=lp_result.entry_price,
                created_at=current_timestamp()
            )
            
            self.active_positions[lp_result.position_id] = lp_position
            return lp_result
        else:
            raise LiquidityProvisionFailedError(f"Failed to provide liquidity: {lp_result.error}")

    def monitor_and_rebalance_positions(self):
        // TEST: Position monitoring detects rebalancing opportunities
        // TEST: Position monitoring handles protocol failures gracefully
        // TEST: Position monitoring respects rebalancing thresholds
        
        for strategy_id, strategy in self.yield_strategies.items():
            if strategy.status != StrategyStatus.ACTIVE:
                continue
            
            rebalance_needed = False
            
            for position_id in strategy.positions:
                position = self.active_positions.get(position_id)
                if not position:
                    continue
                
                current_yield = self.protocol_integrator.get_current_yield(
                    position.protocol_id, position.strategy_params
                )
                
                yield_change = (current_yield - position.expected_yield) / position.expected_yield
                
                if yield_change < -self.config.rebalance_threshold:
                    rebalance_needed = True
            
            if rebalance_needed:
                new_opportunities = self.yield_optimizer.scan_yield_opportunities()
                total_value = sum(pos.current_value for pos in strategy.positions)
                new_allocation = self.yield_optimizer.calculate_optimal_allocation(
                    new_opportunities, total_value, strategy.risk_tolerance
                )
                
                self.execute_rebalancing(strategy_id, new_allocation)

    def harvest_and_compound_rewards(self):
        // TEST: Reward harvesting processes all eligible positions
        // TEST: Reward harvesting optimizes gas costs through batching
        // TEST: Reward harvesting handles failed transactions gracefully
        
        harvestable_positions = []
        
        for position_id, position in self.active_positions.items():
            rewards_data = self.protocol_integrator.get_pending_rewards(position.protocol_id, position_id)
            
            if rewards_data.total_value > self.config.min_harvest_threshold:
                harvestable_positions.append((position_id, position, rewards_data))
        
        if not harvestable_positions:
            return
        
        protocol_groups = group_by_protocol(harvestable_positions)
        total_harvested = 0
        harvest_results = []
        
        for protocol_id, positions in protocol_groups.items():
            try:
                batch_result = self.compounding_manager.batch_harvest_rewards(protocol_id, positions)
                
                if batch_result.success:
                    total_harvested += batch_result.total_harvested
                    harvest_results.extend(batch_result.individual_results)
                    
                    if self.config.auto_compound_enabled:
                        compound_result = self.compounding_manager.compound_rewards(
                            protocol_id, batch_result.harvested_tokens
                        )
                        
                        if compound_result.success:
                            log_info(f"Compounded {compound_result.compounded_amount} on {protocol_id}")
                
            except Exception as e:
                log_error(f"Failed to harvest rewards from {protocol_id}: {e}")
                continue
        
        return HarvestResult(
            total_harvested=total_harvested,
            individual_results=harvest_results,
            protocols_processed=len(protocol_groups)
        )
```

### YieldOptimizer (Strategy Optimization)

```python
class YieldOptimizer:
    def __init__(self, optimization_params):
        // TEST: Yield optimizer initializes with valid parameters
        self.params = optimization_params
        self.protocol_integrator = get_protocol_integrator()
        self.risk_calculator = RiskCalculator()
        self.yield_cache = YieldCache(ttl=60)

    def scan_yield_opportunities(self):
        // TEST: Opportunity scanning returns comprehensive data
        // TEST: Opportunity scanning handles protocol failures gracefully
        
        opportunities = []
        
        for protocol_id in self.params.monitored_protocols:
            try:
                protocol_opportunities = self.protocol_integrator.get_yield_opportunities(protocol_id)
                
                for opportunity in protocol_opportunities:
                    risk_metrics = self.risk_calculator.calculate_protocol_risk(protocol_id, opportunity)
                    
                    enhanced_opportunity = YieldOpportunity(
                        protocol_id=protocol_id,
                        strategy_type=opportunity.strategy_type,
                        apy=opportunity.apy,
                        tvl=opportunity.tvl,
                        risk_score=risk_metrics.composite_score,
                        liquidity_depth=opportunity.liquidity_depth,
                        entry_requirements=opportunity.entry_requirements,
                        discovered_at=current_timestamp()
                    )
                    
                    opportunities.append(enhanced_opportunity)
                    
            except (APIError, ProtocolError) as e:
                log_warning(f"Failed to scan {protocol_id}: {e}")
                continue
        
        opportunities.sort(key=lambda x: x.apy / (1 + x.risk_score), reverse=True)
        return opportunities

    def calculate_optimal_allocation(self, opportunities, capital_amount, risk_tolerance):
        // TEST: Allocation calculation optimizes risk-adjusted returns
        // TEST: Allocation calculation respects diversification constraints
        
        if not opportunities:
            raise NoOpportunitiesError("No opportunities available for allocation")
        
        suitable_opportunities = [
            opp for opp in opportunities
            if opp.risk_score <= risk_tolerance.max_risk_score
        ]
        
        if not suitable_opportunities:
            raise NoSuitableOpportunitiesError("No opportunities match risk tolerance")
        
        allocation_weights = self.optimize_portfolio_weights(suitable_opportunities, risk_tolerance)
        
        allocations = []
        remaining_capital = capital_amount
        
        for i, opportunity in enumerate(suitable_opportunities):
            if allocation_weights[i] == 0:
                continue
            
            allocation_amount = capital_amount * allocation_weights[i]
            
            if allocation_amount < opportunity.entry_requirements.min_amount:
                continue
            
            allocation_amount = min(allocation_amount, remaining_capital)
            
            if allocation_amount > 0:
                allocations.append(AllocationTarget(
                    protocol_id=opportunity.protocol_id,
                    strategy_type=opportunity.strategy_type,
                    amount=allocation_amount,
                    expected_apy=opportunity.apy,
                    risk_score=opportunity.risk_score,
                    strategy_params=opportunity.entry_requirements
                ))
                
                remaining_capital -= allocation_amount
        
        return AllocationStrategy(
            allocations=allocations,
            total_allocated=capital_amount - remaining_capital,
            expected_portfolio_apy=self.calculate_portfolio_apy(allocations),
            portfolio_risk_score=self.calculate_portfolio_risk(allocations),
            diversification_score=self.calculate_diversification_score(allocations)
        )

    def optimize_portfolio_weights(self, opportunities, risk_tolerance):
        // TEST: Portfolio optimization uses proper mathematical models
        // TEST: Portfolio optimization handles correlation matrices
        
        n_opportunities = len(opportunities)
        
        if n_opportunities == 1:
            return [1.0]
        
        expected_returns = [opp.apy / 100 for opp in opportunities]
        risk_scores = [opp.risk_score for opp in opportunities]
        correlation_matrix = self.estimate_correlation_matrix(opportunities)
        
        def objective_function(weights):
            portfolio_return = sum(w * r for w, r in zip(weights, expected_returns))
            portfolio_risk = self.calculate_portfolio_variance(weights, risk_scores, correlation_matrix)
            
            if portfolio_risk == 0:
                return -float('inf')
            
            return -(portfolio_return / portfolio_risk)
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: sum(w) - 1},
            {'type': 'ineq', 'fun': lambda w: risk_tolerance.max_portfolio_risk - 
             self.calculate_portfolio_variance(w, risk_scores, correlation_matrix)}
        ]
        
        bounds = [(0, risk_tolerance.max_single_allocation) for _ in range(n_opportunities)]
        initial_weights = [1.0 / n_opportunities] * n_opportunities
        
        result = optimize_portfolio(objective_function, initial_weights, bounds=bounds, constraints=constraints)
        
        if result.success:
            return result.x
        else:
            log_warning("Portfolio optimization failed, using equal weights")
            return initial_weights

    def filter_by_risk(self, opportunities, risk_tolerance):
        // TEST: Risk filtering applies all tolerance parameters
        
        filtered = []
        
        for opportunity in opportunities:
            if opportunity.risk_score > risk_tolerance.max_risk_score:
                continue
            
            if (risk_tolerance.protocol_limits and 
                opportunity.protocol_id in risk_tolerance.protocol_limits):
                max_allocation = risk_tolerance.protocol_limits[opportunity.protocol_id]
                if max_allocation == 0:
                    continue
            
            if (risk_tolerance.allowed_strategies and 
                opportunity.strategy_type not in risk_tolerance.allowed_strategies):
                continue
            
            if opportunity.tvl < risk_tolerance.min_tvl:
                continue
            
            filtered.append(opportunity)
        
        return filtered
```

### ImpermanentLossCalculator (IL Analysis and Protection)

```python
class ImpermanentLossCalculator:
    def __init__(self):
        // TEST: IL calculator initializes correctly
        self.price_oracle = PriceOracle()
        self.historical_data = HistoricalDataProvider()

    def calculate_il_risk(self, token_pair, amount, historical_data):
        // TEST: IL risk calculation uses proper mathematical models
        // TEST: IL risk calculation handles various time horizons
        
        price_history = self.historical_data.get_price_history(token_pair, days=self.config.analysis_period_days)
        
        if len(price_history) < self.config.min_data_points:
            raise InsufficientDataError("Not enough historical data for IL analysis")
        
        price_ratios = []
        for data_point in price_history:
            ratio = data_point.token0_price / data_point.token1_price
            price_ratios.append(ratio)
        
        initial_ratio = price_ratios[0]
        
        il_values = []
        for ratio in price_ratios:
            il_percentage = self.calculate_il_percentage(initial_ratio, ratio)
            il_values.append(il_percentage)
        
        max_il = max(il_values)
        mean_il = statistics.mean(il_values)
        std_il = statistics.stdev(il_values) if len(il_values) > 1 else 0
        il_var_95 = statistics.quantiles(il_values, n=20)[18] if len(il_values) >= 20 else max_il
        potential_loss_usd = amount * (max_il / 100)
        
        return ILRiskAnalysis(
            max_il_percentage=max_il,
            mean_il_percentage=mean_il,
            il_volatility=std_il,
            il_var_95=il_var_95,
            potential_loss_usd=potential_loss_usd,
            confidence_level=0.95,
            analysis_period_days=self.config.analysis_period_days
        )

    def calculate_il_percentage(self, initial_ratio, current_ratio):
        // TEST: IL percentage calculation uses correct formula
        
        if initial_ratio == 0 or current_ratio == 0:
            return 0
        
        ratio_change = current_ratio / initial_ratio
        il_multiplier = (2 * math.sqrt(ratio_change)) / (1 + ratio_change) - 1
        
        return il_multiplier * 100

    def create_protection_strategy(self, token_pair, amount, il_risk):
        // TEST: Protection strategy creation considers all risk factors
        // TEST: Protection strategy is cost-effective
        
        protection_methods = []
        
        if self.config.enable_perp_hedging:
            perp_hedge = self.create_perpetual_hedge_strategy(token_pair, amount, il_risk)
            if perp_hedge.is_viable:
                protection_methods.append(perp_hedge)
        
        if self.config.enable_options_hedging:
            options_hedge = self.create_options_hedge_strategy(token_pair, amount, il_risk)
            if options_hedge.is_viable:
                protection_methods.append(options_hedge)
        
        if not protection_methods:
            raise NoViableProtectionError("No viable IL protection methods available")
        
        best_method = min(protection_methods, key=lambda x: x.cost_percentage)
        
        return ILProtectionStrategy(
            method=best_method.method_type,
            cost_percentage=best_method.cost_percentage,
            coverage_percentage=best_method.coverage_percentage,
            execution_params=best_method.execution_params,
            expected_effectiveness=best_method.expected_effectiveness
        )
```

## TDD Anchor Summary

### Core Functionality Tests
1. **DeFiManager Initialization**: Validates proper setup with all components
2. **Yield Optimization**: Tests allocation calculation and risk filtering
3. **Liquidity Provision**: Validates pool selection and IL protection
4. **Position Monitoring**: Tests rebalancing triggers and execution
5. **Reward Harvesting**: Validates batch processing and compounding

### Edge Case Tests
6. **Insufficient Capital**: Handles below-threshold amounts gracefully
7. **No Opportunities**: Manages scenarios with no suitable yields
8. **Protocol Failures**: Continues operation when individual protocols fail
9. **IL Protection Failures**: Handles protection strategy failures
10. **Rebalancing Failures**: Manages failed rebalancing attempts

### Security Tests
11. **Input Validation**: All parameters properly validated
12. **Risk Limit Enforcement**: Position sizes and allocations respected
13. **Slippage Protection**: Price changes handled during execution
14. **Access Control**: Unauthorized operations prevented

### Performance Tests
15. **Concurrent Operations**: Multiple strategies handled efficiently
16. **Cache Effectiveness**: Yield data caching reduces API calls
17. **Gas Optimization**: Batch operations achieve cost savings
18. **Response Times**: All operations complete within limits

## Integration Points

### Phase 1 Dependencies
- **WalletProvider Interface**: Extends existing wallet abstraction
- **Event System**: Emits DeFi-specific events for monitoring
- **Risk Management**: Integrates with existing risk controls
- **Configuration**: Uses environment-based settings

### External Integrations
- **DeFi Protocols**: Uniswap, Aave, Compound, Curve, Convex APIs
- **Price Oracles**: Chainlink, Band Protocol for accurate pricing
- **Yield Aggregators**: Yearn, Harvest for strategy insights
- **IL Protection**: Perpetual and options platforms for hedging

### Error Handling Strategy
- **Graceful Degradation**: Continue operation when protocols fail
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascade failures across protocols
- **Comprehensive Logging**: Detailed audit trail for all operations