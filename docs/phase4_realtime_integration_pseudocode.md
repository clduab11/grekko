# Phase 4: Real-Time Integration Layer - WebSocket Communication Pseudocode

## Module Overview

This module defines the real-time integration layer with WebSocket communication, event-driven UI updates, live trading execution feedback, and multi-asset portfolio synchronization across all backend systems.

## Core Components

### RealTimeIntegrationManager

```typescript
class RealTimeIntegrationManager {
    private webSocketManager: WebSocketManager
    private eventBus: EventBus
    private dataStreamCoordinator: DataStreamCoordinator
    private connectionHealthMonitor: ConnectionHealthMonitor
    private messageQueue: MessageQueue
    
    // TEST: Real-time integration manager initializes correctly
    initialize(config: IntegrationConfig): void {
        this.webSocketManager = new WebSocketManager(config.webSocket)
        this.eventBus = new EventBus()
        this.dataStreamCoordinator = new DataStreamCoordinator()
        this.connectionHealthMonitor = new ConnectionHealthMonitor()
        this.messageQueue = new MessageQueue(config.messageQueue)
        
        // Setup backend connections
        this.setupBackendConnections()
        
        // Initialize event routing
        this.initializeEventRouting()
        
        // Start health monitoring
        this.startHealthMonitoring()
        
        // Setup message processing
        this.setupMessageProcessing()
        
        // Initialize reconnection logic
        this.initializeReconnectionLogic()
    }
    
    // TEST: Backend connections establish correctly
    private setupBackendConnections(): void {
        const backendEndpoints = [
            {
                name: 'wallet-service',
                url: 'wss://api.grekko.com/ws/wallet',
                topics: ['wallet-events', 'balance-updates', 'transaction-status'],
                priority: 'high'
            },
            {
                name: 'trading-service',
                url: 'wss://api.grekko.com/ws/trading',
                topics: ['order-updates', 'execution-events', 'position-changes'],
                priority: 'critical'
            },
            {
                name: 'market-data-service',
                url: 'wss://api.grekko.com/ws/market-data',
                topics: ['price-updates', 'orderbook-changes', 'trade-events'],
                priority: 'high'
            },
            {
                name: 'agent-service',
                url: 'wss://api.grekko.com/ws/agents',
                topics: ['agent-signals', 'performance-updates', 'status-changes'],
                priority: 'medium'
            },
            {
                name: 'sentiment-service',
                url: 'wss://api.grekko.com/ws/sentiment',
                topics: ['sentiment-updates', 'news-events', 'social-signals'],
                priority: 'low'
            }
        ]
        
        backendEndpoints.forEach(endpoint => {
            this.establishBackendConnection(endpoint)
        })
    }
    
    // TEST: Individual backend connections work correctly
    private establishBackendConnection(endpoint: BackendEndpoint): void {
        const connection = this.webSocketManager.createConnection({
            name: endpoint.name,
            url: endpoint.url,
            protocols: ['grekko-v1'],
            options: {
                reconnect: true,
                maxReconnectAttempts: 10,
                reconnectInterval: 5000,
                heartbeatInterval: 30000,
                timeout: 10000
            }
        })
        
        // Setup connection event handlers
        connection.on('open', () => {
            this.handleConnectionOpen(endpoint.name)
        })
        
        connection.on('message', (message) => {
            this.handleIncomingMessage(endpoint.name, message)
        })
        
        connection.on('close', (code, reason) => {
            this.handleConnectionClose(endpoint.name, code, reason)
        })
        
        connection.on('error', (error) => {
            this.handleConnectionError(endpoint.name, error)
        })
        
        // Subscribe to topics
        endpoint.topics.forEach(topic => {
            this.subscribeToTopic(endpoint.name, topic)
        })
    }
    
    // TEST: Connection open handling works correctly
    private handleConnectionOpen(serviceName: string): void {
        console.log(`Connected to ${serviceName}`)
        
        // Update connection status
        this.connectionHealthMonitor.updateStatus(serviceName, 'connected')
        
        // Send authentication if required
        this.authenticateConnection(serviceName)
        
        // Resume subscriptions
        this.resumeSubscriptions(serviceName)
        
        // Emit connection event
        this.eventBus.emit('connection-established', {
            service: serviceName,
            timestamp: new Date()
        })
    }
    
    // TEST: Message handling processes correctly
    private handleIncomingMessage(serviceName: string, message: WebSocketMessage): void {
        try {
            // Parse message
            const parsedMessage = this.parseMessage(message)
            
            // Validate message structure
            this.validateMessage(parsedMessage)
            
            // Route message to appropriate handler
            this.routeMessage(serviceName, parsedMessage)
            
            // Update connection health
            this.connectionHealthMonitor.recordActivity(serviceName)
            
        } catch (error) {
            this.handleMessageError(serviceName, message, error)
        }
    }
    
    // TEST: Message routing works correctly
    private routeMessage(serviceName: string, message: ParsedMessage): void {
        const routingKey = `${serviceName}.${message.topic}.${message.type}`
        
        switch (routingKey) {
            // Wallet service messages
            case 'wallet-service.wallet-events.balance-update':
                this.handleBalanceUpdate(message.data)
                break
            case 'wallet-service.wallet-events.transaction-confirmed':
                this.handleTransactionConfirmed(message.data)
                break
                
            // Trading service messages
            case 'trading-service.order-updates.order-filled':
                this.handleOrderFilled(message.data)
                break
            case 'trading-service.order-updates.order-cancelled':
                this.handleOrderCancelled(message.data)
                break
            case 'trading-service.position-changes.position-opened':
                this.handlePositionOpened(message.data)
                break
                
            // Market data service messages
            case 'market-data-service.price-updates.tick':
                this.handlePriceTick(message.data)
                break
            case 'market-data-service.orderbook-changes.update':
                this.handleOrderBookUpdate(message.data)
                break
                
            // Agent service messages
            case 'agent-service.agent-signals.trading-signal':
                this.handleTradingSignal(message.data)
                break
            case 'agent-service.performance-updates.metrics':
                this.handlePerformanceUpdate(message.data)
                break
                
            // Sentiment service messages
            case 'sentiment-service.sentiment-updates.score':
                this.handleSentimentUpdate(message.data)
                break
            case 'sentiment-service.news-events.article':
                this.handleNewsUpdate(message.data)
                break
                
            default:
                this.handleUnknownMessage(routingKey, message)
        }
    }
    
    // TEST: Balance updates propagate correctly
    private handleBalanceUpdate(data: BalanceUpdateData): void {
        // Validate balance data
        this.validateBalanceData(data)
        
        // Update local balance cache
        this.updateBalanceCache(data)
        
        // Emit balance change event
        this.eventBus.emit('balance-changed', {
            walletId: data.walletId,
            asset: data.asset,
            balance: data.balance,
            previousBalance: data.previousBalance,
            timestamp: data.timestamp
        })
        
        // Update portfolio calculations
        this.triggerPortfolioRecalculation(data.walletId)
        
        // Update UI components
        this.updateBalanceDisplay(data)
    }
    
    // TEST: Order fill handling works correctly
    private handleOrderFilled(data: OrderFilledData): void {
        // Validate order data
        this.validateOrderData(data)
        
        // Update order status
        this.updateOrderStatus(data.orderId, 'filled')
        
        // Create position update
        this.createPositionFromFill(data)
        
        // Emit order filled event
        this.eventBus.emit('order-filled', {
            orderId: data.orderId,
            symbol: data.symbol,
            side: data.side,
            quantity: data.quantity,
            price: data.price,
            timestamp: data.timestamp
        })
        
        // Update trading interface
        this.updateTradingInterface(data)
        
        // Trigger performance calculation
        this.triggerPerformanceCalculation(data)
    }
    
    // TEST: Price tick handling maintains performance
    private handlePriceTick(data: PriceTickData): void {
        // Throttle price updates to maintain performance
        if (!this.shouldProcessPriceTick(data.symbol)) {
            return
        }
        
        // Validate price data
        this.validatePriceData(data)
        
        // Update price cache
        this.updatePriceCache(data)
        
        // Emit price update event
        this.eventBus.emit('price-updated', {
            symbol: data.symbol,
            price: data.price,
            change: data.change,
            volume: data.volume,
            timestamp: data.timestamp
        })
        
        // Update chart data
        this.updateChartData(data)
        
        // Update position P&L
        this.updatePositionPnL(data)
    }
    
    // TEST: Trading signal handling works correctly
    private handleTradingSignal(data: TradingSignalData): void {
        // Validate signal data
        this.validateSignalData(data)
        
        // Check agent permissions
        if (!this.checkAgentPermissions(data.agentId, data.signal)) {
            this.rejectSignal(data, 'insufficient-permissions')
            return
        }
        
        // Emit trading signal event
        this.eventBus.emit('trading-signal-received', {
            agentId: data.agentId,
            signal: data.signal,
            confidence: data.confidence,
            timestamp: data.timestamp
        })
        
        // Process signal based on agent autonomy level
        this.processSignalByAutonomyLevel(data)
        
        // Update agent interface
        this.updateAgentInterface(data)
    }
    
    // TEST: Event routing initializes correctly
    private initializeEventRouting(): void {
        // Setup UI update handlers
        this.eventBus.on('balance-changed', (event) => {
            this.updateUIComponent('portfolio-balance', event)
        })
        
        this.eventBus.on('order-filled', (event) => {
            this.updateUIComponent('trading-orders', event)
            this.updateUIComponent('position-summary', event)
        })
        
        this.eventBus.on('price-updated', (event) => {
            this.updateUIComponent('price-ticker', event)
            this.updateUIComponent('trading-chart', event)
        })
        
        this.eventBus.on('trading-signal-received', (event) => {
            this.updateUIComponent('agent-signals', event)
        })
        
        // Setup cross-component communication
        this.setupCrossComponentCommunication()
    }
    
    // TEST: UI component updates work correctly
    private updateUIComponent(componentId: string, eventData: any): void {
        const component = this.getUIComponent(componentId)
        
        if (!component) {
            console.warn(`UI component not found: ${componentId}`)
            return
        }
        
        // Queue update to avoid blocking
        this.messageQueue.enqueue({
            type: 'ui-update',
            component: componentId,
            data: eventData,
            priority: this.getUpdatePriority(componentId),
            timestamp: new Date()
        })
    }
    
    // TEST: Health monitoring works correctly
    private startHealthMonitoring(): void {
        // Monitor connection health
        setInterval(() => {
            this.checkConnectionHealth()
        }, 30000) // Every 30 seconds
        
        // Monitor message latency
        this.setupLatencyMonitoring()
        
        // Monitor memory usage
        this.setupMemoryMonitoring()
        
        // Setup health alerts
        this.setupHealthAlerts()
    }
    
    // TEST: Connection health checks work correctly
    private checkConnectionHealth(): void {
        const connections = this.webSocketManager.getAllConnections()
        
        connections.forEach(connection => {
            const health = this.connectionHealthMonitor.getHealth(connection.name)
            
            if (health.status === 'unhealthy') {
                this.handleUnhealthyConnection(connection)
            } else if (health.latency > 5000) { // 5 second threshold
                this.handleHighLatencyConnection(connection)
            }
        })
    }
    
    // TEST: Reconnection logic works correctly
    private initializeReconnectionLogic(): void {
        this.eventBus.on('connection-lost', (event) => {
            this.scheduleReconnection(event.service)
        })
        
        this.eventBus.on('connection-failed', (event) => {
            this.handleConnectionFailure(event.service, event.error)
        })
    }
    
    // TEST: Reconnection attempts work correctly
    private scheduleReconnection(serviceName: string): void {
        const connection = this.webSocketManager.getConnection(serviceName)
        
        if (!connection) return
        
        const reconnectDelay = this.calculateReconnectDelay(connection.reconnectAttempts)
        
        setTimeout(() => {
            this.attemptReconnection(serviceName)
        }, reconnectDelay)
    }
    
    // TEST: Message processing maintains order
    private setupMessageProcessing(): void {
        // Process high priority messages first
        this.messageQueue.setProcessor('critical', (message) => {
            this.processMessage(message)
        })
        
        this.messageQueue.setProcessor('high', (message) => {
            this.processMessage(message)
        })
        
        this.messageQueue.setProcessor('medium', (message) => {
            this.processMessage(message)
        })
        
        this.messageQueue.setProcessor('low', (message) => {
            this.processMessage(message)
        })
        
        // Start message processing
        this.messageQueue.start()
    }
    
    // TEST: Message validation works correctly
    private validateMessage(message: ParsedMessage): void {
        // Check required fields
        if (!message.topic || !message.type || !message.data) {
            throw new Error('Invalid message structure')
        }
        
        // Check message timestamp
        const messageAge = Date.now() - new Date(message.timestamp).getTime()
        if (messageAge > 60000) { // 1 minute threshold
            throw new Error('Message too old')
        }
        
        // Validate message signature if present
        if (message.signature) {
            this.validateMessageSignature(message)
        }
    }
    
    // TEST: Subscription management works correctly
    subscribeToTopic(serviceName: string, topic: string): void {
        const connection = this.webSocketManager.getConnection(serviceName)
        
        if (!connection || connection.readyState !== WebSocket.OPEN) {
            // Queue subscription for when connection is ready
            this.queueSubscription(serviceName, topic)
            return
        }
        
        const subscriptionMessage = {
            type: 'subscribe',
            topic: topic,
            timestamp: new Date().toISOString()
        }
        
        connection.send(JSON.stringify(subscriptionMessage))
        
        // Track subscription
        this.dataStreamCoordinator.addSubscription(serviceName, topic)
    }
    
    // TEST: Unsubscription works correctly
    unsubscribeFromTopic(serviceName: string, topic: string): void {
        const connection = this.webSocketManager.getConnection(serviceName)
        
        if (!connection || connection.readyState !== WebSocket.OPEN) {
            return
        }
        
        const unsubscriptionMessage = {
            type: 'unsubscribe',
            topic: topic,
            timestamp: new Date().toISOString()
        }
        
        connection.send(JSON.stringify(unsubscriptionMessage))
        
        // Remove subscription tracking
        this.dataStreamCoordinator.removeSubscription(serviceName, topic)
    }
    
    // TEST: Error handling works correctly
    private handleConnectionError(serviceName: string, error: Error): void {
        console.error(`Connection error for ${serviceName}:`, error)
        
        // Update connection status
        this.connectionHealthMonitor.updateStatus(serviceName, 'error')
        
        // Emit error event
        this.eventBus.emit('connection-error', {
            service: serviceName,
            error: error.message,
            timestamp: new Date()
        })
        
        // Attempt recovery
        this.attemptErrorRecovery(serviceName, error)
    }
    
    // TEST: Performance optimization works correctly
    private optimizePerformance(): void {
        // Throttle high-frequency updates
        this.setupUpdateThrottling()
        
        // Batch similar messages
        this.setupMessageBatching()
        
        // Implement message deduplication
        this.setupMessageDeduplication()
        
        // Monitor and adjust buffer sizes
        this.setupBufferOptimization()
    }
    
    // TEST: Graceful shutdown works correctly
    shutdown(): Promise<void> {
        return new Promise((resolve) => {
            // Stop message processing
            this.messageQueue.stop()
            
            // Close all connections gracefully
            const connections = this.webSocketManager.getAllConnections()
            const closePromises = connections.map(connection => 
                this.closeConnectionGracefully(connection)
            )
            
            Promise.all(closePromises).then(() => {
                // Stop health monitoring
                this.connectionHealthMonitor.stop()
                
                // Clear event listeners
                this.eventBus.removeAllListeners()
                
                resolve()
            })
        })
    }
}
```

