# Phase 4: Frontend UI Overhaul - TDD Anchor Specifications

## Overview

This document provides comprehensive Test-Driven Development (TDD) anchor specifications for all Phase 4 Frontend UI Overhaul components. Each test anchor is designed to validate specific behaviors, edge cases, and integration points across the entire system.

## UI Shell Component Tests

### ElectronApplicationManager Tests

```typescript
describe('ElectronApplicationManager', () => {
    // TEST: Application initializes with correct configuration
    test('should initialize application with valid configuration', async () => {
        const config = createValidApplicationConfig()
        const manager = new ElectronApplicationManager()
        
        await manager.initialize(config)
        
        expect(manager.isInitialized()).toBe(true)
        expect(manager.getSecurityPolicy()).toEqual(config.securityPolicy)
        expect(manager.getWindowCount()).toBe(1)
    })
    
    // TEST: Security policies prevent unauthorized access
    test('should enforce security policies correctly', () => {
        const manager = new ElectronApplicationManager()
        
        manager.setupSecurityPolicies()
        
        expect(manager.getCSPPolicy()).toContain("default-src 'self'")
        expect(manager.isNodeIntegrationDisabled()).toBe(true)
        expect(manager.isContextIsolationEnabled()).toBe(true)
        expect(manager.isSandboxEnabled()).toBe(true)
    })
    
    // TEST: IPC handlers respond to renderer requests
    test('should handle IPC requests correctly', async () => {
        const manager = new ElectronApplicationManager()
        const mockEvent = createMockIPCEvent()
        
        manager.setupIPCHandlers()
        
        const response = await manager.handleIPCRequest('wallet:connect', mockEvent, { type: 'metamask' })
        
        expect(response.success).toBe(true)
        expect(response.data).toBeDefined()
    })
    
    // TEST: Main window creates with correct layout
    test('should create main window with three-panel layout', () => {
        const manager = new ElectronApplicationManager()
        const config = createValidWindowConfig()
        
        const window = manager.createMainWindow(config)
        
        expect(window).toBeInstanceOf(BrowserWindow)
        expect(window.getSize()).toEqual([config.width, config.height])
        expect(window.webContents.isDevToolsOpened()).toBe(false)
    })
    
    // TEST: Application shuts down gracefully
    test('should shutdown gracefully', async () => {
        const manager = new ElectronApplicationManager()
        await manager.initialize(createValidApplicationConfig())
        
        const shutdownPromise = manager.shutdown()
        
        await expect(shutdownPromise).resolves.toBeUndefined()
        expect(BrowserWindow.getAllWindows()).toHaveLength(0)
    })
})
```

### LayoutManager Tests

```typescript
describe('LayoutManager', () => {
    // TEST: Layout configuration applies correctly
    test('should apply layout configuration correctly', () => {
        const manager = new LayoutManager()
        const config = createValidLayoutConfiguration()
        
        manager.configure(config)
        
        expect(manager.getLayout()).toEqual(config)
        expect(manager.getPanelCount()).toBe(3)
    })
    
    // TEST: Panel containers have correct dimensions
    test('should create panel containers with correct dimensions', () => {
        const manager = new LayoutManager()
        const config = createValidLayoutConfiguration()
        
        manager.configure(config)
        
        const leftSidebar = document.getElementById('left-sidebar')
        const rightSidebar = document.getElementById('right-sidebar')
        
        expect(leftSidebar.style.width).toBe(`${config.leftSidebar.width}px`)
        expect(rightSidebar.style.width).toBe(`${config.rightSidebar.width}px`)
    })
    
    // TEST: Sidebar toggle works correctly
    test('should toggle sidebar visibility correctly', () => {
        const manager = new LayoutManager()
        manager.configure(createValidLayoutConfiguration())
        
        manager.toggleSidebar('left')
        
        const leftSidebar = document.getElementById('left-sidebar')
        expect(leftSidebar.classList.contains('collapsed')).toBe(true)
        expect(leftSidebar.style.width).toBe('0px')
    })
    
    // TEST: Resize handlers work correctly
    test('should handle resize events correctly', () => {
        const manager = new LayoutManager()
        manager.configure(createValidLayoutConfiguration())
        const mockEvent = createMockResizeEvent()
        
        manager.handleWindowResize()
        
        expect(manager.getCurrentLayout().leftSidebarWidth).toBeGreaterThan(0)
        expect(manager.getCurrentLayout().rightSidebarWidth).toBeGreaterThan(0)
    })
})
```

