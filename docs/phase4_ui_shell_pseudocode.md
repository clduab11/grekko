# Phase 4: UI Shell - Electron Application Architecture Pseudocode

## Module Overview

This module defines the core Electron application shell with TradingView-style three-panel layout, IPC communication, and cross-platform desktop functionality.

## Core Components

### ElectronApplicationManager

```typescript
class ElectronApplicationManager {
    // TEST: Application initializes with correct configuration
    initialize(config: ApplicationConfig): Promise<void> {
        // Validate configuration parameters
        validateConfig(config)
        
        // Initialize Electron app with security policies
        setupSecurityPolicies()
        
        // Configure auto-updater
        setupAutoUpdater(config.updateChannel)
        
        // Register global shortcuts and menu
        registerGlobalShortcuts()
        setupApplicationMenu()
        
        // Initialize IPC handlers
        setupIPCHandlers()
        
        // Create main window
        createMainWindow(config.windowConfig)
    }
    
    // TEST: Security policies prevent unauthorized access
    private setupSecurityPolicies(): void {
        // Configure Content Security Policy
        setCSP({
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            connectSrc: ["'self'", "wss:", "https:"],
            imgSrc: ["'self'", "data:", "https:"]
        })
        
        // Disable node integration in renderer
        setWebSecurity(true)
        setNodeIntegration(false)
        setContextIsolation(true)
        
        // Enable sandbox mode
        setSandbox(true)
    }
    
    // TEST: IPC handlers respond to renderer requests
    private setupIPCHandlers(): void {
        // Handle wallet connection requests
        ipcMain.handle('wallet:connect', handleWalletConnect)
        
        // Handle trading operations
        ipcMain.handle('trading:submitOrder', handleTradingOrder)
        
        // Handle agent configuration
        ipcMain.handle('agent:configure', handleAgentConfig)
        
        // Handle data subscriptions
        ipcMain.handle('data:subscribe', handleDataSubscription)
        
        // Handle window management
        ipcMain.handle('window:manage', handleWindowManagement)
    }
    
    // TEST: Main window creates with correct layout
    private createMainWindow(config: WindowConfig): BrowserWindow {
        const mainWindow = new BrowserWindow({
            width: config.width || 1920,
            height: config.height || 1080,
            minWidth: 1200,
            minHeight: 800,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                enableRemoteModule: false,
                preload: path.join(__dirname, 'preload.js')
            },
            titleBarStyle: 'hiddenInset',
            show: false
        })
        
        // Load the renderer process
        mainWindow.loadFile('dist/index.html')
        
        // Show window when ready
        mainWindow.once('ready-to-show', () => {
            mainWindow.show()
            
            // TEST: Window appears in correct state
            if (config.maximized) {
                mainWindow.maximize()
            }
        })
        
        return mainWindow
    }
    
    // TEST: Application shuts down gracefully
    shutdown(): Promise<void> {
        // Close all windows
        BrowserWindow.getAllWindows().forEach(window => {
            window.close()
        })
        
        // Cleanup resources
        cleanupResources()
        
        // Quit application
        app.quit()
    }
}
```

### MainWindowController

