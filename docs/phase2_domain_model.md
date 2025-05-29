# Phase 2: Asset Class Expansion - Domain Model

## Overview

This domain model defines the core entities, relationships, and data structures for Phase 2's advanced asset classes: NFTs, DeFi instruments, derivatives, and cross-chain operations.

## Domain Glossary

### Core Terms
- **Asset Manager**: Specialized component managing specific asset class operations
- **Floor Sweep**: Automated purchase of lowest-priced NFTs in a collection
- **Yield Farming**: Strategy to maximize returns through DeFi protocol participation
- **Impermanent Loss**: Temporary loss from providing liquidity vs holding assets
- **Greeks**: Risk sensitivities for options (Delta, Gamma, Theta, Vega)
- **Cross-Chain Arbitrage**: Exploiting price differences across blockchain networks

### Technical Terms
- **Trait Rarity**: Statistical measure of NFT attribute uniqueness
- **APY**: Annual Percentage Yield from DeFi protocols
- **Slippage**: Price difference between expected and executed trade
- **Bridge Protocol**: Infrastructure enabling cross-chain asset transfers
- **Perpetual Futures**: Derivative contracts without expiration dates

## Core Entities

### 1. Asset Manager Entities

#### AssetManager (Abstract Base)
```
AssetManager {
  manager_id: string (unique identifier)
  asset_type: AssetType (NFT, DEFI, DERIVATIVES, CROSS_CHAIN)
  status: ManagerStatus (ACTIVE, PAUSED, ERROR, MAINTENANCE)
  wallet_provider: WalletProvider (from Phase 1)
  risk_limits: RiskLimits
  configuration: ManagerConfig
  created_at: timestamp
  updated_at: timestamp
}

Relationships:
- extends WalletProvider interface
- manages multiple AssetPositions
- emits AssetEvents
- integrates with RiskManager
```

#### NFTManager
```
NFTManager extends AssetManager {
  supported_marketplaces: List[Marketplace]
  collection_filters: CollectionFilters
  trait_preferences: TraitPreferences
  sweep_config: SweepConfiguration
  batch_size: integer (max NFTs per transaction)
}

Relationships:
- manages NFTCollections
- executes NFTTransactions
- monitors MarketplaceEvents
```

#### DeFiManager
```
DeFiManager extends AssetManager {
  supported_protocols: List[DeFiProtocol]
  yield_strategy: YieldStrategy
  rebalance_threshold: decimal (percentage)
  compound_frequency: duration
  il_protection: boolean
}

Relationships:
- manages LiquidityPositions
- monitors YieldOpportunities
- executes ProtocolTransactions
```

#### DerivativesManager
```
DerivativesManager extends AssetManager {
  supported_platforms: List[DerivativesPlatform]
  leverage_limits: LeverageLimits
  position_sizing: PositionSizingStrategy
  risk_metrics: RiskMetrics
  auto_close_rules: AutoCloseRules
}

Relationships:
- manages DerivativePositions
- calculates OptionsGreeks
- monitors LiquidationRisk
```

#### CrossChainManager
```
CrossChainManager extends AssetManager {
  supported_chains: List[ChainId]
  bridge_preferences: BridgePreferences
  arbitrage_threshold: decimal (minimum profit percentage)
  gas_optimization: GasOptimizationConfig
}

Relationships:
- manages CrossChainPositions
- monitors BridgeStatus
- executes ArbitrageOpportunities
```

### 2. Asset-Specific Entities

#### NFT Domain

##### NFTCollection
```
NFTCollection {
  collection_id: string
  contract_address: string
  chain_id: integer
  name: string
  symbol: string
  total_supply: integer
  floor_price: Price
  volume_24h: decimal
  traits: List[TraitDefinition]
  marketplace_data: Map[Marketplace, MarketplaceData]
  last_updated: timestamp
}

Relationships:
- contains multiple NFTAssets
- tracked across multiple Marketplaces
- has associated TraitRarities
```