### WebSocketManager

```typescript
class WebSocketManager {
    private connections: Map<string, WebSocketConnection>
    private config: WebSocketConfig
    
    // TEST: WebSocket manager initializes correctly
    constructor(config: WebSocketConfig) {
        this.connections = new Map()
        this.config = config
    }
    
    // TEST: Connection creation works correctly
    createConnection(options: ConnectionOptions): WebSocketConnection {
        const connection = new WebSocketConnection(options)
        
        // Store connection
        this.connections.set(options.name, connection)
        
        // Setup connection monitoring
        this.setupConnectionMonitoring(connection)
        
        return connection
    }
    
    // TEST: Connection monitoring works correctly
    private setupConnectionMonitoring(connection: WebSocketConnection): void {
        // Monitor connection state
        connection.on('stateChange', (state) => {
            this.handleConnectionStateChange(connection.name, state)
        })
        
        // Monitor message throughput
        connection.on('message', () => {
            this.updateThroughputMetrics(connection.name)
        })
        
        // Monitor errors
        connection.on('error', (error) => {
            this.recordConnectionError(connection.name, error)
        })
    }
    
    // TEST: Connection retrieval works correctly
    getConnection(name: string): WebSocketConnection | undefined {
        return this.connections.get(name)
    }
    
    // TEST: All connections retrieval works correctly
    getAllConnections(): WebSocketConnection[] {
        return Array.from(this.connections.values())
    }
    
    // TEST: Connection removal works correctly
    removeConnection(name: string): void {
        const connection = this.connections.get(name)
        
        if (connection) {
            connection.close()
            this.connections.delete(name)
        }
    }
}
```

