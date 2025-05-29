# Phase 1: Domain Model Specification

## Overview

This document defines the core domain entities, relationships, and data structures for Phase 1: Foundational Wallet & Fiat Integration of the Grekko DeFi trading platform.

## Core Domain Entities

### 1. Wallet Provider Entity

```typescript
// Core wallet provider abstraction
interface WalletProvider {
  // Identity attributes
  providerId: string           // Unique identifier (e.g., "metamask", "coinbase", "walletconnect")
  name: string                // Human-readable name
  version: string             // Provider version
  icon: string                // Provider icon URL
  
  // Capability attributes
  supportedChains: ChainId[]  // Supported blockchain networks
  capabilities: WalletCapability[]  // Available features
  connectionMethods: ConnectionMethod[]  // How to connect
  
  // State attributes
  isAvailable: boolean        // Provider availability
  isConnected: boolean        // Connection status
  lastConnected: Date         // Last connection timestamp
  
  // Configuration
  config: ProviderConfig      // Provider-specific configuration
}

enum WalletCapability {
  SIGN_MESSAGE = "sign_message",
  SIGN_TRANSACTION = "sign_transaction", 
  SEND_TRANSACTION = "send_transaction",
  SWITCH_CHAIN = "switch_chain",
  ADD_CHAIN = "add_chain",
  WATCH_ASSET = "watch_asset",
  FIAT_ONRAMP = "fiat_onramp"
}

enum ConnectionMethod {
  BROWSER_EXTENSION = "browser_extension",
  MOBILE_APP = "mobile_app", 
  QR_CODE = "qr_code",
  DEEP_LINK = "deep_link",
  WEB_INTERFACE = "web_interface"
}
```

### 2. Wallet Connection Entity

```typescript
// Active wallet connection state
interface WalletConnection {
  // Connection identity
  connectionId: string        // Unique connection identifier
  providerId: string          // Associated wallet provider
  sessionId: string           // Session identifier
  
  // Account information
  accounts: Account[]         // Connected accounts
  activeAccount: string       // Currently active account address
  
  // Network information
  chainId: ChainId           // Current blockchain network
  networkName: string        // Network display name
  rpcUrl: string             // RPC endpoint URL
  
  // Connection metadata
  connectedAt: Date          // Connection timestamp
  lastActivity: Date         // Last activity timestamp
  expiresAt: Date            // Session expiration
  
  // Connection state
  status: ConnectionStatus   // Current connection status
  permissions: Permission[]  // Granted permissions
  
  // Provider-specific data
  providerData: Record<string, any>  // Provider-specific information
}

enum ConnectionStatus {
  CONNECTING = "connecting",
  CONNECTED = "connected",
  DISCONNECTING = "disconnecting", 
  DISCONNECTED = "disconnected",
  ERROR = "error",
  EXPIRED = "expired"
}

interface Account {
  address: string            // Account address
  name?: string              // Account name/label
  balance: TokenBalance[]    // Token balances
  isActive: boolean          // Is currently active account
}
```

### 3. Transaction Entity

```typescript
// Transaction request and execution tracking
interface Transaction {
  // Transaction identity
  transactionId: string      // Internal transaction ID
  hash?: string              // Blockchain transaction hash
  nonce?: number             // Transaction nonce
  
  // Transaction details
  from: string               // Sender address
  to: string                 // Recipient address
  value: BigNumber           // Transaction value
  data?: string              // Transaction data/input
  
  // Gas configuration
  gasLimit: BigNumber        // Gas limit
  gasPrice?: BigNumber       // Gas price (legacy)
  maxFeePerGas?: BigNumber   // EIP-1559 max fee
  maxPriorityFeePerGas?: BigNumber  // EIP-1559 priority fee
  
  // Transaction metadata
  chainId: ChainId           // Target blockchain
  type: TransactionType      // Transaction type
  status: TransactionStatus  // Current status
  
  // Timing information
  createdAt: Date            // Creation timestamp
  submittedAt?: Date         // Submission timestamp
  confirmedAt?: Date         // Confirmation timestamp
  
  // Execution details
  blockNumber?: number       // Block number
  blockHash?: string         // Block hash
  transactionIndex?: number  // Transaction index in block
  gasUsed?: BigNumber        // Actual gas used
  effectiveGasPrice?: BigNumber  // Effective gas price
  
  // Error handling
  error?: TransactionError   // Error information if failed
  retryCount: number         // Number of retry attempts
}

enum TransactionType {
  TRANSFER = "transfer",
  CONTRACT_CALL = "contract_call",
  CONTRACT_DEPLOYMENT = "contract_deployment",
  FIAT_ONRAMP = "fiat_onramp",
  SWAP = "swap",
  BRIDGE = "bridge"
}

enum TransactionStatus {
  PENDING = "pending",
  SUBMITTED = "submitted", 
  CONFIRMED = "confirmed",
  FAILED = "failed",
  CANCELLED = "cancelled",
  REPLACED = "replaced"
}
```

