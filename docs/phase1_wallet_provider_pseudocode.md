# Phase 1: WalletProvider Abstraction Layer - Pseudocode Specification

## Overview

This document provides the pseudocode specification for the WalletProvider abstraction layer, which serves as the unified interface for all wallet integrations (Coinbase, MetaMask, WalletConnect) in Phase 1.

## Module: WalletProvider Interface

```pseudocode
// Core wallet provider abstraction interface
INTERFACE WalletProvider {
    // Identity properties
    READONLY providerId: String
    READONLY name: String
    READONLY version: String
    READONLY supportedChains: Array<ChainId>
    READONLY capabilities: Array<WalletCapability>
    
    // State properties
    isAvailable: Boolean
    isConnected: Boolean
    connectionState: ConnectionState
    
    // Core methods
    FUNCTION connect(options: ConnectionOptions): Promise<WalletConnection>
    FUNCTION disconnect(): Promise<Void>
    FUNCTION getAccounts(): Promise<Array<Account>>
    FUNCTION switchChain(chainId: ChainId): Promise<Void>
    FUNCTION signMessage(message: String): Promise<String>
    FUNCTION signTransaction(transaction: TransactionRequest): Promise<SignedTransaction>
    FUNCTION sendTransaction(transaction: TransactionRequest): Promise<TransactionHash>
    
    // Event handling
    FUNCTION addEventListener(event: WalletEvent, handler: EventHandler): Void
    FUNCTION removeEventListener(event: WalletEvent, handler: EventHandler): Void
    FUNCTION emit(event: WalletEvent, data: Any): Void
}

ENUM WalletCapability {
    SIGN_MESSAGE,
    SIGN_TRANSACTION,
    SEND_TRANSACTION,
    SWITCH_CHAIN,
    ADD_CHAIN,
    WATCH_ASSET,
    FIAT_ONRAMP
}

ENUM ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    RECONNECTING,
    ERROR
}
```

## Module: WalletProviderRegistry

