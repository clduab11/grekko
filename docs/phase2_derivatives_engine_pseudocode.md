# Phase 2: Derivatives Trading Engine - Pseudocode Specification

## Overview

This module implements the Derivatives Trading Engine with perpetual futures integration, options trading with Greeks calculation, risk management for leveraged positions, and cross-platform arbitrage opportunities.

## Module Structure

```
DerivativesTradingEngine/
├── DerivativesManager (main orchestrator)
├── PlatformIntegrator (derivatives platform abstractions)
├── PerpetualsEngine (perpetual futures trading)
├── OptionsEngine (options trading and Greeks)
├── RiskCalculator (position risk management)
├── ArbitrageDetector (cross-platform opportunities)
└── LiquidationMonitor (position monitoring)
```

## Core Pseudocode

### DerivativesManager (Main Orchestrator)

```python
class DerivativesManager extends AssetManager:
    def __init__(self, wallet_provider, config):
        // TEST: DerivativesManager initializes with valid wallet provider and config
        super().__init__(wallet_provider, config)
        self.platform_integrator = PlatformIntegrator(config.platform_configs)
        self.perpetuals_engine = PerpetualsEngine(config.perp_config)
        self.options_engine = OptionsEngine(config.options_config)
        self.risk_calculator = RiskCalculator(config.risk_params)
        self.arbitrage_detector = ArbitrageDetector(config.arbitrage_config)
        self.liquidation_monitor = LiquidationMonitor(config.liquidation_config)
        self.active_positions = {}
        
        // TEST: All components initialize successfully
        validate_configuration(config)
        initialize_platform_connections()

    def open_perpetual_position(self, asset_symbol, position_type, size, leverage, platform_preference=None):
        // TEST: Perpetual position opening validates all parameters
        // TEST: Perpetual position opening respects risk limits
        // TEST: Perpetual position opening handles platform failures gracefully
        
        validate_input(asset_symbol, position_type, size, leverage)
        
        if not self.risk_calculator.can_open_position(asset_symbol, size, leverage):
            raise RiskLimitExceeded("Position exceeds risk limits")
        
        available_platforms = self.platform_integrator.get_platforms_for_asset(asset_symbol)
        
        if platform_preference and platform_preference in available_platforms:
            selected_platform = platform_preference
        else:
            platform_analysis = self.analyze_platforms_for_perpetuals(available_platforms, asset_symbol, size, leverage)
            selected_platform = platform_analysis.best_platform
        
        margin_required = self.calculate_margin_requirement(size, leverage, selected_platform)
        
        if not self.wallet_provider.has_sufficient_balance(margin_required):
            raise InsufficientMarginError("Insufficient margin for position")
        
        position_result = self.perpetuals_engine.open_position(
            platform=selected_platform,
            asset_symbol=asset_symbol,
            position_type=position_type,
            size=size,
            leverage=leverage,
            margin_required=margin_required
        )
        
        if position_result.success:
            position = DerivativePosition(
                position_id=position_result.position_id,
                platform_id=selected_platform,
                asset_symbol=asset_symbol,
                position_type=position_type,
                size=size,
                leverage=leverage,
                entry_price=position_result.entry_price,
                margin_used=margin_required,
                liquidation_price=position_result.liquidation_price,
                created_at=current_timestamp(),
                status=PositionStatus.OPEN
            )
            
            self.active_positions[position_result.position_id] = position
            self.liquidation_monitor.add_position(position)
            
            return position_result
        else:
            raise PositionOpeningFailedError(f"Failed to open position: {position_result.error}")

    def trade_options(self, underlying_asset, strategy_type, strategy_params):
        // TEST: Options trading validates strategy parameters
        // TEST: Options trading calculates Greeks correctly
        // TEST: Options trading manages portfolio risk
        
        validate_options_strategy(strategy_type, strategy_params)
        
        available_contracts = self.platform_integrator.get_options_contracts(underlying_asset)
        if not available_contracts:
            raise NoOptionsAvailableError(f"No options available for {underlying_asset}")
        
        strategy_analysis = self.options_engine.analyze_strategy(strategy_type, strategy_params, available_contracts)
        if not strategy_analysis.is_viable:
            raise StrategyNotViableError(f"Strategy not viable: {strategy_analysis.reason}")
        
        current_greeks = self.calculate_portfolio_greeks()
        strategy_greeks = strategy_analysis.strategy_greeks
        projected_greeks = self.combine_greeks(current_greeks, strategy_greeks)
        
        if not self.risk_calculator.validate_greeks_limits(projected_greeks):
            raise GreeksLimitExceeded("Strategy would exceed Greeks limits")
        
        execution_result = self.options_engine.execute_strategy(strategy_type, strategy_analysis.selected_contracts, strategy_params)
        
        if execution_result.success:
            for contract_result in execution_result.contract_results:
                options_position = OptionsPosition(
                    position_id=contract_result.position_id,
                    contract_id=contract_result.contract_id,
                    underlying_asset=underlying_asset,
                    strategy_type=strategy_type,
                    option_type=contract_result.option_type,
                    strike_price=contract_result.strike_price,
                    expiration_date=contract_result.expiration_date,
                    quantity=contract_result.quantity,
                    premium_paid=contract_result.premium_paid,
                    greeks=contract_result.greeks,
                    created_at=current_timestamp()
                )
                
                self.active_positions[contract_result.position_id] = options_position
            
            return execution_result
        else:
            raise OptionsExecutionFailedError(f"Options strategy execution failed: {execution_result.error}")

    def detect_arbitrage_opportunities(self):
        // TEST: Arbitrage detection scans all platforms efficiently
        // TEST: Arbitrage detection calculates accurate profit potential
        // TEST: Arbitrage detection considers execution costs
        
        opportunities = []
        platform_prices = {}
        
        for platform_id in self.platform_integrator.get_active_platforms():
            try:
                prices = self.platform_integrator.get_platform_prices(platform_id)
                platform_prices[platform_id] = prices
            except (APIError, PlatformError) as e:
                log_warning(f"Failed to get prices from {platform_id}: {e}")
                continue
        
        for asset_symbol in self.config.monitored_assets:
            asset_prices = {}
            
            for platform_id, prices in platform_prices.items():
                if asset_symbol in prices:
                    asset_prices[platform_id] = prices[asset_symbol]
            
            if len(asset_prices) < 2:
                continue
            
            arbitrage_ops = self.arbitrage_detector.find_opportunities(asset_symbol, asset_prices)
            
            for opportunity in arbitrage_ops:
                execution_cost = self.calculate_arbitrage_execution_cost(opportunity)
                net_profit = opportunity.gross_profit - execution_cost
                
                if net_profit > self.config.min_arbitrage_profit:
                    enhanced_opportunity = ArbitrageOpportunity(
                        asset_symbol=asset_symbol,
                        buy_platform=opportunity.buy_platform,
                        sell_platform=opportunity.sell_platform,
                        buy_price=opportunity.buy_price,
                        sell_price=opportunity.sell_price,
                        gross_profit=opportunity.gross_profit,
                        execution_cost=execution_cost,
                        net_profit=net_profit,
                        profit_percentage=net_profit / opportunity.buy_price * 100,
                        max_size=opportunity.max_size,
                        discovered_at=current_timestamp(),
                        expires_at=current_timestamp() + self.config.opportunity_ttl
                    )
                    
                    opportunities.append(enhanced_opportunity)
        
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        return opportunities

    def execute_arbitrage(self, opportunity):
        // TEST: Arbitrage execution handles simultaneous trades
        // TEST: Arbitrage execution manages partial fills
        // TEST: Arbitrage execution calculates actual profit
        
        validate_arbitrage_opportunity(opportunity)
        
        if current_timestamp() > opportunity.expires_at:
            raise OpportunityExpiredError("Arbitrage opportunity has expired")
        
        current_buy_price = self.platform_integrator.get_current_price(opportunity.buy_platform, opportunity.asset_symbol)
        current_sell_price = self.platform_integrator.get_current_price(opportunity.sell_platform, opportunity.asset_symbol)
        
        current_profit = current_sell_price - current_buy_price
        if current_profit < self.config.min_arbitrage_profit:
            raise OpportunityNoLongerViableError("Arbitrage opportunity no longer profitable")
        
        trade_size = min(
            opportunity.max_size,
            self.risk_calculator.get_max_arbitrage_size(opportunity.asset_symbol),
            self.get_available_balance_for_arbitrage()
        )
        
        if trade_size <= 0:
            raise InsufficientCapitalError("Insufficient capital for arbitrage")
        
        execution_result = self.arbitrage_detector.execute_simultaneous_trades(
            buy_platform=opportunity.buy_platform,
            sell_platform=opportunity.sell_platform,
            asset_symbol=opportunity.asset_symbol,
            size=trade_size,
            max_slippage=self.config.max_arbitrage_slippage
        )
        
        if execution_result.success:
            actual_profit = execution_result.sell_execution.average_price - execution_result.buy_execution.average_price
            actual_profit_usd = actual_profit * execution_result.executed_size
            
            arbitrage_record = ArbitrageExecution(
                opportunity_id=opportunity.opportunity_id,
                asset_symbol=opportunity.asset_symbol,
                executed_size=execution_result.executed_size,
                buy_platform=opportunity.buy_platform,
                sell_platform=opportunity.sell_platform,
                buy_price=execution_result.buy_execution.average_price,
                sell_price=execution_result.sell_execution.average_price,
                actual_profit=actual_profit_usd,
                execution_cost=execution_result.total_fees,
                net_profit=actual_profit_usd - execution_result.total_fees,
                executed_at=current_timestamp()
            )
            
            return arbitrage_record
        else:
            raise ArbitrageExecutionFailedError(f"Arbitrage execution failed: {execution_result.error}")

    def monitor_positions_risk(self):
        // TEST: Risk monitoring updates position metrics correctly
        // TEST: Risk monitoring triggers alerts on threshold breaches
        // TEST: Risk monitoring handles liquidation scenarios
        
        for position_id, position in self.active_positions.items():
            if position.status != PositionStatus.OPEN:
                continue
            
            current_data = self.platform_integrator.get_position_data(position.platform_id, position_id)
            
            if current_data:
                position.current_price = current_data.current_price
                position.unrealized_pnl = current_data.unrealized_pnl
                position.margin_ratio = current_data.margin_ratio
                
                risk_metrics = self.risk_calculator.calculate_position_risk(position, current_data)
                
                if risk_metrics.liquidation_risk > self.config.liquidation_warning_threshold:
                    self.emit_event(LiquidationWarning(
                        position_id=position_id,
                        liquidation_risk=risk_metrics.liquidation_risk,
                        current_margin_ratio=position.margin_ratio,
                        liquidation_price=current_data.liquidation_price
                    ))
                
                pnl_percentage = position.unrealized_pnl / position.margin_used * 100
                
                if pnl_percentage < -self.config.max_loss_percentage:
                    self.emit_event(StopLossTriggered(
                        position_id=position_id,
                        current_pnl=position.unrealized_pnl,
                        pnl_percentage=pnl_percentage
                    ))
                    
                    if self.config.auto_stop_loss_enabled:
                        self.close_position(position_id, "stop_loss")
                
                elif pnl_percentage > self.config.take_profit_percentage:
                    self.emit_event(TakeProfitTriggered(
                        position_id=position_id,
                        current_pnl=position.unrealized_pnl,
                        pnl_percentage=pnl_percentage
                    ))
                    
                    if self.config.auto_take_profit_enabled:
                        self.close_position(position_id, "take_profit")

    def close_position(self, position_id, reason="manual"):
        // TEST: Position closing handles all position types
        // TEST: Position closing calculates final PnL correctly
        // TEST: Position closing updates tracking properly
        
        position = self.active_positions.get(position_id)
        if not position:
            raise PositionNotFoundError(f"Position {position_id} not found")
        
        if position.status != PositionStatus.OPEN:
            raise PositionNotOpenError(f"Position {position_id} is not open")
        
        if isinstance(position, DerivativePosition):
            close_result = self.perpetuals_engine.close_position(position.platform_id, position_id)
        elif isinstance(position, OptionsPosition):
            close_result = self.options_engine.close_position(position.platform_id, position_id)
        else:
            raise UnsupportedPositionTypeError(f"Unsupported position type: {type(position)}")
        
        if close_result.success:
            position.status = PositionStatus.CLOSED
            position.exit_price = close_result.exit_price
            position.realized_pnl = close_result.realized_pnl
            position.total_fees = close_result.total_fees
            position.closed_at = current_timestamp()
            position.close_reason = reason
            
            self.liquidation_monitor.remove_position(position_id)
            
            return close_result
        else:
            raise PositionClosingFailedError(f"Failed to close position: {close_result.error}")
```

