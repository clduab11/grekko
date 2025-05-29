# Phase 4: Data Visualization Engine - Advanced Charting Pseudocode

## Module Overview

This module defines the data visualization engine with TradingView-style advanced charting capabilities, real-time data feeds, technical indicators, and multi-asset support with sentiment overlays.

## Core Components

### TradingChartController

```typescript
class TradingChartController {
    private chartEngine: ChartEngine
    private dataStreamManager: DataStreamManager
    private indicatorManager: IndicatorManager
    private overlayManager: OverlayManager
    private interactionManager: InteractionManager
    
    // TEST: Chart controller initializes with all components
    initialize(container: HTMLElement, config: ChartConfig): void {
        this.chartEngine = new ChartEngine(container, config)
        this.dataStreamManager = new DataStreamManager()
        this.indicatorManager = new IndicatorManager()
        this.overlayManager = new OverlayManager()
        this.interactionManager = new InteractionManager()
        
        // Setup chart canvas and rendering
        this.setupChartCanvas()
        
        // Initialize data subscriptions
        this.initializeDataSubscriptions()
        
        // Setup technical indicators
        this.setupTechnicalIndicators()
        
        // Configure chart interactions
        this.setupChartInteractions()
        
        // Start real-time updates
        this.startRealTimeUpdates()
    }
    
    // TEST: Chart canvas setup creates proper rendering context
    private setupChartCanvas(): void {
        const canvasConfig = {
            width: this.chartEngine.getContainerWidth(),
            height: this.chartEngine.getContainerHeight(),
            devicePixelRatio: window.devicePixelRatio || 1,
            antialias: true,
            preserveDrawingBuffer: false
        }
        
        // Create main chart canvas
        this.chartEngine.createCanvas('main', canvasConfig)
        
        // Create overlay canvas for indicators
        this.chartEngine.createCanvas('indicators', canvasConfig)
        
        // Create interaction canvas for user input
        this.chartEngine.createCanvas('interaction', canvasConfig)
        
        // Setup coordinate system
        this.chartEngine.setupCoordinateSystem({
            xAxis: { type: 'time', autoScale: true },
            yAxis: { type: 'price', autoScale: true, position: 'right' }
        })
    }
    
    // TEST: Data subscriptions connect to real-time feeds
    private initializeDataSubscriptions(): void {
        // Subscribe to market data
        this.dataStreamManager.subscribe('market-data', {
            symbols: ['BTC/USD', 'ETH/USD', 'SOL/USD'],
            timeframes: ['1m', '5m', '15m', '1h', '4h', '1d'],
            dataTypes: ['ohlcv', 'trades', 'orderbook']
        })
        
        // Subscribe to sentiment data
        this.dataStreamManager.subscribe('sentiment-data', {
            symbols: ['BTC/USD', 'ETH/USD', 'SOL/USD'],
            sources: ['twitter', 'reddit', 'news'],
            updateInterval: 60000 // 1 minute
        })
        
        // Subscribe to AI predictions
        this.dataStreamManager.subscribe('ai-predictions', {
            symbols: ['BTC/USD', 'ETH/USD', 'SOL/USD'],
            models: ['trend-predictor', 'volatility-predictor'],
            updateInterval: 300000 // 5 minutes
        })
        
        // Setup data event handlers
        this.setupDataEventHandlers()
    }
    
    // TEST: Data event handlers process updates correctly
    private setupDataEventHandlers(): void {
        // Handle market data updates
        this.dataStreamManager.on('market-data-update', (data: MarketDataUpdate) => {
            this.processMarketDataUpdate(data)
        })
        
        // Handle sentiment data updates
        this.dataStreamManager.on('sentiment-data-update', (data: SentimentDataUpdate) => {
            this.processSentimentDataUpdate(data)
        })
        
        // Handle AI prediction updates
        this.dataStreamManager.on('ai-prediction-update', (data: PredictionDataUpdate) => {
            this.processPredictionDataUpdate(data)
        })
        
        // Handle connection status changes
        this.dataStreamManager.on('connection-status-change', (status: ConnectionStatus) => {
            this.updateConnectionStatusIndicator(status)
        })
    }
    
    // TEST: Market data updates render correctly on chart
    private processMarketDataUpdate(data: MarketDataUpdate): void {
        // Validate data integrity
        this.validateMarketData(data)
        
        // Update chart data series
        this.chartEngine.updateDataSeries(data.symbol, {
            timestamp: data.timestamp,
            open: data.open,
            high: data.high,
            low: data.low,
            close: data.close,
            volume: data.volume
        })
        
        // Update technical indicators
        this.indicatorManager.updateIndicators(data.symbol, data)
        
        // Trigger chart redraw
        this.chartEngine.requestRedraw()
        
        // Update price display
        this.updatePriceDisplay(data)
    }
    
    // TEST: Technical indicators setup correctly
    private setupTechnicalIndicators(): void {
        // Setup default indicators
        const defaultIndicators = [
            {
                type: IndicatorType.SMA,
                period: 20,
                color: '#FF6B6B',
                visible: true
            },
            {
                type: IndicatorType.EMA,
                period: 50,
                color: '#4ECDC4',
                visible: true
            },
            {
                type: IndicatorType.RSI,
                period: 14,
                overbought: 70,
                oversold: 30,
                panel: 'secondary'
            },
            {
                type: IndicatorType.MACD,
                fastPeriod: 12,
                slowPeriod: 26,
                signalPeriod: 9,
                panel: 'secondary'
            }
        ]
        
        defaultIndicators.forEach(indicator => {
            this.indicatorManager.addIndicator(indicator)
        })
        
        // Setup indicator calculation engine
        this.indicatorManager.setupCalculationEngine()
    }
    
    // TEST: Chart interactions respond correctly
    private setupChartInteractions(): void {
        // Setup zoom and pan
        this.interactionManager.enableZoom({
            wheelZoom: true,
            pinchZoom: true,
            boxZoom: true,
            minZoom: 0.1,
            maxZoom: 100
        })
        
        this.interactionManager.enablePan({
            mousePan: true,
            touchPan: true,
            keyboardPan: true
        })
        
        // Setup crosshair
        this.interactionManager.enableCrosshair({
            style: 'cross',
            color: '#666666',
            width: 1,
            showLabels: true
        })
        
        // Setup drawing tools
        this.setupDrawingTools()
        
        // Setup event handlers
        this.setupInteractionEventHandlers()
    }
    
    // TEST: Drawing tools work correctly
    private setupDrawingTools(): void {
        const drawingTools = [
            {
                type: 'trendline',
                icon: 'trend-line',
                shortcut: 'T',
                cursor: 'crosshair'
            },
            {
                type: 'rectangle',
                icon: 'rectangle',
                shortcut: 'R',
                cursor: 'crosshair'
            },
            {
                type: 'fibonacci',
                icon: 'fibonacci',
                shortcut: 'F',
                cursor: 'crosshair'
            },
            {
                type: 'text',
                icon: 'text',
                shortcut: 'A',
                cursor: 'text'
            }
        ]
        
        drawingTools.forEach(tool => {
            this.interactionManager.registerDrawingTool(tool)
        })
    }
    
    // TEST: Symbol switching updates chart correctly
    switchSymbol(symbol: string): void {
        // Validate symbol
        if (!this.isValidSymbol(symbol)) {
            throw new Error(`Invalid symbol: ${symbol}`)
        }
        
        // Clear current chart data
        this.chartEngine.clearData()
        
        // Update data subscriptions
        this.dataStreamManager.updateSubscription('market-data', {
            symbols: [symbol]
        })
        
        // Load historical data
        this.loadHistoricalData(symbol)
        
        // Update indicators for new symbol
        this.indicatorManager.switchSymbol(symbol)
        
        // Update UI elements
        this.updateSymbolDisplay(symbol)
        
        // Emit symbol change event
        this.emitChartEvent('symbolChanged', { symbol, timestamp: new Date() })
    }
    
    // TEST: Timeframe switching updates chart correctly
    switchTimeframe(timeframe: TimeframeType): void {
        // Validate timeframe
        if (!this.isValidTimeframe(timeframe)) {
            throw new Error(`Invalid timeframe: ${timeframe}`)
        }
        
        // Update chart configuration
        this.chartEngine.updateTimeframe(timeframe)
        
        // Update data subscription
        this.dataStreamManager.updateSubscription('market-data', {
            timeframes: [timeframe]
        })
        
        // Reload data for new timeframe
        this.reloadChartData(timeframe)
        
        // Recalculate indicators
        this.indicatorManager.recalculateIndicators(timeframe)
        
        // Update timeframe selector UI
        this.updateTimeframeSelector(timeframe)
    }
    
    // TEST: Historical data loads correctly
    private async loadHistoricalData(symbol: string): Promise<void> {
        try {
            // Show loading indicator
            this.showLoadingIndicator()
            
            // Fetch historical data
            const historicalData = await this.dataStreamManager.fetchHistoricalData({
                symbol,
                timeframe: this.chartEngine.getCurrentTimeframe(),
                limit: 1000,
                endTime: new Date()
            })
            
            // Validate data
            this.validateHistoricalData(historicalData)
            
            // Load data into chart
            this.chartEngine.loadHistoricalData(historicalData)
            
            // Calculate initial indicators
            this.indicatorManager.calculateInitialIndicators(historicalData)
            
            // Hide loading indicator
            this.hideLoadingIndicator()
            
            // Auto-fit chart to data
            this.chartEngine.autoFit()
            
        } catch (error) {
            this.handleDataLoadError(error)
        }
    }
    
    // TEST: Real-time updates maintain performance
    private startRealTimeUpdates(): void {
        // Setup update throttling
        const updateThrottle = new UpdateThrottle({
            maxUpdatesPerSecond: 10,
            batchUpdates: true,
            prioritizeLatest: true
        })
        
        // Setup performance monitoring
        const performanceMonitor = new PerformanceMonitor({
            targetFPS: 60,
            memoryThreshold: 100 * 1024 * 1024, // 100MB
            cpuThreshold: 80 // 80%
        })
        
        // Start update loop
        this.startUpdateLoop(updateThrottle, performanceMonitor)
    }
    
    // TEST: Update loop maintains smooth performance
    private startUpdateLoop(throttle: UpdateThrottle, monitor: PerformanceMonitor): void {
        const updateLoop = () => {
            // Check performance metrics
            const metrics = monitor.getMetrics()
            
            if (metrics.fps < 30) {
                // Reduce update frequency if performance is poor
                throttle.reduceFrequency()
            } else if (metrics.fps > 55) {
                // Increase update frequency if performance is good
                throttle.increaseFrequency()
            }
            
            // Process pending updates
            if (throttle.shouldUpdate()) {
                this.processQueuedUpdates()
            }
            
            // Schedule next update
            requestAnimationFrame(updateLoop)
        }
        
        // Start the loop
        requestAnimationFrame(updateLoop)
    }
    
    // TEST: Queued updates process efficiently
    private processQueuedUpdates(): void {
        const updates = this.dataStreamManager.getQueuedUpdates()
        
        if (updates.length === 0) return
        
        // Batch similar updates
        const batchedUpdates = this.batchUpdates(updates)
        
        // Process each batch
        batchedUpdates.forEach(batch => {
            switch (batch.type) {
                case 'market-data':
                    this.processBatchedMarketData(batch.updates)
                    break
                case 'sentiment-data':
                    this.processBatchedSentimentData(batch.updates)
                    break
                case 'prediction-data':
                    this.processBatchedPredictionData(batch.updates)
                    break
            }
        })
        
        // Trigger single redraw for all updates
        this.chartEngine.requestRedraw()
    }
    
    // TEST: Sentiment overlays display correctly
    private processSentimentDataUpdate(data: SentimentDataUpdate): void {
        // Create sentiment overlay
        const sentimentOverlay = {
            type: 'sentiment',
            timestamp: data.timestamp,
            value: data.sentimentScore,
            confidence: data.confidence,
            color: this.getSentimentColor(data.sentimentScore),
            opacity: data.confidence
        }
        
        // Add to overlay manager
        this.overlayManager.addOverlay('sentiment', sentimentOverlay)
        
        // Update sentiment indicator
        this.updateSentimentIndicator(data)
    }
    
    // TEST: AI prediction overlays display correctly
    private processPredictionDataUpdate(data: PredictionDataUpdate): void {
        // Create prediction overlay
        const predictionOverlay = {
            type: 'prediction',
            timestamp: data.timestamp,
            predictedPrice: data.predictedPrice,
            confidence: data.confidence,
            timeHorizon: data.timeHorizon,
            color: this.getPredictionColor(data.direction),
            style: 'dashed'
        }
        
        // Add to overlay manager
        this.overlayManager.addOverlay('prediction', predictionOverlay)
        
        // Update prediction indicator
        this.updatePredictionIndicator(data)
    }
    
    // TEST: Chart export works correctly
    exportChart(format: ExportFormat, options: ExportOptions): Promise<Blob> {
        return new Promise((resolve, reject) => {
            try {
                switch (format) {
                    case ExportFormat.PNG:
                        resolve(this.exportToPNG(options))
                        break
                    case ExportFormat.SVG:
                        resolve(this.exportToSVG(options))
                        break
                    case ExportFormat.PDF:
                        resolve(this.exportToPDF(options))
                        break
                    case ExportFormat.CSV:
                        resolve(this.exportToCSV(options))
                        break
                    default:
                        reject(new Error(`Unsupported export format: ${format}`))
                }
            } catch (error) {
                reject(error)
            }
        })
    }
    
    // TEST: Chart themes apply correctly
    applyTheme(theme: ChartTheme): void {
        // Update chart colors
        this.chartEngine.updateColors({
            background: theme.backgroundColor,
            grid: theme.gridColor,
            text: theme.textColor,
            candleUp: theme.candleUpColor,
            candleDown: theme.candleDownColor,
            volume: theme.volumeColor
        })
        
        // Update indicator colors
        this.indicatorManager.updateTheme(theme.indicators)
        
        // Update overlay colors
        this.overlayManager.updateTheme(theme.overlays)
        
        // Redraw chart with new theme
        this.chartEngine.requestRedraw()
    }
}
```