```typescript
class MainWindowController {
    private layoutManager: LayoutManager
    private themeManager: ThemeManager
    private stateManager: WindowStateManager
    
    // TEST: Window initializes with three-panel layout
    initialize(window: BrowserWindow): void {
        this.layoutManager = new LayoutManager()
        this.themeManager = new ThemeManager()
        this.stateManager = new WindowStateManager()
        
        // Setup layout configuration
        this.setupLayout()
        
        // Apply theme
        this.applyTheme(this.themeManager.getCurrentTheme())
        
        // Restore window state
        this.restoreWindowState()
        
        // Setup event listeners
        this.setupEventListeners()
    }
    
    // TEST: Layout creates three distinct panels
    private setupLayout(): void {
        const layoutConfig = {
            leftSidebar: {
                width: 300,
                minWidth: 250,
                maxWidth: 500,
                collapsible: true,
                component: 'NewsSidebar'
            },
            mainChart: {
                flex: 1,
                minWidth: 600,
                component: 'TradingChart'
            },
            rightSidebar: {
                width: 350,
                minWidth: 300,
                maxWidth: 600,
                collapsible: true,
                component: 'AgentSidebar'
            }
        }
        
        this.layoutManager.configure(layoutConfig)
    }
    
    // TEST: Theme applies correctly to all components
    private applyTheme(theme: ThemeConfiguration): void {
        // Apply CSS variables for theme
        document.documentElement.style.setProperty('--primary-color', theme.primaryColor)
        document.documentElement.style.setProperty('--background-color', theme.backgroundColor)
        document.documentElement.style.setProperty('--text-color', theme.textColor)
        
        // Apply chart-specific theme
        this.layoutManager.getComponent('TradingChart').applyTheme(theme.chartColors)
        
        // Update sidebar themes
        this.layoutManager.getComponent('NewsSidebar').applyTheme(theme)
        this.layoutManager.getComponent('AgentSidebar').applyTheme(theme)
    }
    
    // TEST: Window state persists across sessions
    private restoreWindowState(): void {
        const savedState = this.stateManager.loadState()
        
        if (savedState) {
            // Restore layout dimensions
            this.layoutManager.restoreLayout(savedState.layout)
            
            // Restore sidebar states
            if (savedState.leftSidebarCollapsed) {
                this.layoutManager.collapseSidebar('left')
            }
            if (savedState.rightSidebarCollapsed) {
                this.layoutManager.collapseSidebar('right')
            }
        }
    }
    
    // TEST: Event listeners handle user interactions
    private setupEventListeners(): void {
        // Handle layout changes
        this.layoutManager.on('layoutChanged', (layout) => {
            this.stateManager.saveLayoutState(layout)
        })
        
        // Handle theme changes
        this.themeManager.on('themeChanged', (theme) => {
            this.applyTheme(theme)
        })
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.layoutManager.handleResize()
        })
        
        // Handle keyboard shortcuts
        this.setupKeyboardShortcuts()
    }
    
    // TEST: Keyboard shortcuts trigger correct actions
    private setupKeyboardShortcuts(): void {
        const shortcuts = {
            'Ctrl+1': () => this.layoutManager.focusPanel('leftSidebar'),
            'Ctrl+2': () => this.layoutManager.focusPanel('mainChart'),
            'Ctrl+3': () => this.layoutManager.focusPanel('rightSidebar'),
            'Ctrl+Shift+L': () => this.layoutManager.toggleSidebar('left'),
            'Ctrl+Shift+R': () => this.layoutManager.toggleSidebar('right'),
            'F11': () => this.toggleFullscreen()
        }
        
        Object.entries(shortcuts).forEach(([key, action]) => {
            registerShortcut(key, action)
        })
    }
    
    // TEST: Fullscreen mode toggles correctly
    private toggleFullscreen(): void {
        const window = getCurrentWindow()
        
        if (window.isFullScreen()) {
            window.setFullScreen(false)
        } else {
            window.setFullScreen(true)
        }
    }
}
```

### LayoutManager

