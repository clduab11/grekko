# Phase 2: NFT Trading System - Pseudocode Specification

## Overview

This module implements the NFT Trading System with marketplace integrations, floor sweep automation, trait-based purchasing, and batch transaction optimization.

## Module Structure

```
NFTTradingSystem/
├── NFTManager (main orchestrator)
├── MarketplaceIntegrator (API abstractions)
├── CollectionAnalyzer (metadata and traits)
├── FloorSweepEngine (automation logic)
├── TraitFilter (rarity and filtering)
├── BatchTransactionOptimizer (gas efficiency)
└── NFTRiskManager (position limits)
```

## Core Pseudocode

### NFTManager (Main Orchestrator)

```python
class NFTManager extends AssetManager:
    def __init__(self, wallet_provider, config):
        // TEST: NFTManager initializes with valid wallet provider and config
        super().__init__(wallet_provider, config)
        self.marketplace_integrator = MarketplaceIntegrator(config.api_keys)
        self.collection_analyzer = CollectionAnalyzer()
        self.floor_sweep_engine = FloorSweepEngine(config.sweep_config)
        self.trait_filter = TraitFilter()
        self.batch_optimizer = BatchTransactionOptimizer(config.batch_config)
        self.risk_manager = NFTRiskManager(config.risk_limits)
        self.active_sweeps = {}
        self.position_tracker = {}
        
        // TEST: All components initialize successfully
        validate_configuration(config)
        register_event_handlers()

    def start_floor_sweep(self, collection_address, sweep_params):
        // TEST: Floor sweep starts with valid parameters
        // TEST: Floor sweep rejects invalid collection addresses
        // TEST: Floor sweep respects risk limits
        
        validate_input(collection_address, sweep_params)
        
        if not self.risk_manager.can_start_sweep(collection_address, sweep_params):
            raise RiskLimitExceeded("Sweep exceeds risk limits")
        
        collection_data = self.collection_analyzer.analyze_collection(collection_address)
        
        if not collection_data.is_valid:
            raise InvalidCollection("Collection analysis failed")
        
        sweep_id = generate_sweep_id()
        sweep_config = SweepConfiguration(
            collection_address=collection_address,
            max_items=sweep_params.max_items,
            max_price_per_item=sweep_params.max_price,
            slippage_tolerance=sweep_params.slippage,
            gas_limit=sweep_params.gas_limit
        )
        
        self.active_sweeps[sweep_id] = sweep_config
        
        // Start async sweep execution
        self.floor_sweep_engine.execute_sweep(sweep_id, sweep_config)
        
        // TEST: Sweep tracking is properly initialized
        return sweep_id

    def execute_trait_based_purchase(self, collection_address, trait_criteria, purchase_params):
        // TEST: Trait purchase executes with valid criteria
        // TEST: Trait purchase validates rarity thresholds
        // TEST: Trait purchase handles no matches gracefully
        
        validate_input(collection_address, trait_criteria, purchase_params)
        
        collection_data = self.collection_analyzer.analyze_collection(collection_address)
        filtered_nfts = self.trait_filter.filter_by_traits(
            collection_data.nfts,
            trait_criteria
        )
        
        if not filtered_nfts:
            return PurchaseResult(success=False, reason="No NFTs match criteria")
        
        // Calculate fair value for trait combinations
        fair_values = self.trait_filter.calculate_trait_values(filtered_nfts, collection_data)
        
        // Filter by price and rarity thresholds
        purchase_candidates = []
        for nft in filtered_nfts:
            if (nft.current_price <= fair_values[nft.token_id] * purchase_params.max_premium and
                nft.rarity_score >= purchase_params.min_rarity):
                purchase_candidates.append(nft)
        
        if not purchase_candidates:
            return PurchaseResult(success=False, reason="No NFTs meet price/rarity criteria")
        
        // Sort by best value (rarity/price ratio)
        purchase_candidates.sort(key=lambda x: x.rarity_score / x.current_price, reverse=True)
        
        // Execute purchases up to limit
        results = []
        for nft in purchase_candidates[:purchase_params.max_purchases]:
            result = self.execute_single_purchase(nft, purchase_params)
            results.append(result)
            
            if not result.success:
                break
        
        // TEST: Purchase results are properly tracked
        return PurchaseResult(success=True, purchases=results)

    def get_collection_insights(self, collection_address):
        // TEST: Collection insights return comprehensive data
        // TEST: Collection insights handle invalid addresses
        
        validate_collection_address(collection_address)
        
        collection_data = self.collection_analyzer.analyze_collection(collection_address)
        marketplace_data = self.marketplace_integrator.get_collection_data(collection_address)
        
        insights = CollectionInsights(
            floor_price=marketplace_data.floor_price,
            volume_24h=marketplace_data.volume_24h,
            total_supply=collection_data.total_supply,
            trait_distribution=collection_data.trait_distribution,
            rarity_analysis=self.trait_filter.analyze_rarity_distribution(collection_data),
            price_trends=marketplace_data.price_history,
            liquidity_score=calculate_liquidity_score(marketplace_data)
        )
        
        return insights

    def monitor_active_positions(self):
        // TEST: Position monitoring updates correctly
        // TEST: Position monitoring triggers alerts on significant changes
        
        for position_id, position in self.position_tracker.items():
            current_data = self.marketplace_integrator.get_nft_data(
                position.collection_address,
                position.token_id
            )
            
            // Update position value
            position.current_value = current_data.current_price or position.last_known_price
            position.unrealized_pnl = position.current_value - position.purchase_price
            
            // Check for significant changes
            price_change_pct = (position.current_value - position.last_known_price) / position.last_known_price
            
            if abs(price_change_pct) > self.config.alert_threshold:
                self.emit_event(PositionAlert(
                    position_id=position_id,
                    change_percentage=price_change_pct,
                    current_value=position.current_value
                ))
            
            position.last_updated = current_timestamp()
```