### ChartEngine

```typescript
class ChartEngine {
    private container: HTMLElement
    private canvases: Map<string, HTMLCanvasElement>
    private contexts: Map<string, CanvasRenderingContext2D>
    private dataSeries: Map<string, DataSeries>
    private coordinateSystem: CoordinateSystem
    private renderQueue: RenderQueue
    
    // TEST: Chart engine initializes with proper configuration
    constructor(container: HTMLElement, config: ChartConfig) {
        this.container = container
        this.canvases = new Map()
        this.contexts = new Map()
        this.dataSeries = new Map()
        this.coordinateSystem = new CoordinateSystem(config.coordinates)
        this.renderQueue = new RenderQueue()
        
        // Setup resize observer
        this.setupResizeObserver()
        
        // Initialize rendering pipeline
        this.initializeRenderingPipeline()
    }
    
    // TEST: Canvas creation works correctly
    createCanvas(name: string, config: CanvasConfig): HTMLCanvasElement {
        const canvas = document.createElement('canvas')
        canvas.width = config.width * config.devicePixelRatio
        canvas.height = config.height * config.devicePixelRatio
        canvas.style.width = `${config.width}px`
        canvas.style.height = `${config.height}px`
        canvas.style.position = 'absolute'
        canvas.style.top = '0'
        canvas.style.left = '0'
        
        // Get rendering context
        const context = canvas.getContext('2d', {
            alpha: true,
            antialias: config.antialias,
            preserveDrawingBuffer: config.preserveDrawingBuffer
        })
        
        // Scale context for high DPI displays
        context.scale(config.devicePixelRatio, config.devicePixelRatio)
        
        // Store canvas and context
        this.canvases.set(name, canvas)
        this.contexts.set(name, context)
        
        // Add to container
        this.container.appendChild(canvas)
        
        return canvas
    }
    
    // TEST: Data series updates correctly
    updateDataSeries(symbol: string, dataPoint: DataPoint): void {
        let series = this.dataSeries.get(symbol)
        
        if (!series) {
            series = new DataSeries(symbol)
            this.dataSeries.set(symbol, series)
        }
        
        // Add data point to series
        series.addDataPoint(dataPoint)
        
        // Update coordinate system bounds
        this.coordinateSystem.updateBounds(dataPoint)
        
        // Queue render update
        this.renderQueue.queueUpdate('data-series', symbol)
    }
    
    // TEST: Rendering pipeline processes efficiently
    private initializeRenderingPipeline(): void {
        const pipeline = new RenderingPipeline([
            new BackgroundRenderer(),
            new GridRenderer(),
            new DataSeriesRenderer(),
            new IndicatorRenderer(),
            new OverlayRenderer(),
            new UIElementRenderer()
        ])
        
        this.renderQueue.setPipeline(pipeline)
    }
    
    // TEST: Chart redraw maintains performance
    requestRedraw(): void {
        if (this.renderQueue.isRenderPending()) {
            return // Avoid duplicate render requests
        }
        
        this.renderQueue.scheduleRender(() => {
            this.performRender()
        })
    }
    
    // TEST: Render performance meets targets
    private performRender(): void {
        const startTime = performance.now()
        
        // Clear all canvases
        this.clearCanvases()
        
        // Render each layer
        this.renderBackground()
        this.renderGrid()
        this.renderDataSeries()
        this.renderIndicators()
        this.renderOverlays()
        this.renderUI()
        
        const renderTime = performance.now() - startTime
        
        // Log performance metrics
        this.logRenderPerformance(renderTime)
        
        // Check if render time exceeds threshold
        if (renderTime > 16.67) { // 60 FPS threshold
            this.optimizeRenderingStrategy()
        }
    }
    
    // TEST: Auto-fit adjusts chart view correctly
    autoFit(): void {
        const allData = Array.from(this.dataSeries.values())
            .flatMap(series => series.getAllDataPoints())
        
        if (allData.length === 0) return
        
        // Calculate data bounds
        const bounds = this.calculateDataBounds(allData)
        
        // Add padding
        const padding = {
            top: 0.1,
            bottom: 0.1,
            left: 0.05,
            right: 0.05
        }
        
        // Update coordinate system
        this.coordinateSystem.setBounds({
            xMin: bounds.xMin - (bounds.xMax - bounds.xMin) * padding.left,
            xMax: bounds.xMax + (bounds.xMax - bounds.xMin) * padding.right,
            yMin: bounds.yMin - (bounds.yMax - bounds.yMin) * padding.bottom,
            yMax: bounds.yMax + (bounds.yMax - bounds.yMin) * padding.top
        })
        
        // Request redraw
        this.requestRedraw()
    }
}
```