```pseudocode
// Central registry for managing wallet providers
CLASS WalletProviderRegistry {
    PRIVATE providers: Map<String, WalletProvider>
    PRIVATE eventBus: EventBus
    PRIVATE logger: Logger
    
    // TEST: Registry should initialize with empty provider map
    CONSTRUCTOR() {
        this.providers = NEW Map()
        this.eventBus = NEW EventBus()
        this.logger = NEW Logger("WalletProviderRegistry")
    }
    
    // TEST: Should successfully register valid wallet provider
    // TEST: Should reject duplicate provider registration
    // TEST: Should validate provider interface compliance
    FUNCTION registerProvider(provider: WalletProvider): Result<Void, RegistrationError> {
        // Input validation
        IF provider IS NULL OR provider.providerId IS EMPTY {
            RETURN Error(INVALID_PROVIDER)
        }
        
        // Check for duplicates
        IF this.providers.has(provider.providerId) {
            RETURN Error(DUPLICATE_PROVIDER)
        }
        
        // Validate provider interface
        IF NOT this.validateProviderInterface(provider) {
            RETURN Error(INVALID_INTERFACE)
        }
        
        // Register provider
        this.providers.set(provider.providerId, provider)
        this.setupProviderEventHandlers(provider)
        
        // Emit registration event
        this.eventBus.emit("provider.registered", {
            providerId: provider.providerId,
            capabilities: provider.capabilities
        })
        
        this.logger.info("Provider registered", { providerId: provider.providerId })
        RETURN Success()
    }
    
    // TEST: Should return provider for valid ID
    // TEST: Should return null for invalid ID
    FUNCTION getProvider(providerId: String): WalletProvider? {
        RETURN this.providers.get(providerId)
    }
    
    // TEST: Should return all registered providers
    // TEST: Should return empty array when no providers registered
    FUNCTION getAllProviders(): Array<WalletProvider> {
        RETURN Array.from(this.providers.values())
    }
    
    // TEST: Should return only available providers
    // TEST: Should filter out unavailable providers
    FUNCTION getAvailableProviders(): Array<WalletProvider> {
        RETURN this.getAllProviders().filter(provider => provider.isAvailable)
    }
    
    // TEST: Should return providers supporting specific capability
    // TEST: Should return empty array if no providers support capability
    FUNCTION getProvidersByCapability(capability: WalletCapability): Array<WalletProvider> {
        RETURN this.getAllProviders().filter(provider => 
            provider.capabilities.includes(capability)
        )
    }
    
    // TEST: Should return providers supporting specific chain
    // TEST: Should return empty array if no providers support chain
    FUNCTION getProvidersByChain(chainId: ChainId): Array<WalletProvider> {
        RETURN this.getAllProviders().filter(provider =>
            provider.supportedChains.includes(chainId)
        )
    }
    
    // TEST: Should successfully unregister existing provider
    // TEST: Should handle unregistering non-existent provider gracefully
    FUNCTION unregisterProvider(providerId: String): Result<Void, Error> {
        IF NOT this.providers.has(providerId) {
            RETURN Error(PROVIDER_NOT_FOUND)
        }
        
        provider = this.providers.get(providerId)
        
        // Disconnect if connected
        IF provider.isConnected {
            TRY {
                AWAIT provider.disconnect()
            } CATCH error {
                this.logger.warn("Error disconnecting provider during unregistration", error)
            }
        }
        
        // Remove event handlers
        this.removeProviderEventHandlers(provider)
        
        // Remove from registry
        this.providers.delete(providerId)
        
        // Emit unregistration event
        this.eventBus.emit("provider.unregistered", { providerId })
        
        this.logger.info("Provider unregistered", { providerId })
        RETURN Success()
    }
    
    // TEST: Should validate all required interface methods exist
    // TEST: Should validate provider properties are correctly typed
    PRIVATE FUNCTION validateProviderInterface(provider: WalletProvider): Boolean {
        requiredMethods = [
            "connect", "disconnect", "getAccounts", "switchChain",
            "signMessage", "signTransaction", "sendTransaction"
        ]
        
        FOR method IN requiredMethods {
            IF NOT (method IN provider AND typeof provider[method] === "function") {
                RETURN false
            }
        }
        
        requiredProperties = ["providerId", "name", "supportedChains", "capabilities"]
        FOR property IN requiredProperties {
            IF NOT (property IN provider) {
                RETURN false
            }
        }
        
        RETURN true
    }
    
    // TEST: Should setup event handlers for provider events
    PRIVATE FUNCTION setupProviderEventHandlers(provider: WalletProvider): Void {
        provider.addEventListener("connect", (data) => {
            this.eventBus.emit("wallet.connected", {
                providerId: provider.providerId,
                ...data
            })
        })
        
        provider.addEventListener("disconnect", (data) => {
            this.eventBus.emit("wallet.disconnected", {
                providerId: provider.providerId,
                ...data
            })
        })
        
        provider.addEventListener("accountsChanged", (data) => {
            this.eventBus.emit("wallet.accountsChanged", {
                providerId: provider.providerId,
                ...data
            })
        })
        
        provider.addEventListener("chainChanged", (data) => {
            this.eventBus.emit("wallet.chainChanged", {
                providerId: provider.providerId,
                ...data
            })
        })
        
        provider.addEventListener("error", (data) => {
            this.eventBus.emit("wallet.error", {
                providerId: provider.providerId,
                ...data
            })
        })
    }
    
    PRIVATE FUNCTION removeProviderEventHandlers(provider: WalletProvider): Void {
        // Remove all event listeners for this provider
        provider.removeEventListener("connect")
        provider.removeEventListener("disconnect")
        provider.removeEventListener("accountsChanged")
        provider.removeEventListener("chainChanged")
        provider.removeEventListener("error")
    }
}
```

## Module: WalletConnectionManager