### OptionsEngine (Options Trading and Greeks)

```python
class OptionsEngine:
    def __init__(self, options_config):
        // TEST: Options engine initializes with valid configuration
        self.config = options_config
        self.platform_integrator = get_platform_integrator()
        self.greeks_calculator = GreeksCalculator()

    def analyze_strategy(self, strategy_type, strategy_params, available_contracts):
        // TEST: Strategy analysis validates all strategy types
        // TEST: Strategy analysis calculates accurate Greeks
        
        if strategy_type == OptionsStrategyType.COVERED_CALL:
            return self.analyze_covered_call_strategy(strategy_params, available_contracts)
        elif strategy_type == OptionsStrategyType.PROTECTIVE_PUT:
            return self.analyze_protective_put_strategy(strategy_params, available_contracts)
        elif strategy_type == OptionsStrategyType.IRON_CONDOR:
            return self.analyze_iron_condor_strategy(strategy_params, available_contracts)
        elif strategy_type == OptionsStrategyType.STRADDLE:
            return self.analyze_straddle_strategy(strategy_params, available_contracts)
        else:
            raise UnsupportedStrategyError(f"Strategy {strategy_type} not supported")

    def analyze_covered_call_strategy(self, strategy_params, available_contracts):
        // TEST: Covered call analysis selects optimal strike and expiration
        
        underlying_price = strategy_params.underlying_price
        target_premium = strategy_params.target_premium
        max_days_to_expiry = strategy_params.max_days_to_expiry
        
        call_options = [
            contract for contract in available_contracts
            if (contract.option_type == OptionType.CALL and
                contract.days_to_expiry <= max_days_to_expiry and
                contract.strike_price > underlying_price)
        ]
        
        if not call_options:
            return StrategyAnalysis(is_viable=False, reason="No suitable call options found")
        
        best_contract = None
        best_score = 0
        
        for contract in call_options:
            greeks = self.greeks_calculator.calculate_greeks(contract, underlying_price)
            
            premium_score = contract.premium / target_premium if target_premium > 0 else 1
            delta_score = abs(greeks.delta - 0.3)
            theta_score = greeks.theta
            
            total_score = premium_score + (1 - delta_score) + theta_score
            
            if total_score > best_score:
                best_score = total_score
                best_contract = contract
        
        if best_contract:
            strategy_greeks = self.greeks_calculator.calculate_greeks(best_contract, underlying_price)
            
            return StrategyAnalysis(
                is_viable=True,
                selected_contracts=[best_contract],
                strategy_greeks=strategy_greeks,
                expected_premium=best_contract.premium,
                max_profit=best_contract.premium,
                max_loss=float('inf'),
                breakeven_price=underlying_price + best_contract.premium
            )
        else:
            return StrategyAnalysis(is_viable=False, reason="No optimal contract found")

    def execute_strategy(self, strategy_type, selected_contracts, strategy_params):
        // TEST: Strategy execution handles all contract types
        // TEST: Strategy execution manages partial fills
        
        execution_results = []
        
        for contract in selected_contracts:
            if strategy_type in [OptionsStrategyType.COVERED_CALL, OptionsStrategyType.CASH_SECURED_PUT]:
                order_side = "sell"
            else:
                order_side = "buy"
            
            order_params = OptionsOrderParams(
                contract_id=contract.contract_id,
                side=order_side,
                quantity=strategy_params.quantity,
                order_type="limit",
                limit_price=contract.premium,
                time_in_force="GTC"
            )
            
            try:
                order_result = self.platform_integrator.place_options_order(contract.platform_id, order_params)
                
                if order_result.status in ["filled", "partially_filled"]:
                    position_greeks = self.greeks_calculator.calculate_position_greeks(
                        contract, order_result.filled_quantity, order_side
                    )
                    
                    contract_result = ContractExecutionResult(
                        success=True,
                        position_id=order_result.position_id,
                        contract_id=contract.contract_id,
                        option_type=contract.option_type,
                        strike_price=contract.strike_price,
                        expiration_date=contract.expiration_date,
                        quantity=order_result.filled_quantity,
                        premium_paid=order_result.average_fill_price * order_result.filled_quantity,
                        greeks=position_greeks
                    )
                else:
                    contract_result = ContractExecutionResult(success=False, error=f"Order not filled: {order_result.status}")
                
                execution_results.append(contract_result)
                
            except Exception as e:
                execution_results.append(ContractExecutionResult(success=False, error=str(e)))
        
        successful_executions = [r for r in execution_results if r.success]
        
        if successful_executions:
            return StrategyExecutionResult(
                success=True,
                contract_results=execution_results,
                total_premium=sum(r.premium_paid for r in successful_executions),
                combined_greeks=self.combine_position_greeks(successful_executions)
            )
        else:
            return StrategyExecutionResult(success=False, error="No contracts were successfully executed")
```