## Agent Selection Component Tests

### AgentSidebarController Tests

```typescript
describe('AgentSidebarController', () => {
    // TEST: Agent sidebar initializes with all three agents
    test('should initialize with three core agents', () => {
        const controller = new AgentSidebarController()
        
        controller.initialize()
        
        const agents = controller.getRegisteredAgents()
        expect(agents).toHaveLength(3)
        expect(agents.map(a => a.name)).toEqual(['Spot', 'Gordo', 'Gordon Gekko'])
    })
    
    // TEST: Core agents register with correct configurations
    test('should register agents with correct configurations', () => {
        const controller = new AgentSidebarController()
        
        controller.initialize()
        
        const spotAgent = controller.getAgent('spot-tutor')
        expect(spotAgent.autonomyLevel).toBe(AutonomyLevel.TUTOR)
        expect(spotAgent.riskParameters.maxPositionSize).toBe(0)
        
        const gordoAgent = controller.getAgent('gordo-semi')
        expect(gordoAgent.autonomyLevel).toBe(AutonomyLevel.SEMI_AUTONOMOUS)
        expect(gordoAgent.riskParameters.maxPositionSize).toBe(1000)
        
        const gekkoAgent = controller.getAgent('gekko-auto')
        expect(gekkoAgent.autonomyLevel).toBe(AutonomyLevel.AUTONOMOUS)
        expect(gekkoAgent.riskParameters.maxPositionSize).toBe(5000)
    })
    
    // TEST: Agent selection triggers correct workflow
    test('should trigger correct workflow on agent selection', async () => {
        const controller = new AgentSidebarController()
        controller.initialize()
        const mockPermissionManager = createMockPermissionManager()
        
        await controller.selectAgent('gordo-semi')
        
        expect(mockPermissionManager.requestPermissions).toHaveBeenCalled()
        expect(controller.getActiveAgent().agentId).toBe('gordo-semi')
    })
    
    // TEST: Permission requests work correctly for autonomous agents
    test('should request permissions for autonomous agents', async () => {
        const controller = new AgentSidebarController()
        controller.initialize()
        const agent = controller.getAgent('gekko-auto')
        
        const permissionModal = controller.createPermissionModal(agent)
        
        expect(permissionModal).toBeDefined()
        expect(permissionModal.querySelector('.risk-level')).toBeDefined()
        expect(permissionModal.querySelector('.permission-list')).toBeDefined()
    })
    
    // TEST: Configuration saving works correctly
    test('should save agent configuration correctly', async () => {
        const controller = new AgentSidebarController()
        controller.initialize()
        const mockConfig = createMockAgentConfiguration()
        
        await controller.saveConfiguration('gordo-semi', mockConfig)
        
        const agent = controller.getAgent('gordo-semi')
        expect(agent.configuration).toEqual(mockConfig)
    })
})
```

### Agent Base Classes Tests

```typescript
describe('BaseTradingAgent', () => {
    // TEST: Base agent class provides common functionality
    test('should provide common functionality for all agents', () => {
        const config = createMockAgentConfig()
        const agent = new TestTradingAgent(config)
        
        expect(agent.agentId).toBe(config.agentId)
        expect(agent.name).toBe(config.name)
        expect(agent.status).toBe(AgentStatus.INACTIVE)
    })
    
    // TEST: Agent start process works correctly
    test('should start agent correctly', async () => {
        const agent = new TestTradingAgent(createMockAgentConfig())
        
        await agent.start()
        
        expect(agent.status).toBe(AgentStatus.ACTIVE)
    })
    
    // TEST: Agent configuration updates correctly
    test('should update configuration correctly', async () => {
        const agent = new TestTradingAgent(createMockAgentConfig())
        const newConfig = createMockAgentConfiguration()
        
        await agent.configure(newConfig)
        
        expect(agent.configuration).toEqual(newConfig)
    })
})
```