### MarketplaceIntegrator (API Abstractions)

```python
class MarketplaceIntegrator:
    def __init__(self, api_keys):
        // TEST: Marketplace integrator initializes with valid API keys
        // TEST: Marketplace integrator handles missing API keys gracefully
        
        self.marketplaces = {
            'opensea': OpenSeaClient(api_keys.get('opensea')),
            'looksrare': LooksRareClient(api_keys.get('looksrare')),
            'blur': BlurClient(api_keys.get('blur')),
            'x2y2': X2Y2Client(api_keys.get('x2y2'))
        }
        
        self.rate_limiters = {
            marketplace: RateLimiter(config.rate_limits[marketplace])
            for marketplace in self.marketplaces.keys()
        }
        
        self.cache = MarketplaceCache(ttl=30)  // 30 second cache

    def get_collection_floor_price(self, collection_address):
        // TEST: Floor price aggregation returns accurate data
        // TEST: Floor price handles marketplace failures gracefully
        // TEST: Floor price respects rate limits
        
        floor_prices = {}
        
        for marketplace_name, client in self.marketplaces.items():
            try:
                with self.rate_limiters[marketplace_name]:
                    cache_key = f"floor_{marketplace_name}_{collection_address}"
                    
                    if cached_price := self.cache.get(cache_key):
                        floor_prices[marketplace_name] = cached_price
                        continue
                    
                    price_data = client.get_collection_floor_price(collection_address)
                    
                    if price_data and price_data.is_valid:
                        floor_prices[marketplace_name] = price_data.price
                        self.cache.set(cache_key, price_data.price)
                        
            except (APIError, RateLimitError) as e:
                log_warning(f"Failed to get floor price from {marketplace_name}: {e}")
                continue
        
        if not floor_prices:
            raise NoMarketplaceDataError("No marketplace data available")
        
        // Return lowest floor price across marketplaces
        return min(floor_prices.values())

    def get_nft_listings(self, collection_address, limit=100):
        // TEST: NFT listings aggregation returns comprehensive data
        // TEST: NFT listings handles pagination correctly
        // TEST: NFT listings deduplicates across marketplaces
        
        all_listings = []
        
        for marketplace_name, client in self.marketplaces.items():
            try:
                with self.rate_limiters[marketplace_name]:
                    listings = client.get_collection_listings(collection_address, limit)
                    
                    for listing in listings:
                        listing.marketplace = marketplace_name
                        listing.fetched_at = current_timestamp()
                        all_listings.append(listing)
                        
            except (APIError, RateLimitError) as e:
                log_warning(f"Failed to get listings from {marketplace_name}: {e}")
                continue
        
        // Deduplicate by token_id, keeping lowest price
        deduplicated = {}
        for listing in all_listings:
            key = f"{listing.collection_address}_{listing.token_id}"
            
            if key not in deduplicated or listing.price < deduplicated[key].price:
                deduplicated[key] = listing
        
        // Sort by price ascending
        sorted_listings = sorted(deduplicated.values(), key=lambda x: x.price)
        
        return sorted_listings[:limit]

    def execute_purchase(self, nft_listing, wallet_provider):
        // TEST: Purchase execution handles different marketplace protocols
        // TEST: Purchase execution validates sufficient balance
        // TEST: Purchase execution handles transaction failures
        
        marketplace_client = self.marketplaces[nft_listing.marketplace]
        
        // Validate purchase parameters
        if not marketplace_client.is_listing_valid(nft_listing):
            raise InvalidListingError("Listing is no longer valid")
        
        // Check wallet balance
        required_amount = nft_listing.price + estimate_gas_cost(nft_listing)
        
        if not wallet_provider.has_sufficient_balance(required_amount):
            raise InsufficientBalanceError("Insufficient balance for purchase")
        
        // Prepare transaction
        transaction = marketplace_client.prepare_purchase_transaction(
            nft_listing,
            wallet_provider.get_active_account()
        )
        
        // Execute transaction
        try:
            tx_hash = wallet_provider.send_transaction(transaction)
            
            // Wait for confirmation
            receipt = wait_for_transaction_confirmation(tx_hash, timeout=300)
            
            if receipt.status == 'success':
                return PurchaseResult(
                    success=True,
                    tx_hash=tx_hash,
                    nft_token_id=nft_listing.token_id,
                    purchase_price=nft_listing.price,
                    gas_used=receipt.gas_used
                )
            else:
                return PurchaseResult(
                    success=False,
                    error="Transaction failed",
                    tx_hash=tx_hash
                )
                
        except TransactionError as e:
            return PurchaseResult(
                success=False,
                error=str(e)
            )
```