### RiskCalculator (Position Risk Management)

```python
class RiskCalculator:
    def __init__(self, risk_params):
        // TEST: Risk calculator initializes with valid parameters
        self.params = risk_params
        self.portfolio_tracker = PortfolioTracker()

    def can_open_position(self, asset_symbol, size, leverage):
        // TEST: Position validation checks all risk limits
        // TEST: Position validation considers portfolio exposure
        
        max_position_size = self.params.max_position_size.get(asset_symbol, self.params.default_max_position_size)
        if size > max_position_size:
            return False
        
        max_leverage = self.params.max_leverage.get(asset_symbol, self.params.default_max_leverage)
        if leverage > max_leverage:
            return False
        
        current_exposure = self.portfolio_tracker.get_asset_exposure(asset_symbol)
        total_exposure = current_exposure + (size * leverage)
        
        if total_exposure > self.params.max_portfolio_exposure:
            return False
        
        correlated_exposure = self.portfolio_tracker.get_correlated_exposure(asset_symbol)
        if correlated_exposure + total_exposure > self.params.max_correlated_exposure:
            return False
        
        return True

    def calculate_position_risk(self, position, current_data):
        // TEST: Risk calculation provides comprehensive metrics
        
        if position.position_type == PositionType.LONG:
            distance_to_liquidation = (current_data.current_price - position.liquidation_price) / current_data.current_price
        else:
            distance_to_liquidation = (position.liquidation_price - current_data.current_price) / current_data.current_price
        
        liquidation_risk = max(0, 1 - (distance_to_liquidation / 0.1))
        
        price_volatility = self.calculate_price_volatility(position.asset_symbol)
        position_volatility = price_volatility * position.leverage
        
        position_value = position.size * current_data.current_price
        var_95 = position_value * position_volatility * 1.645
        
        return PositionRiskMetrics(
            liquidation_risk=liquidation_risk,
            distance_to_liquidation=distance_to_liquidation,
            position_volatility=position_volatility,
            var_95=var_95,
            margin_ratio=current_data.margin_ratio,
            unrealized_pnl_percentage=position.unrealized_pnl / position.margin_used * 100
        )

    def validate_greeks_limits(self, projected_greeks):
        // TEST: Greeks validation checks all risk parameters
        
        if abs(projected_greeks.delta) > self.params.max_portfolio_delta:
            return False
        
        if abs(projected_greeks.gamma) > self.params.max_portfolio_gamma:
            return False
        
        if abs(projected_greeks.theta) > self.params.max_portfolio_theta:
            return False
        
        if abs(projected_greeks.vega) > self.params.max_portfolio_vega:
            return False
        
        return True

    def get_max_arbitrage_size(self, asset_symbol):
        // TEST: Arbitrage size calculation considers risk limits
        
        max_single_trade = self.params.max_arbitrage_size.get(asset_symbol, self.params.default_max_arbitrage_size)
        current_exposure = self.portfolio_tracker.get_asset_exposure(asset_symbol)
        available_exposure = self.params.max_portfolio_exposure - current_exposure
        
        return min(max_single_trade, available_exposure)
```