### 4. Asset and Balance Entity

```typescript
// Token and asset representation
interface Asset {
  // Asset identity
  assetId: string            // Unique asset identifier
  symbol: string             // Asset symbol (e.g., "ETH", "USDC")
  name: string               // Full asset name
  
  // Asset metadata
  decimals: number           // Token decimals
  logoUrl?: string           // Asset logo URL
  description?: string       // Asset description
  
  // Contract information
  contractAddress?: string   // Token contract address
  chainId: ChainId           // Blockchain network
  
  // Asset classification
  type: AssetType            // Asset type
  category: AssetCategory    // Asset category
  
  // Market data
  price?: Price              // Current price information
  marketCap?: BigNumber      // Market capitalization
  volume24h?: BigNumber      // 24-hour trading volume
  
  // Metadata
  isVerified: boolean        // Is verified asset
  tags: string[]             // Asset tags
  createdAt: Date            // Asset creation timestamp
}

interface TokenBalance {
  // Balance identity
  assetId: string            // Asset identifier
  address: string            // Account address
  chainId: ChainId           // Blockchain network
  
  // Balance information
  balance: BigNumber         // Raw balance amount
  formattedBalance: string   // Human-readable balance
  usdValue?: BigNumber       // USD value
  
  // Balance metadata
  lastUpdated: Date          // Last update timestamp
  isStale: boolean           // Is balance data stale
  
  // Additional information
  allowances?: Allowance[]   // Token allowances
  stakingInfo?: StakingInfo  // Staking information
}

enum AssetType {
  NATIVE = "native",         // Native blockchain token
  ERC20 = "erc20",          // ERC-20 token
  ERC721 = "erc721",        // NFT
  ERC1155 = "erc1155",      // Multi-token
  LP_TOKEN = "lp_token"     // Liquidity provider token
}

enum AssetCategory {
  CURRENCY = "currency",
  STABLECOIN = "stablecoin",
  DEFI = "defi",
  NFT = "nft",
  GAMING = "gaming",
  MEME = "meme"
}
```

### 5. Fiat Onramp Entity

```typescript
// Fiat-to-crypto conversion tracking
interface FiatOnramp {
  // Onramp identity
  onrampId: string           // Unique onramp transaction ID
  providerId: string         // Onramp provider (e.g., "coinbase")
  externalId: string         // Provider's transaction ID
  
  // Transaction details
  fiatAmount: BigNumber      // Fiat amount
  fiatCurrency: string       // Fiat currency code
  cryptoAmount: BigNumber    // Crypto amount received
  cryptoAsset: string        // Crypto asset symbol
  
  // User information
  userId: string             // User identifier
  destinationAddress: string // Crypto destination address
  
  // KYC/Compliance
  kycStatus: KYCStatus       // KYC verification status
  complianceChecks: ComplianceCheck[]  // Compliance verifications
  
  // Status tracking
  status: OnrampStatus       // Current onramp status
  statusHistory: StatusUpdate[]  // Status change history
  
  // Timing information
  initiatedAt: Date          // Initiation timestamp
  completedAt?: Date         // Completion timestamp
  expiresAt: Date            // Expiration timestamp
  
  // Financial information
  fees: Fee[]                // Associated fees
  exchangeRate: BigNumber    // Fiat to crypto exchange rate
  
  // Error handling
  error?: OnrampError        // Error information if failed
}

enum KYCStatus {
  NOT_STARTED = "not_started",
  IN_PROGRESS = "in_progress",
  PENDING_REVIEW = "pending_review",
  APPROVED = "approved",
  REJECTED = "rejected",
  EXPIRED = "expired"
}

enum OnrampStatus {
  INITIATED = "initiated",
  KYC_REQUIRED = "kyc_required",
  PAYMENT_PENDING = "payment_pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled"
}
```