```typescript
class LayoutManager {
    private panels: Map<string, PanelComponent>
    private layout: LayoutConfiguration
    private resizeObserver: ResizeObserver
    
    // TEST: Layout configuration applies correctly
    configure(config: LayoutConfiguration): void {
        this.layout = config
        
        // Create panel containers
        this.createPanelContainers()
        
        // Setup resize handlers
        this.setupResizeHandlers()
        
        // Initialize components
        this.initializeComponents()
    }
    
    // TEST: Panel containers have correct dimensions
    private createPanelContainers(): void {
        const container = document.getElementById('app-container')
        
        // Create main layout structure
        const layoutHTML = `
            <div class="layout-container">
                <div class="sidebar left-sidebar" id="left-sidebar">
                    <div class="sidebar-content"></div>
                    <div class="sidebar-resize-handle"></div>
                </div>
                <div class="main-content" id="main-chart">
                    <div class="chart-container"></div>
                </div>
                <div class="sidebar right-sidebar" id="right-sidebar">
                    <div class="sidebar-resize-handle"></div>
                    <div class="sidebar-content"></div>
                </div>
            </div>
        `
        
        container.innerHTML = layoutHTML
        
        // Apply initial dimensions
        this.applyDimensions()
    }
    
    // TEST: Dimensions apply correctly to panels
    private applyDimensions(): void {
        const leftSidebar = document.getElementById('left-sidebar')
        const rightSidebar = document.getElementById('right-sidebar')
        
        // Set sidebar widths
        leftSidebar.style.width = `${this.layout.leftSidebar.width}px`
        rightSidebar.style.width = `${this.layout.rightSidebar.width}px`
        
        // Set minimum and maximum widths
        leftSidebar.style.minWidth = `${this.layout.leftSidebar.minWidth}px`
        leftSidebar.style.maxWidth = `${this.layout.leftSidebar.maxWidth}px`
        rightSidebar.style.minWidth = `${this.layout.rightSidebar.minWidth}px`
        rightSidebar.style.maxWidth = `${this.layout.rightSidebar.maxWidth}px`
    }
    
    // TEST: Resize handlers work correctly
    private setupResizeHandlers(): void {
        // Setup left sidebar resize
        const leftHandle = document.querySelector('.left-sidebar .sidebar-resize-handle')
        this.setupResizeHandle(leftHandle, 'left')
        
        // Setup right sidebar resize
        const rightHandle = document.querySelector('.right-sidebar .sidebar-resize-handle')
        this.setupResizeHandle(rightHandle, 'right')
        
        // Setup window resize observer
        this.resizeObserver = new ResizeObserver((entries) => {
            this.handleWindowResize(entries)
        })
        
        this.resizeObserver.observe(document.body)
    }
    
    // TEST: Sidebar resize handles work correctly
    private setupResizeHandle(handle: Element, side: 'left' | 'right'): void {
        let isResizing = false
        let startX = 0
        let startWidth = 0
        
        handle.addEventListener('mousedown', (e: MouseEvent) => {
            isResizing = true
            startX = e.clientX
            
            const sidebar = side === 'left' 
                ? document.getElementById('left-sidebar')
                : document.getElementById('right-sidebar')
            
            startWidth = parseInt(getComputedStyle(sidebar).width)
            
            document.addEventListener('mousemove', handleMouseMove)
            document.addEventListener('mouseup', handleMouseUp)
        })
        
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return
            
            const deltaX = side === 'left' ? e.clientX - startX : startX - e.clientX
            const newWidth = startWidth + deltaX
            
            // Apply constraints
            const config = side === 'left' ? this.layout.leftSidebar : this.layout.rightSidebar
            const constrainedWidth = Math.max(config.minWidth, Math.min(config.maxWidth, newWidth))
            
            // Update sidebar width
            const sidebar = side === 'left' 
                ? document.getElementById('left-sidebar')
                : document.getElementById('right-sidebar')
            
            sidebar.style.width = `${constrainedWidth}px`
            
            // Emit layout change event
            this.emitLayoutChange()
        }
        
        const handleMouseUp = () => {
            isResizing = false
            document.removeEventListener('mousemove', handleMouseMove)
            document.removeEventListener('mouseup', handleMouseUp)
        }
    }
    
    // TEST: Components initialize correctly
    private initializeComponents(): void {
        // Initialize news sidebar
        const newsSidebar = new NewsSidebarComponent()
        newsSidebar.mount(document.querySelector('.left-sidebar .sidebar-content'))
        this.panels.set('NewsSidebar', newsSidebar)
        
        // Initialize trading chart
        const tradingChart = new TradingChartComponent()
        tradingChart.mount(document.querySelector('.chart-container'))
        this.panels.set('TradingChart', tradingChart)
        
        // Initialize agent sidebar
        const agentSidebar = new AgentSidebarComponent()
        agentSidebar.mount(document.querySelector('.right-sidebar .sidebar-content'))
        this.panels.set('AgentSidebar', agentSidebar)
    }
    
    // TEST: Sidebar toggle works correctly
    toggleSidebar(side: 'left' | 'right'): void {
        const sidebar = side === 'left' 
            ? document.getElementById('left-sidebar')
            : document.getElementById('right-sidebar')
        
        const isCollapsed = sidebar.classList.contains('collapsed')
        
        if (isCollapsed) {
            sidebar.classList.remove('collapsed')
            sidebar.style.width = side === 'left' 
                ? `${this.layout.leftSidebar.width}px`
                : `${this.layout.rightSidebar.width}px`
        } else {
            sidebar.classList.add('collapsed')
            sidebar.style.width = '0px'
        }
        
        this.emitLayoutChange()
    }
    
    // TEST: Panel focus works correctly
    focusPanel(panelId: string): void {
        const panel = this.panels.get(panelId)
        if (panel) {
            panel.focus()
        }
    }
    
    // TEST: Layout change events emit correctly
    private emitLayoutChange(): void {
        const currentLayout = this.getCurrentLayout()
        this.emit('layoutChanged', currentLayout)
    }
    
    // TEST: Current layout state is accurate
    private getCurrentLayout(): LayoutState {
        const leftSidebar = document.getElementById('left-sidebar')
        const rightSidebar = document.getElementById('right-sidebar')
        
        return {
            leftSidebarWidth: parseInt(getComputedStyle(leftSidebar).width),
            rightSidebarWidth: parseInt(getComputedStyle(rightSidebar).width),
            leftSidebarCollapsed: leftSidebar.classList.contains('collapsed'),
            rightSidebarCollapsed: rightSidebar.classList.contains('collapsed')
        }
    }
    
    // TEST: Window resize handling works correctly
    handleWindowResize(): void {
        // Recalculate layout constraints
        this.validateLayoutConstraints()
        
        // Notify components of resize
        this.panels.forEach(panel => {
            if (panel.handleResize) {
                panel.handleResize()
            }
        })
    }
    
    // TEST: Layout constraints are enforced
    private validateLayoutConstraints(): void {
        const windowWidth = window.innerWidth
        const leftSidebar = document.getElementById('left-sidebar')
        const rightSidebar = document.getElementById('right-sidebar')
        
        const leftWidth = parseInt(getComputedStyle(leftSidebar).width)
        const rightWidth = parseInt(getComputedStyle(rightSidebar).width)
        const minChartWidth = this.layout.mainChart.minWidth
        
        // Ensure minimum chart width is maintained
        const availableWidth = windowWidth - leftWidth - rightWidth
        
        if (availableWidth < minChartWidth) {
            // Proportionally reduce sidebar widths
            const totalSidebarWidth = leftWidth + rightWidth
            const maxSidebarWidth = windowWidth - minChartWidth
            const scaleFactor = maxSidebarWidth / totalSidebarWidth
            
            leftSidebar.style.width = `${leftWidth * scaleFactor}px`
            rightSidebar.style.width = `${rightWidth * scaleFactor}px`
        }
    }
}
```