```pseudocode
// Manages active wallet connections and state synchronization
CLASS WalletConnectionManager {
    PRIVATE connections: Map<String, WalletConnection>
    PRIVATE activeConnection: String?
    PRIVATE registry: WalletProviderRegistry
    PRIVATE eventBus: EventBus
    PRIVATE logger: Logger
    PRIVATE rateLimiter: RateLimiter
    
    // TEST: Should initialize with empty connections
    CONSTRUCTOR(registry: WalletProviderRegistry, eventBus: EventBus) {
        this.connections = NEW Map()
        this.activeConnection = NULL
        this.registry = registry
        this.eventBus = eventBus
        this.logger = NEW Logger("WalletConnectionManager")
        this.rateLimiter = NEW RateLimiter(maxRequests: 100, windowMs: 60000)
    }
    
    // TEST: Should successfully connect to available provider
    // TEST: Should reject connection to unavailable provider
    // TEST: Should handle connection timeout
    // TEST: Should enforce rate limiting
    FUNCTION connect(providerId: String, options: ConnectionOptions = {}): Promise<Result<WalletConnection, ConnectionError>> {
        // Rate limiting check
        IF NOT this.rateLimiter.checkLimit(providerId) {
            RETURN Error(RATE_LIMIT_EXCEEDED)
        }
        
        // Input validation
        IF providerId IS EMPTY {
            RETURN Error(INVALID_PROVIDER_ID)
        }
        
        provider = this.registry.getProvider(providerId)
        IF provider IS NULL {
            RETURN Error(PROVIDER_NOT_FOUND)
        }
        
        IF NOT provider.isAvailable {
            RETURN Error(PROVIDER_UNAVAILABLE)
        }
        
        // Check if already connected
        IF this.connections.has(providerId) {
            existingConnection = this.connections.get(providerId)
            IF existingConnection.status === ConnectionStatus.CONNECTED {
                RETURN Success(existingConnection)
            }
        }
        
        TRY {
            // Set connection timeout
            timeoutMs = options.timeout || 30000
            connectionPromise = provider.connect(options)
            
            connection = AWAIT Promise.race([
                connectionPromise,
                this.createTimeoutPromise(timeoutMs)
            ])
            
            // Store connection
            this.connections.set(providerId, connection)
            
            // Set as active if no active connection
            IF this.activeConnection IS NULL {
                this.activeConnection = providerId
            }
            
            // Setup connection monitoring
            this.setupConnectionMonitoring(connection)
            
            // Emit connection event
            this.eventBus.emit("connection.established", {
                providerId,
                connectionId: connection.connectionId,
                accounts: connection.accounts,
                chainId: connection.chainId
            })
            
            this.logger.info("Wallet connected", { providerId, connectionId: connection.connectionId })
            RETURN Success(connection)
            
        } CATCH error {
            this.logger.error("Connection failed", { providerId, error })
            
            // Clean up failed connection
            this.connections.delete(providerId)
            
            RETURN Error(CONNECTION_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully disconnect active connection
    // TEST: Should handle disconnecting non-existent connection
    // TEST: Should clean up connection state properly
    FUNCTION disconnect(providerId: String): Promise<Result<Void, Error>> {
        IF NOT this.connections.has(providerId) {
            RETURN Error(CONNECTION_NOT_FOUND)
        }
        
        connection = this.connections.get(providerId)
        provider = this.registry.getProvider(providerId)
        
        TRY {
            // Disconnect from provider
            IF provider IS NOT NULL {
                AWAIT provider.disconnect()
            }
            
            // Clean up connection state
            this.connections.delete(providerId)
            
            // Update active connection
            IF this.activeConnection === providerId {
                this.activeConnection = this.getNextActiveConnection()
            }
            
            // Remove connection monitoring
            this.removeConnectionMonitoring(connection)
            
            // Emit disconnection event
            this.eventBus.emit("connection.terminated", {
                providerId,
                connectionId: connection.connectionId
            })
            
            this.logger.info("Wallet disconnected", { providerId })
            RETURN Success()
            
        } CATCH error {
            this.logger.error("Disconnection failed", { providerId, error })
            RETURN Error(DISCONNECTION_FAILED, error.message)
        }
    }
    
    // TEST: Should return active connection when exists
    // TEST: Should return null when no active connection
    FUNCTION getActiveConnection(): WalletConnection? {
        IF this.activeConnection IS NULL {
            RETURN NULL
        }
        RETURN this.connections.get(this.activeConnection)
    }
    
    // TEST: Should successfully set active connection to existing connection
    // TEST: Should reject setting active connection to non-existent connection
    FUNCTION setActiveConnection(providerId: String): Result<Void, Error> {
        IF NOT this.connections.has(providerId) {
            RETURN Error(CONNECTION_NOT_FOUND)
        }
        
        connection = this.connections.get(providerId)
        IF connection.status !== ConnectionStatus.CONNECTED {
            RETURN Error(CONNECTION_NOT_ACTIVE)
        }
        
        this.activeConnection = providerId
        
        this.eventBus.emit("connection.activated", {
            providerId,
            connectionId: connection.connectionId
        })
        
        RETURN Success()
    }
    
    // TEST: Should return all active connections
    // TEST: Should return empty array when no connections
    FUNCTION getAllConnections(): Array<WalletConnection> {
        RETURN Array.from(this.connections.values())
    }
    
    // TEST: Should return connection for valid provider ID
    // TEST: Should return null for invalid provider ID
    FUNCTION getConnection(providerId: String): WalletConnection? {
        RETURN this.connections.get(providerId)
    }
    
    // TEST: Should disconnect all connections successfully
    // TEST: Should handle errors during mass disconnection
    FUNCTION disconnectAll(): Promise<Array<Result<Void, Error>>> {
        disconnectionPromises = []
        
        FOR providerId IN this.connections.keys() {
            disconnectionPromises.push(this.disconnect(providerId))
        }
        
        RETURN Promise.all(disconnectionPromises)
    }
    
    // TEST: Should sync balances for all connected accounts
    // TEST: Should handle sync errors gracefully
    FUNCTION syncAllBalances(): Promise<Void> {
        syncPromises = []
        
        FOR connection IN this.connections.values() {
            IF connection.status === ConnectionStatus.CONNECTED {
                syncPromises.push(this.syncConnectionBalances(connection))
            }
        }
        
        AWAIT Promise.allSettled(syncPromises)
    }
    
    // TEST: Should create timeout promise that rejects after specified time
    PRIVATE FUNCTION createTimeoutPromise(timeoutMs: Number): Promise<Never> {
        RETURN NEW Promise((resolve, reject) => {
            setTimeout(() => {
                reject(NEW Error("Connection timeout"))
            }, timeoutMs)
        })
    }
    
    // TEST: Should setup monitoring for connection health
    PRIVATE FUNCTION setupConnectionMonitoring(connection: WalletConnection): Void {
        // Monitor connection health
        healthCheckInterval = setInterval(() => {
            this.checkConnectionHealth(connection)
        }, 30000) // Check every 30 seconds
        
        connection.healthCheckInterval = healthCheckInterval
    }
    
    PRIVATE FUNCTION removeConnectionMonitoring(connection: WalletConnection): Void {
        IF connection.healthCheckInterval {
            clearInterval(connection.healthCheckInterval)
        }
    }
    
    // TEST: Should detect unhealthy connections
    // TEST: Should attempt reconnection for unhealthy connections
    PRIVATE FUNCTION checkConnectionHealth(connection: WalletConnection): Void {
        provider = this.registry.getProvider(connection.providerId)
        
        IF provider IS NULL OR NOT provider.isConnected {
            this.handleUnhealthyConnection(connection)
        }
    }
    
    PRIVATE FUNCTION handleUnhealthyConnection(connection: WalletConnection): Void {
        this.logger.warn("Unhealthy connection detected", {
            providerId: connection.providerId,
            connectionId: connection.connectionId
        })
        
        // Attempt reconnection
        this.attemptReconnection(connection.providerId)
    }
    
    PRIVATE FUNCTION attemptReconnection(providerId: String): Void {
        // Implement exponential backoff reconnection logic
        // This would be called asynchronously
    }
    
    PRIVATE FUNCTION getNextActiveConnection(): String? {
        FOR connection IN this.connections.values() {
            IF connection.status === ConnectionStatus.CONNECTED {
                RETURN connection.providerId
            }
        }
        RETURN NULL
    }
    
    PRIVATE FUNCTION syncConnectionBalances(connection: WalletConnection): Promise<Void> {
        // Implementation would sync balances for all accounts in connection
        // This is a placeholder for the actual balance synchronization logic
    }
}
```