### IndicatorManager

```typescript
class IndicatorManager {
    private indicators: Map<string, TechnicalIndicator>
    private calculationEngine: IndicatorCalculationEngine
    private renderEngine: IndicatorRenderEngine
    
    // TEST: Indicator manager initializes correctly
    constructor() {
        this.indicators = new Map()
        this.calculationEngine = new IndicatorCalculationEngine()
        this.renderEngine = new IndicatorRenderEngine()
        
        // Register built-in indicators
        this.registerBuiltInIndicators()
    }
    
    // TEST: Built-in indicators register correctly
    private registerBuiltInIndicators(): void {
        // Moving averages
        this.calculationEngine.register('SMA', new SMACalculator())
        this.calculationEngine.register('EMA', new EMACalculator())
        this.calculationEngine.register('WMA', new WMACalculator())
        
        // Oscillators
        this.calculationEngine.register('RSI', new RSICalculator())
        this.calculationEngine.register('MACD', new MACDCalculator())
        this.calculationEngine.register('Stochastic', new StochasticCalculator())
        
        // Volatility indicators
        this.calculationEngine.register('BollingerBands', new BollingerBandsCalculator())
        this.calculationEngine.register('ATR', new ATRCalculator())
        
        // Volume indicators
        this.calculationEngine.register('VolumeProfile', new VolumeProfileCalculator())
        this.calculationEngine.register('OBV', new OBVCalculator())
    }
    
    // TEST: Indicator addition works correctly
    addIndicator(config: IndicatorConfig): string {
        const indicatorId = generateId()
        
        // Create indicator instance
        const indicator = new TechnicalIndicator({
            id: indicatorId,
            type: config.type,
            parameters: config.parameters,
            style: config.style,
            panel: config.panel || 'main'
        })
        
        // Store indicator
        this.indicators.set(indicatorId, indicator)
        
        // Initialize calculation
        this.calculationEngine.initialize(indicator)
        
        // Setup rendering
        this.renderEngine.setupIndicator(indicator)
        
        return indicatorId
    }
    
    // TEST: Indicator updates calculate correctly
    updateIndicators(symbol: string, data: MarketDataUpdate): void {
        this.indicators.forEach(indicator => {
            if (indicator.appliesToSymbol(symbol)) {
                // Calculate new values
                const newValues = this.calculationEngine.calculate(indicator, data)
                
                // Update indicator data
                indicator.addValues(newValues)
                
                // Queue for rendering
                this.renderEngine.queueUpdate(indicator.id)
            }
        })
    }
}
```