### FloorSweepEngine (Automation Logic)

```python
class FloorSweepEngine:
    def __init__(self, sweep_config):
        // TEST: Floor sweep engine initializes with valid configuration
        self.config = sweep_config
        self.active_sweeps = {}
        self.batch_optimizer = BatchTransactionOptimizer()

    def execute_sweep(self, sweep_id, sweep_config):
        // TEST: Sweep execution respects all configuration parameters
        // TEST: Sweep execution handles marketplace failures gracefully
        // TEST: Sweep execution optimizes gas costs through batching
        
        try:
            sweep_state = SweepState(
                sweep_id=sweep_id,
                config=sweep_config,
                status=SweepStatus.RUNNING,
                purchased_items=[],
                failed_purchases=[],
                total_spent=0
            )
            
            self.active_sweeps[sweep_id] = sweep_state
            
            // Get current floor listings
            listings = self.get_floor_listings(sweep_config.collection_address)
            
            // Filter listings by price and criteria
            eligible_listings = self.filter_eligible_listings(listings, sweep_config)
            
            if not eligible_listings:
                sweep_state.status = SweepStatus.COMPLETED
                sweep_state.completion_reason = "No eligible listings found"
                return
            
            // Group listings for batch optimization
            batches = self.batch_optimizer.create_purchase_batches(
                eligible_listings,
                sweep_config.max_items,
                sweep_config.gas_limit
            )
            
            // Execute batches
            for batch_index, batch in enumerate(batches):
                if sweep_state.total_spent >= sweep_config.max_total_spend:
                    break
                
                batch_result = self.execute_batch_purchase(batch, sweep_config)
                
                // Update sweep state
                sweep_state.purchased_items.extend(batch_result.successful_purchases)
                sweep_state.failed_purchases.extend(batch_result.failed_purchases)
                sweep_state.total_spent += batch_result.total_spent
                
                // Check if we've reached limits
                if len(sweep_state.purchased_items) >= sweep_config.max_items:
                    break
                
                // Brief pause between batches to avoid overwhelming marketplaces
                sleep(self.config.batch_delay_seconds)
            
            sweep_state.status = SweepStatus.COMPLETED
            sweep_state.completed_at = current_timestamp()
            
            // TEST: Sweep completion triggers appropriate events
            self.emit_sweep_completed_event(sweep_state)
            
        except Exception as e:
            sweep_state.status = SweepStatus.FAILED
            sweep_state.error = str(e)
            log_error(f"Sweep {sweep_id} failed: {e}")

    def get_floor_listings(self, collection_address):
        // TEST: Floor listings retrieval returns sorted data
        // TEST: Floor listings handles rate limits appropriately
        
        marketplace_integrator = get_marketplace_integrator()
        
        listings = marketplace_integrator.get_nft_listings(
            collection_address,
            limit=self.config.max_listings_to_fetch
        )
        
        // Filter out listings that are too old
        current_time = current_timestamp()
        fresh_listings = [
            listing for listing in listings
            if (current_time - listing.fetched_at) < self.config.listing_freshness_threshold
        ]
        
        return fresh_listings

    def filter_eligible_listings(self, listings, sweep_config):
        // TEST: Listing filtering applies all criteria correctly
        // TEST: Listing filtering handles edge cases (empty lists, invalid data)
        
        eligible = []
        
        for listing in listings:
            // Price filter
            if listing.price > sweep_config.max_price_per_item:
                continue
            
            // Marketplace filter (if specified)
            if (sweep_config.preferred_marketplaces and 
                listing.marketplace not in sweep_config.preferred_marketplaces):
                continue
            
            // Trait filter (if specified)
            if sweep_config.trait_requirements:
                if not self.meets_trait_requirements(listing, sweep_config.trait_requirements):
                    continue
            
            // Rarity filter (if specified)
            if sweep_config.min_rarity_score:
                if listing.rarity_score < sweep_config.min_rarity_score:
                    continue
            
            eligible.append(listing)
        
        return eligible

    def execute_batch_purchase(self, batch_listings, sweep_config):
        // TEST: Batch purchase optimizes gas costs
        // TEST: Batch purchase handles partial failures
        // TEST: Batch purchase respects slippage tolerance
        
        marketplace_integrator = get_marketplace_integrator()
        wallet_provider = get_wallet_provider()
        
        batch_result = BatchPurchaseResult(
            successful_purchases=[],
            failed_purchases=[],
            total_spent=0,
            gas_used=0
        )
        
        // Group by marketplace for batch optimization
        marketplace_groups = group_by_marketplace(batch_listings)
        
        for marketplace, listings in marketplace_groups.items():
            try:
                // Check if marketplace supports batch purchases
                if marketplace_integrator.supports_batch_purchase(marketplace):
                    result = self.execute_marketplace_batch(marketplace, listings, sweep_config)
                else:
                    result = self.execute_sequential_purchases(marketplace, listings, sweep_config)
                
                batch_result.merge(result)
                
            except Exception as e:
                log_error(f"Batch purchase failed for {marketplace}: {e}")
                
                // Mark all listings in this marketplace as failed
                for listing in listings:
                    batch_result.failed_purchases.append(
                        FailedPurchase(listing=listing, error=str(e))
                    )
        
        return batch_result
```