## Data Visualization Component Tests

### TradingChartController Tests

```typescript
describe('TradingChartController', () => {
    // TEST: Chart controller initializes with all components
    test('should initialize with all required components', () => {
        const container = document.createElement('div')
        const config = createMockChartConfig()
        const controller = new TradingChartController()
        
        controller.initialize(container, config)
        
        expect(controller.chartEngine).toBeDefined()
        expect(controller.dataStreamManager).toBeDefined()
        expect(controller.indicatorManager).toBeDefined()
        expect(controller.overlayManager).toBeDefined()
    })
    
    // TEST: Data subscriptions connect to real-time feeds
    test('should establish data subscriptions correctly', () => {
        const controller = new TradingChartController()
        const mockDataStreamManager = createMockDataStreamManager()
        
        controller.initializeDataSubscriptions()
        
        expect(mockDataStreamManager.subscribe).toHaveBeenCalledWith('market-data', expect.any(Object))
        expect(mockDataStreamManager.subscribe).toHaveBeenCalledWith('sentiment-data', expect.any(Object))
        expect(mockDataStreamManager.subscribe).toHaveBeenCalledWith('ai-predictions', expect.any(Object))
    })
    
    // TEST: Market data updates render correctly on chart
    test('should process market data updates correctly', () => {
        const controller = new TradingChartController()
        const mockData = createMockMarketDataUpdate()
        
        controller.processMarketDataUpdate(mockData)
        
        expect(controller.chartEngine.updateDataSeries).toHaveBeenCalledWith(mockData.symbol, expect.any(Object))
        expect(controller.indicatorManager.updateIndicators).toHaveBeenCalled()
    })
    
    // TEST: Symbol switching updates chart correctly
    test('should switch symbols correctly', async () => {
        const controller = new TradingChartController()
        const newSymbol = 'ETH/USD'
        
        await controller.switchSymbol(newSymbol)
        
        expect(controller.chartEngine.clearData).toHaveBeenCalled()
        expect(controller.dataStreamManager.updateSubscription).toHaveBeenCalledWith('market-data', { symbols: [newSymbol] })
    })
    
    // TEST: Chart export works correctly
    test('should export chart in different formats', async () => {
        const controller = new TradingChartController()
        const options = createMockExportOptions()
        
        const pngBlob = await controller.exportChart(ExportFormat.PNG, options)
        const csvBlob = await controller.exportChart(ExportFormat.CSV, options)
        
        expect(pngBlob).toBeInstanceOf(Blob)
        expect(csvBlob).toBeInstanceOf(Blob)
        expect(pngBlob.type).toBe('image/png')
        expect(csvBlob.type).toBe('text/csv')
    })
})
```

### ChartEngine Tests

```typescript
describe('ChartEngine', () => {
    // TEST: Chart engine initializes with proper configuration
    test('should initialize with proper configuration', () => {
        const container = document.createElement('div')
        const config = createMockChartConfig()
        
        const engine = new ChartEngine(container, config)
        
        expect(engine.container).toBe(container)
        expect(engine.coordinateSystem).toBeDefined()
        expect(engine.renderQueue).toBeDefined()
    })
    
    // TEST: Canvas creation works correctly
    test('should create canvas with correct properties', () => {
        const engine = new ChartEngine(document.createElement('div'), createMockChartConfig())
        const config = createMockCanvasConfig()
        
        const canvas = engine.createCanvas('test', config)
        
        expect(canvas.width).toBe(config.width * config.devicePixelRatio)
        expect(canvas.height).toBe(config.height * config.devicePixelRatio)
        expect(canvas.style.width).toBe(`${config.width}px`)
    })
    
    // TEST: Data series updates correctly
    test('should update data series correctly', () => {
        const engine = new ChartEngine(document.createElement('div'), createMockChartConfig())
        const dataPoint = createMockDataPoint()
        
        engine.updateDataSeries('BTC/USD', dataPoint)
        
        const series = engine.dataSeries.get('BTC/USD')
        expect(series).toBeDefined()
        expect(series.getLatestDataPoint()).toEqual(dataPoint)
    })
    
    // TEST: Auto-fit adjusts chart view correctly
    test('should auto-fit chart view correctly', () => {
        const engine = new ChartEngine(document.createElement('div'), createMockChartConfig())
        const mockData = createMockDataSeries()
        
        engine.dataSeries.set('BTC/USD', mockData)
        engine.autoFit()
        
        const bounds = engine.coordinateSystem.getBounds()
        expect(bounds.xMin).toBeLessThan(bounds.xMax)
        expect(bounds.yMin).toBeLessThan(bounds.yMax)
    })
})
```