##### NFTAsset
```
NFTAsset {
  token_id: string
  collection_id: string
  owner_address: string
  metadata_uri: string
  traits: Map[string, string]
  rarity_score: decimal
  last_sale_price: Price
  current_listing: Listing (optional)
  price_history: List[PricePoint]
}

Relationships:
- belongs to NFTCollection
- has multiple Listings across marketplaces
- tracked in PriceHistory
```

##### TraitDefinition
```
TraitDefinition {
  trait_type: string
  possible_values: List[string]
  rarity_distribution: Map[string, decimal]
  floor_prices: Map[string, Price]
}

Relationships:
- defines traits for NFTCollection
- used in RarityCalculation
```

#### DeFi Domain

##### DeFiProtocol
```
DeFiProtocol {
  protocol_id: string
  name: string
  protocol_type: ProtocolType (LENDING, DEX, YIELD_FARM, STAKING)
  chain_id: integer
  contract_addresses: Map[string, string]
  supported_tokens: List[TokenAddress]
  current_apy: decimal
  tvl: decimal
  risk_score: decimal
  audit_status: AuditStatus
}

Relationships:
- offers multiple YieldOpportunities
- supports various TokenPairs
- has associated RiskMetrics
```

##### LiquidityPosition
```
LiquidityPosition {
  position_id: string
  protocol_id: string
  token_pair: TokenPair
  liquidity_amount: decimal
  entry_price: Price
  current_value: decimal
  impermanent_loss: decimal
  rewards_earned: decimal
  apy_current: decimal
  created_at: timestamp
}

Relationships:
- managed by DeFiManager
- tracks ImpermanentLoss
- generates RewardEvents
```

##### YieldOpportunity
```
YieldOpportunity {
  opportunity_id: string
  protocol_id: string
  token_pair: TokenPair
  apy: decimal
  risk_score: decimal
  liquidity_required: decimal
  entry_conditions: EntryConditions
  exit_conditions: ExitConditions
  discovered_at: timestamp
  expires_at: timestamp (optional)
}

Relationships:
- offered by DeFiProtocol
- evaluated by YieldStrategy
- may become LiquidityPosition
```

#### Derivatives Domain

##### DerivativesPlatform
```
DerivativesPlatform {
  platform_id: string
  name: string
  platform_type: PlatformType (PERPS, OPTIONS, FUTURES)
  chain_id: integer
  supported_assets: List[string]
  max_leverage: decimal
  funding_rate: decimal (for perps)
  insurance_fund: decimal
  api_endpoints: Map[string, string]
}

Relationships:
- hosts multiple DerivativePositions
- provides MarketData
- has associated RiskParameters
```

##### DerivativePosition
```
DerivativePosition {
  position_id: string
  platform_id: string
  asset_symbol: string
  position_type: PositionType (LONG, SHORT)
  size: decimal
  entry_price: decimal
  current_price: decimal
  leverage: decimal
  margin_required: decimal
  unrealized_pnl: decimal
  liquidation_price: decimal
  created_at: timestamp
}

Relationships:
- traded on DerivativesPlatform
- monitored by RiskManager
- generates PnLEvents
```

##### OptionsContract
```
OptionsContract {
  contract_id: string
  underlying_asset: string
  strike_price: decimal
  expiration_date: timestamp
  option_type: OptionType (CALL, PUT)
  premium: decimal
  greeks: OptionsGreeks
  implied_volatility: decimal
  open_interest: integer
}

Relationships:
- part of OptionsStrategy
- has calculated OptionsGreeks
- tracked in VolatilityData
```

##### OptionsGreeks
```
OptionsGreeks {
  delta: decimal (price sensitivity)
  gamma: decimal (delta sensitivity)
  theta: decimal (time decay)
  vega: decimal (volatility sensitivity)
  rho: decimal (interest rate sensitivity)
  calculated_at: timestamp
}

Relationships:
- calculated for OptionsContract
- used in RiskCalculations
```

#### Cross-Chain Domain