### 6. Event Entity

```typescript
// System event tracking
interface DomainEvent {
  // Event identity
  eventId: string            // Unique event identifier
  eventType: string          // Event type
  aggregateId: string        // Related aggregate ID
  aggregateType: string      // Aggregate type
  
  // Event data
  eventData: Record<string, any>  // Event payload
  metadata: EventMetadata    // Event metadata
  
  // Timing information
  timestamp: Date            // Event timestamp
  version: number            // Event version
  
  // Correlation
  correlationId?: string     // Correlation identifier
  causationId?: string       // Causation identifier
}

interface EventMetadata {
  userId?: string            // Associated user
  sessionId?: string         // Session identifier
  source: string             // Event source
  ipAddress?: string         // Client IP address
  userAgent?: string         // Client user agent
}

// Specific event types
interface WalletConnectedEvent extends DomainEvent {
  eventType: "wallet.connected"
  eventData: {
    providerId: string
    connectionId: string
    accounts: string[]
    chainId: ChainId
  }
}

interface TransactionSubmittedEvent extends DomainEvent {
  eventType: "transaction.submitted"
  eventData: {
    transactionId: string
    hash: string
    from: string
    to: string
    value: string
    chainId: ChainId
  }
}

interface OnrampCompletedEvent extends DomainEvent {
  eventType: "onramp.completed"
  eventData: {
    onrampId: string
    fiatAmount: string
    cryptoAmount: string
    destinationAddress: string
  }
}
```

## Domain Relationships

### 1. Wallet Provider Relationships

```
WalletProvider (1) ←→ (0..*) WalletConnection
WalletProvider (1) ←→ (0..*) Transaction
WalletConnection (1) ←→ (0..*) Account
Account (1) ←→ (0..*) TokenBalance
```

### 2. Transaction Relationships

```
WalletConnection (1) ←→ (0..*) Transaction
Transaction (1) ←→ (0..*) DomainEvent
Asset (1) ←→ (0..*) Transaction
```

### 3. Asset Relationships

```
Asset (1) ←→ (0..*) TokenBalance
Asset (1) ←→ (0..*) FiatOnramp
ChainId (1) ←→ (0..*) Asset
```

### 4. Event Relationships

```
DomainEvent (1) ←→ (1) EventMetadata
WalletConnection (1) ←→ (0..*) DomainEvent
Transaction (1) ←→ (0..*) DomainEvent
FiatOnramp (1) ←→ (0..*) DomainEvent
```

## Domain Aggregates

### 1. Wallet Aggregate

**Root Entity**: WalletProvider
**Aggregate Boundary**: 
- WalletProvider
- WalletConnection
- Account
- TokenBalance

**Business Rules**:
- Only one active connection per provider per user
- Account balances must be consistent across the aggregate
- Connection state changes must be atomic
- Provider capabilities determine available operations

### 2. Transaction Aggregate

**Root Entity**: Transaction
**Aggregate Boundary**:
- Transaction
- TransactionError
- StatusUpdate

**Business Rules**:
- Transaction state transitions must follow valid paths
- Gas configuration must be valid for target network
- Retry attempts must respect maximum limits
- Transaction hash must be unique per network

### 3. Onramp Aggregate

**Root Entity**: FiatOnramp
**Aggregate Boundary**:
- FiatOnramp
- ComplianceCheck
- Fee
- StatusUpdate