## Real-Time Integration Component Tests

### RealTimeIntegrationManager Tests

```typescript
describe('RealTimeIntegrationManager', () => {
    // TEST: Real-time integration manager initializes correctly
    test('should initialize with all required components', () => {
        const config = createMockIntegrationConfig()
        const manager = new RealTimeIntegrationManager()
        
        manager.initialize(config)
        
        expect(manager.webSocketManager).toBeDefined()
        expect(manager.eventBus).toBeDefined()
        expect(manager.dataStreamCoordinator).toBeDefined()
        expect(manager.connectionHealthMonitor).toBeDefined()
    })
    
    // TEST: Backend connections establish correctly
    test('should establish backend connections correctly', async () => {
        const manager = new RealTimeIntegrationManager()
        const mockWebSocketManager = createMockWebSocketManager()
        
        await manager.setupBackendConnections()
        
        expect(mockWebSocketManager.createConnection).toHaveBeenCalledTimes(5)
        expect(mockWebSocketManager.createConnection).toHaveBeenCalledWith(expect.objectContaining({
            name: 'wallet-service'
        }))
    })
    
    // TEST: Message handling processes correctly
    test('should handle incoming messages correctly', async () => {
        const manager = new RealTimeIntegrationManager()
        const mockMessage = createMockWebSocketMessage()
        
        await manager.handleIncomingMessage('trading-service', mockMessage)
        
        expect(manager.connectionHealthMonitor.recordActivity).toHaveBeenCalledWith('trading-service')
    })
    
    // TEST: Balance updates propagate correctly
    test('should propagate balance updates correctly', () => {
        const manager = new RealTimeIntegrationManager()
        const balanceData = createMockBalanceUpdateData()
        
        manager.handleBalanceUpdate(balanceData)
        
        expect(manager.eventBus.emit).toHaveBeenCalledWith('balance-changed', expect.objectContaining({
            walletId: balanceData.walletId,
            asset: balanceData.asset
        }))
    })
    
    // TEST: Order fill handling works correctly
    test('should handle order fills correctly', () => {
        const manager = new RealTimeIntegrationManager()
        const orderData = createMockOrderFilledData()
        
        manager.handleOrderFilled(orderData)
        
        expect(manager.eventBus.emit).toHaveBeenCalledWith('order-filled', expect.objectContaining({
            orderId: orderData.orderId,
            symbol: orderData.symbol
        }))
    })
    
    // TEST: Connection health checks work correctly
    test('should perform health checks correctly', () => {
        const manager = new RealTimeIntegrationManager()
        const mockConnection = createMockWebSocketConnection()
        
        manager.checkConnectionHealth()
        
        expect(manager.connectionHealthMonitor.getHealth).toHaveBeenCalled()
    })
})
```

### WebSocketManager Tests