##### BridgeProtocol
```
BridgeProtocol {
  bridge_id: string
  name: string
  supported_chains: List[ChainId]
  supported_assets: List[TokenAddress]
  bridge_fee: decimal
  transfer_time: duration
  security_score: decimal
  daily_volume_limit: decimal
  status: BridgeStatus (ACTIVE, MAINTENANCE, DEPRECATED)
}

Relationships:
- facilitates CrossChainTransfers
- has associated SecurityMetrics
- tracks TransferHistory
```

##### CrossChainTransfer
```
CrossChainTransfer {
  transfer_id: string
  bridge_id: string
  source_chain: ChainId
  destination_chain: ChainId
  asset_address: string
  amount: decimal
  source_tx_hash: string
  destination_tx_hash: string (optional)
  status: TransferStatus
  initiated_at: timestamp
  completed_at: timestamp (optional)
}

Relationships:
- uses BridgeProtocol
- part of ArbitrageOpportunity
- tracked in TransferHistory
```

##### ArbitrageOpportunity
```
ArbitrageOpportunity {
  opportunity_id: string
  asset_symbol: string
  source_chain: ChainId
  destination_chain: ChainId
  source_price: Price
  destination_price: Price
  profit_percentage: decimal
  bridge_cost: decimal
  gas_cost: decimal
  net_profit: decimal
  execution_time: duration
  discovered_at: timestamp
  expires_at: timestamp
}

Relationships:
- requires CrossChainTransfer
- evaluated by ArbitrageStrategy
- may become ArbitrageExecution
```

### 3. Supporting Entities

#### Price and Market Data

##### Price
```
Price {
  amount: decimal
  currency: string (ETH, USD, etc.)
  timestamp: timestamp
  source: string (marketplace/exchange)
}

Relationships:
- used across all asset types
- tracked in PriceHistory
```

##### MarketData
```
MarketData {
  asset_identifier: string
  price: Price
  volume_24h: decimal
  price_change_24h: decimal
  market_cap: decimal (optional)
  liquidity: decimal
  last_updated: timestamp
}

Relationships:
- aggregated from multiple sources
- used in trading decisions
```

#### Risk Management

##### RiskLimits
```
RiskLimits {
  max_position_size: decimal
  max_daily_loss: decimal
  max_leverage: decimal
  max_slippage: decimal
  stop_loss_percentage: decimal
  take_profit_percentage: decimal
}

Relationships:
- enforced by RiskManager
- configured per AssetManager
```

##### RiskMetrics
```
RiskMetrics {
  var_95: decimal (Value at Risk)
  expected_shortfall: decimal
  sharpe_ratio: decimal
  max_drawdown: decimal
  volatility: decimal
  correlation_matrix: Map[string, decimal]
  calculated_at: timestamp
}

Relationships:
- calculated for portfolios
- used in risk assessment
```

#### Configuration and Strategy

##### ManagerConfig
```
ManagerConfig {
  auto_trading_enabled: boolean
  max_concurrent_positions: integer
  rebalance_frequency: duration
  notification_preferences: NotificationConfig
  api_rate_limits: Map[string, integer]
  environment_variables: Map[string, string]
}

Relationships:
- configures AssetManager behavior
- loaded from environment
```

##### TradingStrategy
```
TradingStrategy {
  strategy_id: string
  strategy_type: StrategyType
  parameters: Map[string, any]
  entry_conditions: List[Condition]
  exit_conditions: List[Condition]
  risk_parameters: RiskParameters
  performance_metrics: PerformanceMetrics
}

Relationships:
- implemented by AssetManagers
- evaluated against market conditions
```

## Entity Relationships

### Inheritance Hierarchy
```
WalletProvider (Phase 1)
  └── AssetManager (Abstract)
      ├── NFTManager
      ├── DeFiManager
      ├── DerivativesManager
      └── CrossChainManager
```