### IPCBridge

```typescript
class IPCBridge {
    private channels: Map<string, IPCChannel>
    
    // TEST: IPC bridge initializes correctly
    initialize(): void {
        this.channels = new Map()
        
        // Setup preload script exposure
        this.setupPreloadAPI()
        
        // Register channel handlers
        this.registerChannels()
    }
    
    // TEST: Preload API exposes correct methods
    private setupPreloadAPI(): void {
        // Expose safe IPC methods to renderer
        contextBridge.exposeInMainWorld('electronAPI', {
            // Wallet operations
            connectWallet: (type: string, config: any) => 
                ipcRenderer.invoke('wallet:connect', { type, config }),
            
            disconnectWallet: (walletId: string) => 
                ipcRenderer.invoke('wallet:disconnect', { walletId }),
            
            // Trading operations
            submitOrder: (order: TradingOrder) => 
                ipcRenderer.invoke('trading:submitOrder', order),
            
            cancelOrder: (orderId: string) => 
                ipcRenderer.invoke('trading:cancelOrder', { orderId }),
            
            // Agent operations
            configureAgent: (agentId: string, config: AgentConfiguration) => 
                ipcRenderer.invoke('agent:configure', { agentId, config }),
            
            activateAgent: (agentId: string) => 
                ipcRenderer.invoke('agent:activate', { agentId }),
            
            // Data subscriptions
            subscribeMarketData: (symbols: string[]) => 
                ipcRenderer.invoke('data:subscribe', { type: 'market', symbols }),
            
            subscribeNews: (filters: NewsFilter[]) => 
                ipcRenderer.invoke('data:subscribe', { type: 'news', filters }),
            
            // Window management
            minimizeWindow: () => 
                ipcRenderer.invoke('window:minimize'),
            
            maximizeWindow: () => 
                ipcRenderer.invoke('window:maximize'),
            
            closeWindow: () => 
                ipcRenderer.invoke('window:close'),
            
            // Event listeners
            onMarketData: (callback: Function) => 
                ipcRenderer.on('market-data', callback),
            
            onNewsUpdate: (callback: Function) => 
                ipcRenderer.on('news-update', callback),
            
            onAgentSignal: (callback: Function) => 
                ipcRenderer.on('agent-signal', callback)
        })
    }
    
    // TEST: Channel handlers process requests correctly
    private registerChannels(): void {
        // Wallet connection channel
        this.registerChannel('wallet:connect', async (event, data) => {
            const walletManager = getWalletManager()
            return await walletManager.connect(data.type, data.config)
        })
        
        // Trading order channel
        this.registerChannel('trading:submitOrder', async (event, order) => {
            const tradingController = getTradingController()
            return await tradingController.submitOrder(order)
        })
        
        // Agent configuration channel
        this.registerChannel('agent:configure', async (event, data) => {
            const agentController = getAgentController()
            return await agentController.configure(data.agentId, data.config)
        })
        
        // Data subscription channel
        this.registerChannel('data:subscribe', async (event, data) => {
            const dataManager = getDataManager()
            return await dataManager.subscribe(data.type, data)
        })
        
        // Window management channel
        this.registerChannel('window:manage', async (event, action) => {
            const windowController = getWindowController()
            return await windowController.handleAction(action)
        })
    }
    
    // TEST: Channel registration works correctly
    private registerChannel(channel: string, handler: Function): void {
        ipcMain.handle(channel, async (event, ...args) => {
            try {
                // Validate request
                this.validateRequest(channel, args)
                
                // Execute handler
                const result = await handler(event, ...args)
                
                // Log successful operation
                this.logOperation(channel, args, result)
                
                return { success: true, data: result }
            } catch (error) {
                // Log error
                this.logError(channel, args, error)
                
                return { success: false, error: error.message }
            }
        })
        
        this.channels.set(channel, { handler, registered: true })
    }
    
    // TEST: Request validation prevents invalid operations
    private validateRequest(channel: string, args: any[]): void {
        // Validate channel exists
        if (!this.channels.has(channel)) {
            throw new Error(`Unknown IPC channel: ${channel}`)
        }
        
        // Validate arguments based on channel
        switch (channel) {
            case 'wallet:connect':
                this.validateWalletConnectArgs(args[0])
                break
            case 'trading:submitOrder':
                this.validateTradingOrderArgs(args[0])
                break
            case 'agent:configure':
                this.validateAgentConfigArgs(args[0])
                break
        }
    }
    
    // TEST: Wallet connect validation works correctly
    private validateWalletConnectArgs(data: any): void {
        if (!data || !data.type) {
            throw new Error('Wallet type is required')
        }
        
        const validTypes = ['metamask', 'coinbase', 'walletconnect']
        if (!validTypes.includes(data.type)) {
            throw new Error(`Invalid wallet type: ${data.type}`)
        }
    }
    
    // TEST: Trading order validation works correctly
    private validateTradingOrderArgs(order: any): void {
        if (!order || !order.symbol || !order.side || !order.quantity) {
            throw new Error('Invalid order: missing required fields')
        }
        
        if (order.quantity <= 0) {
            throw new Error('Order quantity must be positive')
        }
        
        const validSides = ['buy', 'sell']
        if (!validSides.includes(order.side)) {
            throw new Error(`Invalid order side: ${order.side}`)
        }
    }
    
    // TEST: Agent config validation works correctly
    private validateAgentConfigArgs(data: any): void {
        if (!data || !data.agentId || !data.config) {
            throw new Error('Agent ID and configuration are required')
        }
        
        // Validate risk parameters
        if (data.config.riskParameters) {
            const risk = data.config.riskParameters
            if (risk.maxPositionSize <= 0 || risk.maxDailyLoss <= 0) {
                throw new Error('Risk parameters must be positive')
            }
        }
    }
    
    // TEST: Operation logging works correctly
    private logOperation(channel: string, args: any[], result: any): void {
        console.log(`IPC Operation: ${channel}`, {
            timestamp: new Date().toISOString(),
            args: this.sanitizeArgs(args),
            result: this.sanitizeResult(result)
        })
    }
    
    // TEST: Error logging works correctly
    private logError(channel: string, args: any[], error: Error): void {
        console.error(`IPC Error: ${channel}`, {
            timestamp: new Date().toISOString(),
            args: this.sanitizeArgs(args),
            error: error.message,
            stack: error.stack
        })
    }
    
    // TEST: Argument sanitization removes sensitive data
    private sanitizeArgs(args: any[]): any[] {
        return args.map(arg => {
            if (typeof arg === 'object' && arg !== null) {
                const sanitized = { ...arg }
                // Remove sensitive fields
                delete sanitized.privateKey
                delete sanitized.mnemonic
                delete sanitized.password
                return sanitized
            }
            return arg
        })
    }
    
    // TEST: Result sanitization removes sensitive data
    private sanitizeResult(result: any): any {
        if (typeof result === 'object' && result !== null) {
            const sanitized = { ...result }
            // Remove sensitive fields
            delete sanitized.privateKey
            delete sanitized.mnemonic
            delete sanitized.password
            return sanitized
        }
        return result
    }
}
```