```typescript
describe('WebSocketManager', () => {
    // TEST: WebSocket manager initializes correctly
    test('should initialize with configuration', () => {
        const config = createMockWebSocketConfig()
        
        const manager = new WebSocketManager(config)
        
        expect(manager.config).toEqual(config)
        expect(manager.connections.size).toBe(0)
    })
    
    // TEST: Connection creation works correctly
    test('should create connections correctly', () => {
        const manager = new WebSocketManager(createMockWebSocketConfig())
        const options = createMockConnectionOptions()
        
        const connection = manager.createConnection(options)
        
        expect(connection).toBeDefined()
        expect(manager.connections.has(options.name)).toBe(true)
    })
    
    // TEST: Connection retrieval works correctly
    test('should retrieve connections correctly', () => {
        const manager = new WebSocketManager(createMockWebSocketConfig())
        const options = createMockConnectionOptions()
        
        manager.createConnection(options)
        const retrieved = manager.getConnection(options.name)
        
        expect(retrieved).toBeDefined()
        expect(retrieved.name).toBe(options.name)
    })
    
    // TEST: Connection removal works correctly
    test('should remove connections correctly', () => {
        const manager = new WebSocketManager(createMockWebSocketConfig())
        const options = createMockConnectionOptions()
        
        manager.createConnection(options)
        manager.removeConnection(options.name)
        
        expect(manager.connections.has(options.name)).toBe(false)
    })
})
```

## Integration Tests

### Cross-Component Integration Tests

```typescript
describe('Cross-Component Integration', () => {
    // TEST: UI shell integrates with agent selection
    test('should integrate UI shell with agent selection', async () => {
        const layoutManager = new LayoutManager()
        const agentController = new AgentSidebarController()
        
        layoutManager.configure(createValidLayoutConfiguration())
        agentController.initialize()
        
        const agentSidebar = layoutManager.getComponent('AgentSidebar')
        expect(agentSidebar).toBeDefined()
        
        await agentController.selectAgent('spot-tutor')
        expect(agentSidebar.getActiveAgent()).toBeDefined()
    })
    
    // TEST: Chart integrates with real-time data
    test('should integrate chart with real-time data', async () => {
        const chartController = new TradingChartController()
        const integrationManager = new RealTimeIntegrationManager()
        
        chartController.initialize(document.createElement('div'), createMockChartConfig())
        integrationManager.initialize(createMockIntegrationConfig())
        
        const mockPriceData = createMockPriceTickData()
        integrationManager.handlePriceTick(mockPriceData)
        
        expect(chartController.chartEngine.updateDataSeries).toHaveBeenCalled()
    })
    
    // TEST: Agent signals trigger chart updates
    test('should trigger chart updates from agent signals', async () => {
        const agentController = new AgentSidebarController()
        const chartController = new TradingChartController()
        const integrationManager = new RealTimeIntegrationManager()
        
        // Initialize all components
        agentController.initialize()
        chartController.initialize(document.createElement('div'), createMockChartConfig())
        integrationManager.initialize(createMockIntegrationConfig())
        
        // Simulate agent signal
        const signalData = createMockTradingSignalData()
        integrationManager.handleTradingSignal(signalData)
        
        expect(chartController.overlayManager.addOverlay).toHaveBeenCalledWith('signal', expect.any(Object))
    })
})
```

## Performance Tests

### Performance Benchmarks

```typescript
describe('Performance Benchmarks', () => {
    // TEST: Chart rendering meets performance targets
    test('should render charts within performance targets', async () => {
        const chartController = new TradingChartController()
        chartController.initialize(document.createElement('div'), createMockChartConfig())
        
        const startTime = performance.now()
        
        // Simulate 1000 data points
        for (let i = 0; i < 1000; i++) {
            const dataPoint = createMockDataPoint()
            chartController.processMarketDataUpdate(dataPoint)
        }
        
        const endTime = performance.now()
        const renderTime = endTime - startTime
        
        expect(renderTime).toBeLessThan(100) // 100ms target
    })
    
    // TEST: Real-time updates maintain performance
    test('should maintain performance with high-frequency updates', async () => {
        const integrationManager = new RealTimeIntegrationManager()
        integrationManager.initialize(createMockIntegrationConfig())
        
        const startTime = performance.now()
        
        // Simulate 100 updates per second for 1 second
        for (let i = 0; i < 100; i++) {
            const priceData = createMockPriceTickData()
            integrationManager.handlePriceTick(priceData)
        }
        
        const endTime = performance.now()
        const processingTime = endTime - startTime
        
        expect(processingTime).toBeLessThan(50) // 50ms target for 100 updates
    })
    
    // TEST: Memory usage stays within limits
    test('should maintain memory usage within limits', async () => {
        const initialMemory = performance.memory?.usedJSHeapSize || 0
        
        // Run intensive operations
        const chartController = new TradingChartController()
        chartController.initialize(document.createElement('div'), createMockChartConfig())
        
        for (let i = 0; i < 10000; i++) {
            chartController.processMarketDataUpdate(createMockDataPoint())
        }
        
        const finalMemory = performance.memory?.usedJSHeapSize || 0
        const memoryIncrease = finalMemory - initialMemory
        
        expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024) // 50MB limit
    })
})
```