## Module: Error Handling and Types

```pseudocode
// Error types for wallet provider operations
ENUM RegistrationError {
    INVALID_PROVIDER,
    DUPLICATE_PROVIDER,
    INVALID_INTERFACE
}

ENUM ConnectionError {
    INVALID_PROVIDER_ID,
    PROVIDER_NOT_FOUND,
    PROVIDER_UNAVAILABLE,
    CONNECTION_FAILED,
    CONNECTION_TIMEOUT,
    RATE_LIMIT_EXCEEDED
}

// Connection options for wallet connections
INTERFACE ConnectionOptions {
    chainId?: ChainId
    timeout?: Number
    autoSwitch?: Boolean
    permissions?: Array<Permission>
}

// Wallet events
ENUM WalletEvent {
    CONNECT = "connect",
    DISCONNECT = "disconnect",
    ACCOUNTS_CHANGED = "accountsChanged",
    CHAIN_CHANGED = "chainChanged",
    ERROR = "error"
}

// Rate limiter for connection attempts
CLASS RateLimiter {
    PRIVATE requests: Map<String, Array<Number>>
    PRIVATE maxRequests: Number
    PRIVATE windowMs: Number
    
    CONSTRUCTOR(maxRequests: Number, windowMs: Number) {
        this.requests = NEW Map()
        this.maxRequests = maxRequests
        this.windowMs = windowMs
    }
    
    // TEST: Should allow requests within rate limit
    // TEST: Should reject requests exceeding rate limit
    // TEST: Should reset window after time expires
    FUNCTION checkLimit(key: String): Boolean {
        now = Date.now()
        
        IF NOT this.requests.has(key) {
            this.requests.set(key, [])
        }
        
        timestamps = this.requests.get(key)
        
        // Remove old timestamps outside window
        validTimestamps = timestamps.filter(timestamp => 
            now - timestamp < this.windowMs
        )
        
        IF validTimestamps.length >= this.maxRequests {
            RETURN false
        }
        
        validTimestamps.push(now)
        this.requests.set(key, validTimestamps)
        
        RETURN true
    }
}
```

## Integration Points

### 1. Event Bus Integration
- All wallet events are routed through central event bus
- Enables loose coupling between components
- Supports event-driven architecture patterns

### 2. Logging Integration
- Structured logging for all wallet operations
- Error tracking and debugging support
- Performance monitoring capabilities

### 3. Rate Limiting Integration
- Prevents abuse of wallet connection attempts
- Configurable limits per provider
- Sliding window rate limiting algorithm

### 4. Configuration Integration
- Provider-specific configuration management
- Environment-based settings
- Runtime configuration updates

## Performance Considerations

### 1. Connection Pooling
- Reuse existing connections when possible
- Implement connection health monitoring
- Automatic reconnection with exponential backoff

### 2. Caching Strategy
- Cache provider availability status
- Cache account balances with TTL
- Cache network configurations

### 3. Async Operations
- All wallet operations are asynchronous
- Proper error handling and timeout management
- Concurrent connection support

### 4. Memory Management
- Clean up event listeners on disconnection
- Remove stale connections from registry
- Implement garbage collection for unused objects

---

*This pseudocode specification provides the foundation for implementing the WalletProvider abstraction layer with comprehensive TDD anchors and error handling.*