## Type Definitions

```typescript
interface IntegrationConfig {
    webSocket: WebSocketConfig
    messageQueue: MessageQueueConfig
    healthMonitoring: HealthMonitoringConfig
    performance: PerformanceConfig
}

interface BackendEndpoint {
    name: string
    url: string
    topics: string[]
    priority: 'critical' | 'high' | 'medium' | 'low'
}

interface ParsedMessage {
    topic: string
    type: string
    data: any
    timestamp: string
    signature?: string
}

interface BalanceUpdateData {
    walletId: string
    asset: string
    balance: number
    previousBalance: number
    timestamp: Date
}

interface OrderFilledData {
    orderId: string
    symbol: string
    side: 'buy' | 'sell'
    quantity: number
    price: number
    timestamp: Date
}

interface PriceTickData {
    symbol: string
    price: number
    change: number
    volume: number
    timestamp: Date
}

interface TradingSignalData {
    agentId: string
    signal: TradingSignal
    confidence: number
    timestamp: Date
}

interface ConnectionOptions {
    name: string
    url: string
    protocols?: string[]
    options: {
        reconnect: boolean
        maxReconnectAttempts: number
        reconnectInterval: number
        heartbeatInterval: number
        timeout: number
    }
}

interface WebSocketMessage {
    data: string | ArrayBuffer | Blob
    type: string
    target: WebSocket
}
```