## Type Definitions

```typescript
interface ChartConfig {
    width: number
    height: number
    coordinates: CoordinateSystemConfig
    theme: ChartTheme
    performance: PerformanceConfig
}

interface MarketDataUpdate {
    symbol: string
    timestamp: Date
    open: number
    high: number
    low: number
    close: number
    volume: number
}

interface SentimentDataUpdate {
    symbol: string
    timestamp: Date
    sentimentScore: number
    confidence: number
    sources: string[]
}

interface PredictionDataUpdate {
    symbol: string
    timestamp: Date
    predictedPrice: number
    confidence: number
    timeHorizon: number
    direction: 'up' | 'down' | 'neutral'
}

enum TimeframeType {
    ONE_MINUTE = '1m',
    FIVE_MINUTES = '5m',
    FIFTEEN_MINUTES = '15m',
    ONE_HOUR = '1h',
    FOUR_HOURS = '4h',
    ONE_DAY = '1d',
    ONE_WEEK = '1w'
}

enum IndicatorType {
    SMA = 'sma',
    EMA = 'ema',
    RSI = 'rsi',
    MACD = 'macd',
    BOLLINGER_BANDS = 'bollinger_bands',
    VOLUME = 'volume'
}

enum ExportFormat {
    PNG = 'png',
    SVG = 'svg',
    PDF = 'pdf',
    CSV = 'csv'
}