**Business Rules**:
- KYC must be completed before processing
- Exchange rates must be within acceptable bounds
- Compliance checks must pass before completion
- Status transitions must follow regulatory requirements

## Domain Services

### 1. Wallet Connection Service

```typescript
interface WalletConnectionService {
  // Connection management
  establishConnection(providerId: string, options: ConnectionOptions): Promise<WalletConnection>
  terminateConnection(connectionId: string): Promise<void>
  refreshConnection(connectionId: string): Promise<WalletConnection>
  
  // State synchronization
  syncAccountBalances(connectionId: string): Promise<TokenBalance[]>
  syncNetworkState(connectionId: string): Promise<void>
  
  // Event handling
  handleProviderEvents(connectionId: string, event: ProviderEvent): Promise<void>
}
```

### 2. Transaction Coordination Service

```typescript
interface TransactionCoordinationService {
  // Transaction lifecycle
  prepareTransaction(request: TransactionRequest): Promise<Transaction>
  submitTransaction(transactionId: string): Promise<string>
  monitorTransaction(transactionId: string): Promise<TransactionStatus>
  
  // Cross-wallet coordination
  coordinateMultiWalletTransaction(requests: TransactionRequest[]): Promise<Transaction[]>
  
  // Gas optimization
  estimateOptimalGas(transaction: Transaction): Promise<GasEstimate>
}
```

### 3. Asset Management Service

```typescript
interface AssetManagementService {
  // Asset discovery
  discoverAssets(chainId: ChainId): Promise<Asset[]>
  resolveAsset(identifier: string): Promise<Asset>
  
  // Price and market data
  updateAssetPrices(assetIds: string[]): Promise<Price[]>
  calculatePortfolioValue(balances: TokenBalance[]): Promise<BigNumber>
  
  // Balance management
  updateBalances(address: string, chainId: ChainId): Promise<TokenBalance[]>
}
```

## Domain Value Objects

### 1. Chain Configuration

```typescript
interface ChainConfig {
  chainId: ChainId
  name: string
  symbol: string
  rpcUrls: string[]
  blockExplorerUrls: string[]
  iconUrls?: string[]
  nativeCurrency: {
    name: string
    symbol: string
    decimals: number
  }
}
```

### 2. Gas Estimate

```typescript
interface GasEstimate {
  gasLimit: BigNumber
  gasPrice?: BigNumber
  maxFeePerGas?: BigNumber
  maxPriorityFeePerGas?: BigNumber
  estimatedCost: BigNumber
  confidence: number
}
```

### 3. Price Information

```typescript
interface Price {
  assetId: string
  price: BigNumber
  currency: string
  timestamp: Date
  source: string
  confidence: number
}
```

## Domain Invariants

### 1. Wallet Provider Invariants

- Provider ID must be unique across the system
- Supported chains list cannot be empty
- Provider must have at least one connection method
- Provider version must follow semantic versioning

### 2. Connection Invariants

- Connection ID must be unique per session
- Active account must be in the accounts list
- Chain ID must be supported by the provider
- Session cannot expire before creation time

### 3. Transaction Invariants

- Transaction hash must be unique per chain
- Gas limit must be positive
- From address must be a connected account
- Transaction value cannot exceed account balance

### 4. Balance Invariants

- Balance cannot be negative
- Decimals must match asset configuration
- Last updated timestamp cannot be in the future
- USD value must be calculated using current prices

## Domain Events

### 1. Wallet Events

- WalletProviderRegistered
- WalletConnected
- WalletDisconnected
- AccountChanged
- NetworkChanged
- BalanceUpdated

### 2. Transaction Events

- TransactionCreated
- TransactionSubmitted
- TransactionConfirmed
- TransactionFailed
- TransactionCancelled

### 3. Onramp Events

- OnrampInitiated
- KYCCompleted
- PaymentReceived
- OnrampCompleted
- OnrampFailed

### 4. System Events

- AssetDiscovered
- PriceUpdated
- ErrorOccurred
- PerformanceMetricRecorded

---

*This domain model serves as the foundation for implementing Phase 1 components with clear boundaries, relationships, and business rules.*