## Error Handling Tests

### Error Scenarios

```typescript
describe('Error Handling', () => {
    // TEST: Network errors are handled gracefully
    test('should handle network errors gracefully', async () => {
        const integrationManager = new RealTimeIntegrationManager()
        const mockError = new Error('Network connection failed')
        
        integrationManager.handleConnectionError('trading-service', mockError)
        
        expect(integrationManager.connectionHealthMonitor.updateStatus)
            .toHaveBeenCalledWith('trading-service', 'error')
        expect(integrationManager.eventBus.emit)
            .toHaveBeenCalledWith('connection-error', expect.any(Object))
    })
    
    // TEST: Invalid data is rejected
    test('should reject invalid data', () => {
        const chartController = new TradingChartController()
        const invalidData = { invalid: 'data' }
        
        expect(() => {
            chartController.processMarketDataUpdate(invalidData)
        }).toThrow('Invalid market data')
    })
    
    // TEST: Agent errors are handled correctly
    test('should handle agent errors correctly', async () => {
        const agentController = new AgentSidebarController()
        agentController.initialize()
        const error = new AgentError('agent-001', 'Processing failed')
        
        agentController.handleAgentError(error)
        
        const agent = agentController.getAgent('agent-001')
        expect(agent.status).toBe(AgentStatus.ERROR)
    })
})
```

## Mock Factories

```typescript
// Mock factory functions for test data
function createValidApplicationConfig(): ApplicationConfig {
    return {
        windowConfig: {
            width: 1920,
            height: 1080,
            maximized: false,
            fullscreen: false,
            alwaysOnTop: false
        },
        updateChannel: 'stable',
        securityPolicy: {
            csp: { defaultSrc: ["'self'"] },
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true
        },
        logging: {
            level: 'info',
            file: 'app.log'
        }
    }
}

function createMockMarketDataUpdate(): MarketDataUpdate {
    return {
        symbol: 'BTC/USD',
        timestamp: new Date(),
        open: 50000,
        high: 51000,
        low: 49000,
        close: 50500,
        volume: 1000
    }
}

function createMockAgentConfiguration(): AgentConfiguration {
    return {
        riskParameters: {
            maxPositionSize: 1000,
            maxDailyLoss: 100,
            stopLossPercentage: 5,
            takeProfitPercentage: 10,
            maxOpenPositions: 3
        },
        tradingPreferences: {
            preferredAssets: ['BTC', 'ETH'],
            strategy: 'moderate',
            timeframe: '1h'
        },
        notificationSettings: {
            tradeExecuted: true,
            riskLimitReached: true,
            performanceUpdate: false
        }
    }
}

function createMockIntegrationConfig(): IntegrationConfig {
    return {
        webSocket: {
            reconnectInterval: 5000,
            maxReconnectAttempts: 10,
            heartbeatInterval: 30000
        },
        messageQueue: {
            maxSize: 1000,
            processingInterval: 100
        },
        healthMonitoring: {
            checkInterval: 30000,
            timeoutThreshold: 10000
        },
        performance: {
            targetFPS: 60,
            memoryThreshold: 100 * 1024 * 1024
        }
    }
}
```

This comprehensive TDD anchor specification provides complete test coverage for all Phase 4 components, ensuring robust validation of functionality, performance, error handling, and integration across the entire Frontend UI Overhaul system.