## TDD Anchor Summary

### Core Functionality Tests
1. **DerivativesManager Initialization**: Validates proper setup with all components
2. **Perpetual Position Management**: Tests opening, monitoring, and closing positions
3. **Options Strategy Execution**: Validates strategy analysis and Greeks calculation
4. **Arbitrage Detection**: Tests cross-platform opportunity identification
5. **Risk Management**: Validates position limits and portfolio risk controls

### Edge Case Tests
6. **Insufficient Margin**: Handles scenarios with inadequate capital
7. **Platform Failures**: Continues operation when individual platforms fail
8. **Liquidation Scenarios**: Manages positions approaching liquidation
9. **Options Expiration**: Handles contract expiration and exercise
10. **Arbitrage Timing**: Manages expired or invalid opportunities

### Security Tests
11. **Input Validation**: All trading parameters properly validated
12. **Risk Limit Enforcement**: Position sizes and leverage limits respected
13. **Greeks Limits**: Portfolio Greeks maintained within bounds
14. **Access Control**: Unauthorized trading operations prevented

### Performance Tests
15. **Concurrent Trading**: Multiple positions handled efficiently
16. **Real-time Monitoring**: Position updates processed quickly
17. **Arbitrage Speed**: Opportunities detected and executed rapidly
18. **Greeks Calculation**: Options metrics computed accurately

## Integration Points

### Phase 1 Dependencies
- **WalletProvider Interface**: Extends existing wallet abstraction
- **Event System**: Emits derivatives-specific events for monitoring
- **Risk Management**: Integrates with existing risk controls
- **Configuration**: Uses environment-based settings

### External Integrations
- **Derivatives Platforms**: dYdX, GMX, Gains Network, Lyra APIs
- **Price Oracles**: Real-time pricing for accurate Greeks calculation
- **Liquidation Engines**: Platform-specific liquidation monitoring
- **Options Protocols**: Premia, Dopex for options trading

### Error Handling Strategy
- **Graceful Degradation**: Continue operation when platforms fail
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascade failures across platforms
- **Comprehensive Logging**: Detailed audit trail for all operations