### TraitFilter (Rarity and Filtering)

```python
class TraitFilter:
    def __init__(self):
        // TEST: Trait filter initializes correctly
        self.rarity_cache = {}
        self.trait_value_cache = {}

    def filter_by_traits(self, nfts, trait_criteria):
        // TEST: Trait filtering applies AND/OR logic correctly
        // TEST: Trait filtering handles missing trait data
        // TEST: Trait filtering validates trait criteria format
        
        validate_trait_criteria(trait_criteria)
        
        filtered_nfts = []
        
        for nft in nfts:
            if self.matches_trait_criteria(nft, trait_criteria):
                filtered_nfts.append(nft)
        
        return filtered_nfts

    def matches_trait_criteria(self, nft, criteria):
        // TEST: Trait matching handles complex criteria correctly
        
        if criteria.operator == 'AND':
            return all(
                self.matches_single_criterion(nft, criterion)
                for criterion in criteria.conditions
            )
        elif criteria.operator == 'OR':
            return any(
                self.matches_single_criterion(nft, criterion)
                for criterion in criteria.conditions
            )
        else:
            raise InvalidTraitCriteriaError(f"Unknown operator: {criteria.operator}")

    def matches_single_criterion(self, nft, criterion):
        // TEST: Single criterion matching handles all comparison types
        
        trait_value = nft.traits.get(criterion.trait_type)
        
        if trait_value is None:
            return criterion.allow_missing
        
        if criterion.comparison == 'equals':
            return trait_value == criterion.value
        elif criterion.comparison == 'not_equals':
            return trait_value != criterion.value
        elif criterion.comparison == 'in':
            return trait_value in criterion.values
        elif criterion.comparison == 'not_in':
            return trait_value not in criterion.values
        elif criterion.comparison == 'rarity_percentile':
            rarity_percentile = self.get_trait_rarity_percentile(
                nft.collection_address,
                criterion.trait_type,
                trait_value
            )
            return rarity_percentile <= criterion.max_percentile
        else:
            raise InvalidTraitCriteriaError(f"Unknown comparison: {criterion.comparison}")

    def calculate_trait_values(self, nfts, collection_data):
        // TEST: Trait value calculation considers rarity and floor prices
        // TEST: Trait value calculation handles missing data gracefully
        
        trait_values = {}
        
        for nft in nfts:
            base_value = collection_data.floor_price
            rarity_multiplier = self.calculate_rarity_multiplier(nft, collection_data)
            trait_premium = self.calculate_trait_premium(nft, collection_data)
            
            estimated_value = base_value * rarity_multiplier + trait_premium
            trait_values[nft.token_id] = estimated_value
        
        return trait_values

    def calculate_rarity_multiplier(self, nft, collection_data):
        // TEST: Rarity multiplier calculation is consistent and reasonable
        
        if not nft.rarity_score:
            return 1.0
        
        // Normalize rarity score to multiplier (1.0 to 5.0 range)
        max_rarity = collection_data.max_rarity_score
        normalized_rarity = nft.rarity_score / max_rarity
        
        // Apply exponential curve for rare items
        multiplier = 1.0 + (normalized_rarity ** 2) * 4.0
        
        return min(multiplier, 5.0)  // Cap at 5x multiplier

    def analyze_rarity_distribution(self, collection_data):
        // TEST: Rarity analysis provides comprehensive statistics
        
        rarity_scores = [nft.rarity_score for nft in collection_data.nfts if nft.rarity_score]
        
        if not rarity_scores:
            return RarityAnalysis(error="No rarity data available")
        
        return RarityAnalysis(
            min_rarity=min(rarity_scores),
            max_rarity=max(rarity_scores),
            mean_rarity=statistics.mean(rarity_scores),
            median_rarity=statistics.median(rarity_scores),
            percentiles={
                p: statistics.quantiles(rarity_scores, n=100)[p-1]
                for p in [10, 25, 50, 75, 90, 95, 99]
            },
            trait_distribution=self.analyze_trait_distribution(collection_data)
        )
```