## Error Handling

```typescript
// TEST: Error handling provides comprehensive coverage
class RealTimeErrorHandler {
    static handleConnectionError(serviceName: string, error: Error): void {
        console.error(`Connection error for ${serviceName}:`, error)
        
        // Categorize error
        const errorType = this.categorizeError(error)
        
        // Apply appropriate recovery strategy
        switch (errorType) {
            case 'network':
                this.handleNetworkError(serviceName, error)
                break
            case 'authentication':
                this.handleAuthenticationError(serviceName, error)
                break
            case 'rate-limit':
                this.handleRateLimitError(serviceName, error)
                break
            case 'server':
                this.handleServerError(serviceName, error)
                break
            default:
                this.handleUnknownError(serviceName, error)
        }
    }
    
    static handleMessageError(serviceName: string, message: any, error: Error): void {
        console.error(`Message processing error for ${serviceName}:`, error)
        
        // Log problematic message for debugging
        this.logProblematicMessage(serviceName, message, error)
        
        // Attempt message recovery if possible
        this.attemptMessageRecovery(serviceName, message, error)
    }
}
```

This pseudocode module completes the real-time integration layer with comprehensive WebSocket communication, event-driven updates, and robust error handling that connects all Phase 4 UI components with the backend systems from Phases 1-3.