### Aggregation Relationships
```
AssetManager
  ├── manages → AssetPositions
  ├── uses → RiskLimits
  ├── emits → AssetEvents
  └── integrates → WalletProvider

NFTManager
  ├── monitors → NFTCollections
  ├── executes → NFTTransactions
  └── tracks → TraitRarities

DeFiManager
  ├── manages → LiquidityPositions
  ├── monitors → YieldOpportunities
  └── calculates → ImpermanentLoss

DerivativesManager
  ├── manages → DerivativePositions
  ├── calculates → OptionsGreeks
  └── monitors → RiskMetrics

CrossChainManager
  ├── monitors → ArbitrageOpportunities
  ├── executes → CrossChainTransfers
  └── uses → BridgeProtocols
```

## State Transitions

### Asset Manager States
```
INITIALIZING → ACTIVE → PAUSED → ACTIVE
INITIALIZING → ERROR → MAINTENANCE → ACTIVE
ACTIVE → ERROR → MAINTENANCE → ACTIVE
PAUSED → MAINTENANCE → ACTIVE
```

### Position States
```
PENDING → OPEN → CLOSED
PENDING → FAILED
OPEN → LIQUIDATED
OPEN → PARTIALLY_CLOSED → CLOSED
```

### Transfer States
```
INITIATED → PENDING → CONFIRMED → COMPLETED
INITIATED → PENDING → FAILED
INITIATED → EXPIRED
```

## Data Validation Rules

### Universal Rules
- All monetary amounts must be non-negative
- All percentages must be between 0 and 100
- All timestamps must be valid UTC timestamps
- All addresses must be valid for their respective chains

### Asset-Specific Rules
- NFT token IDs must be unique within collections
- DeFi APY values must be realistic (0-1000%)
- Leverage ratios must not exceed platform limits
- Bridge transfers must respect daily volume limits

### Risk Management Rules
- Position sizes must not exceed risk limits
- Total portfolio exposure must stay within bounds
- Stop-loss orders must be set for leveraged positions
- Slippage tolerance must be reasonable (0-50%)

## Event Flows

### NFT Floor Sweep Flow
```
MarketDataUpdate → FloorPriceCalculation → SweepOpportunityDetection → 
RiskValidation → BatchTransactionCreation → ExecutionConfirmation → 
PositionUpdate → EventEmission
```

### DeFi Yield Optimization Flow
```
ProtocolScan → YieldCalculation → RiskAssessment → 
CapitalAllocation → PositionEntry → PerformanceMonitoring → 
RebalanceTrigger → PositionAdjustment
```

### Derivatives Trading Flow
```
MarketAnalysis → SignalGeneration → RiskValidation → 
PositionSizing → OrderPlacement → ExecutionConfirmation → 
PnLCalculation → RiskMonitoring → PositionManagement
```

### Cross-Chain Arbitrage Flow
```
PriceDiscoveryAcrossChains → ArbitrageCalculation → 
ProfitabilityValidation → BridgeSelection → TransferInitiation → 
StatusMonitoring → CompletionConfirmation → ProfitRealization
```

## Integration Points

### Phase 1 Integration
- Extends WalletProvider interface for all asset managers
- Leverages existing connection management and event systems
- Integrates with established risk management infrastructure
- Uses existing monitoring and logging systems

### External System Integration
- NFT marketplaces via REST APIs and WebSocket feeds
- DeFi protocols via smart contract interactions
- Derivatives platforms via trading APIs
- Bridge protocols via cross-chain messaging

### Internal System Integration
- Risk management system for position monitoring
- Event system for real-time updates
- Configuration system for environment-based settings
- Monitoring system for performance tracking

## Performance Considerations

### Caching Strategy
- Market data cached for 30 seconds
- Collection metadata cached for 5 minutes
- Protocol data cached for 1 minute
- Risk calculations cached for 10 seconds

### Scalability Requirements
- Support 1000+ concurrent price feeds
- Handle 100+ simultaneous positions
- Process 10,000+ events per minute
- Maintain <100ms response times

### Data Storage
- Time-series data for price history
- Relational data for positions and configurations
- Document storage for metadata and traits
- Cache storage for frequently accessed data