### BatchTransactionOptimizer (Gas Efficiency)

```python
class BatchTransactionOptimizer:
    def __init__(self, config):
        // TEST: Batch optimizer initializes with valid configuration
        self.config = config
        self.gas_estimator = GasEstimator()

    def create_purchase_batches(self, listings, max_items, gas_limit):
        // TEST: Batch creation respects gas limits
        // TEST: Batch creation optimizes for cost efficiency
        // TEST: Batch creation handles edge cases (single item, empty list)
        
        if not listings:
            return []
        
        batches = []
        current_batch = []
        current_gas_estimate = 0
        
        for listing in listings[:max_items]:
            estimated_gas = self.gas_estimator.estimate_purchase_gas(listing)
            
            // Check if adding this item would exceed gas limit
            if (current_gas_estimate + estimated_gas > gas_limit and current_batch):
                // Finalize current batch
                batches.append(current_batch)
                current_batch = [listing]
                current_gas_estimate = estimated_gas
            else:
                current_batch.append(listing)
                current_gas_estimate += estimated_gas
        
        // Add final batch if not empty
        if current_batch:
            batches.append(current_batch)
        
        return batches

    def optimize_batch_order(self, batch_listings):
        // TEST: Batch ordering optimizes for success probability
        // TEST: Batch ordering considers marketplace-specific factors
        
        // Sort by factors that increase success probability:
        // 1. Marketplace reliability
        // 2. Listing freshness
        // 3. Price (lower first to avoid being outbid)
        
        marketplace_reliability = {
            'opensea': 0.95,
            'looksrare': 0.90,
            'blur': 0.85,
            'x2y2': 0.80
        }
        
        def sort_key(listing):
            reliability = marketplace_reliability.get(listing.marketplace, 0.5)
            freshness = 1.0 / (current_timestamp() - listing.fetched_at + 1)
            price_factor = 1.0 / (listing.price + 1)
            
            return -(reliability * freshness * price_factor)
        
        return sorted(batch_listings, key=sort_key)
```