## Type Definitions

```typescript
interface ApplicationConfig {
    windowConfig: WindowConfig
    updateChannel: 'stable' | 'beta' | 'alpha'
    securityPolicy: SecurityPolicy
    logging: LoggingConfig
}

interface WindowConfig {
    width: number
    height: number
    maximized: boolean
    fullscreen: boolean
    alwaysOnTop: boolean
}

interface LayoutConfiguration {
    leftSidebar: SidebarConfig
    mainChart: ChartConfig
    rightSidebar: SidebarConfig
}

interface SidebarConfig {
    width: number
    minWidth: number
    maxWidth: number
    collapsible: boolean
    component: string
}

interface ChartConfig {
    flex: number
    minWidth: number
    component: string
}

interface LayoutState {
    leftSidebarWidth: number
    rightSidebarWidth: number
    leftSidebarCollapsed: boolean
    rightSidebarCollapsed: boolean
}

interface IPCChannel {
    handler: Function
    registered: boolean
}

interface SecurityPolicy {
    csp: ContentSecurityPolicy
    nodeIntegration: boolean
    contextIsolation: boolean
    sandbox: boolean
}
```

## Error Handling

```typescript
// TEST: Error handling provides meaningful feedback
class UIShellErrorHandler {
    static handleApplicationError(error: Error): void {
        console.error('Application Error:', error)
        
        // Show user-friendly error dialog
        showErrorDialog({
            title: 'Application Error',
            message: 'An unexpected error occurred. Please restart the application.',
            details: error.message
        })
    }
    
    static handleLayoutError(error: Error): void {
        console.error('Layout Error:', error)
        
        // Reset layout to default
        const layoutManager = getLayoutManager()
        layoutManager.resetToDefault()
        
        // Notify user
        showNotification({
            type: 'warning',
            message: 'Layout reset due to error'
        })
    }
    
    static handleIPCError(channel: string, error: Error): void {
        console.error(`IPC Error on channel ${channel}:`, error)
        
        // Show appropriate error message based on channel
        const errorMessages = {
            'wallet:connect': 'Failed to connect wallet. Please try again.',
            'trading:submitOrder': 'Failed to submit order. Please check your connection.',
            'agent:configure': 'Failed to configure agent. Please check your settings.'
        }
        
        const message = errorMessages[channel] || 'Operation failed. Please try again.'
        
        showNotification({
            type: 'error',
            message
        })
    }
}
```

This pseudocode module provides the foundation for the Electron application shell with comprehensive TDD anchors, proper error handling, and modular architecture that supports the three-panel TradingView-style layout.