## TDD Anchor Summary

### Core Functionality Tests
1. **NFTManager Initialization**: Validates proper setup with wallet provider and configuration
2. **Floor Sweep Execution**: Tests complete sweep workflow with various parameters
3. **Trait-Based Filtering**: Validates complex trait criteria and rarity calculations
4. **Marketplace Integration**: Tests API interactions and rate limiting
5. **Batch Optimization**: Validates gas efficiency and transaction grouping

### Edge Case Tests
6. **Invalid Collection Addresses**: Handles malformed or non-existent collections
7. **Empty Marketplace Data**: Graceful handling when no listings available
8. **Rate Limit Handling**: Proper backoff and retry mechanisms
9. **Transaction Failures**: Recovery and error reporting for failed purchases
10. **Network Congestion**: Adaptive gas pricing and timeout handling

### Security Tests
11. **Input Validation**: All user inputs properly sanitized and validated
12. **Risk Limit Enforcement**: Position sizes and spending limits respected
13. **Slippage Protection**: Price changes handled during execution
14. **Wallet Security**: No private key exposure or unauthorized transactions

### Performance Tests
15. **Concurrent Operations**: Multiple sweeps and purchases handled efficiently
16. **Cache Effectiveness**: Marketplace data caching reduces API calls
17. **Gas Optimization**: Batch transactions achieve target cost savings
18. **Response Times**: All operations complete within acceptable timeframes

## Integration Points

### Phase 1 Dependencies
- **WalletProvider Interface**: Extends existing wallet abstraction
- **Event System**: Emits NFT-specific events for monitoring
- **Risk Management**: Integrates with existing risk limits and controls
- **Configuration**: Uses environment-based configuration system

### External Integrations
- **OpenSea API**: Collection data, listings, and purchase execution
- **LooksRare API**: Alternative marketplace data and transactions
- **Blur API**: High-frequency trading and professional tools
- **X2Y2 API**: Additional marketplace coverage and arbitrage

### Error Handling Strategy
- **Graceful Degradation**: Continue operation when individual marketplaces fail
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascade failures across marketplaces
- **Comprehensive Logging**: Detailed audit trail for all operations