# Phase 4: Frontend UI Overhaul - Domain Model

## Domain Overview

The Phase 4 Frontend UI Overhaul domain encompasses the user interface layer of the Grekko trading platform, providing a comprehensive desktop application for trading, portfolio management, and AI agent interaction. The domain integrates with all backend systems from Phases 1-3 while maintaining a clean separation of concerns.

## Core Entities

### UI Application Shell

#### ElectronApplication
**Description**: Main application container managing the Electron framework
**Attributes**:
- `applicationId`: string (unique identifier)
- `version`: string (semantic version)
- `windowState`: WindowState (current window configuration)
- `ipcChannels`: Map<string, IPCChannel> (communication channels)
- `securityPolicy`: SecurityPolicy (CSP and security settings)
- `updateStatus`: UpdateStatus (auto-update state)

**Relationships**:
- Contains multiple `ApplicationWindow` instances
- Manages `IPCBridge` for process communication
- Coordinates with `SecurityManager` for secure operations

#### ApplicationWindow
**Description**: Individual window instance with layout management
**Attributes**:
- `windowId`: string (unique window identifier)
- `layout`: LayoutConfiguration (three-panel layout settings)
- `theme`: ThemeConfiguration (visual appearance)
- `state`: WindowState (minimized, maximized, fullscreen)
- `dimensions`: WindowDimensions (size and position)
- `isActive`: boolean (focus state)

**Relationships**:
- Contains one `MainChartPanel`, one `NewsSidebar`, one `AgentSidebar`
- Managed by `ElectronApplication`
- Communicates through `IPCBridge`

### Chart and Visualization

#### MainChartPanel
**Description**: Primary charting interface with advanced visualization
**Attributes**:
- `chartId`: string (unique chart identifier)
- `activeSymbol`: string (currently displayed asset)
- `timeframe`: TimeframeType (1m, 5m, 1h, 1d, etc.)
- `chartType`: ChartType (candlestick, line, area)
- `indicators`: TechnicalIndicator[] (active technical indicators)
- `overlays`: ChartOverlay[] (sentiment, predictions, positions)
- `zoomLevel`: number (chart zoom factor)
- `viewportRange`: DateRange (visible time range)

**Relationships**:
- Receives data from `MarketDataStream`
- Displays `TradingPosition` overlays
- Integrates with `SentimentVisualization`
- Managed by `ChartController`

#### TechnicalIndicator
**Description**: Technical analysis indicators on charts
**Attributes**:
- `indicatorId`: string (unique identifier)
- `type`: IndicatorType (SMA, EMA, RSI, MACD, etc.)
- `parameters`: Map<string, any> (indicator-specific settings)
- `isVisible`: boolean (display state)
- `color`: string (visual color)
- `lineStyle`: LineStyle (solid, dashed, dotted)

**Relationships**:
- Belongs to `MainChartPanel`
- Calculated by `IndicatorEngine`
- Configured through `IndicatorSettings`

#### ChartOverlay
**Description**: Additional data layers on charts
**Attributes**:
- `overlayId`: string (unique identifier)
- `type`: OverlayType (sentiment, prediction, position, news)
- `data`: any[] (overlay-specific data)
- `opacity`: number (transparency level)
- `zIndex`: number (layer ordering)
- `isInteractive`: boolean (user interaction enabled)

**Relationships**:
- Displayed on `MainChartPanel`
- Sources data from various backend services
- Managed by `OverlayManager`

### News and Social Media

#### NewsSidebar
**Description**: Left sidebar displaying curated news and social sentiment
**Attributes**:
- `sidebarId`: string (unique identifier)
- `activeFilters`: NewsFilter[] (content filtering)
- `refreshInterval`: number (update frequency in ms)
- `maxItems`: number (maximum displayed items)
- `scrollPosition`: number (current scroll state)
- `isCollapsed`: boolean (sidebar visibility)

**Relationships**:
- Contains multiple `NewsItem` instances
- Displays `SentimentIndicator` components
- Managed by `NewsController`
- Receives data from `NewsAggregator`

#### NewsItem
**Description**: Individual news article or social media post
**Attributes**:
- `itemId`: string (unique identifier)
- `title`: string (headline or summary)
- `content`: string (full content)
- `source`: string (news source or platform)
- `publishedAt`: Date (publication timestamp)
- `relevanceScore`: number (AI-calculated relevance)
- `sentimentScore`: number (-1 to 1, negative to positive)
- `assetTags`: string[] (related assets)
- `url`: string (source link)
- `imageUrl`: string (optional thumbnail)

**Relationships**:
- Displayed in `NewsSidebar`
- Analyzed by `SentimentAnalyzer`
- Filtered by `NewsFilter`

#### SentimentIndicator
**Description**: Visual representation of market sentiment
**Attributes**:
- `indicatorId`: string (unique identifier)
- `asset`: string (target asset symbol)
- `sentimentScore`: number (aggregated sentiment)
- `confidence`: number (prediction confidence)
- `trendDirection`: TrendDirection (bullish, bearish, neutral)
- `timeframe`: TimeframeType (sentiment calculation period)
- `lastUpdated`: Date (last calculation time)

**Relationships**:
- Displayed in `NewsSidebar` and `MainChartPanel`
- Calculated by `SentimentEngine`
- Influences `TradingSignal` generation

### AI Agent Management

#### AgentSidebar
**Description**: Right sidebar for AI agent selection and configuration
**Attributes**:
- `sidebarId`: string (unique identifier)
- `activeAgent`: TradingAgent (currently selected agent)
- `agentList`: TradingAgent[] (available agents)
- `configurationPanel`: AgentConfigPanel (settings interface)
- `performanceMetrics`: AgentMetrics (real-time performance)
- `isCollapsed`: boolean (sidebar visibility)

**Relationships**:
- Contains multiple `TradingAgent` instances
- Manages `AgentConfigPanel`
- Displays `AgentMetrics`
- Controlled by `AgentController`

#### TradingAgent
**Description**: AI trading agent with specific capabilities and autonomy levels
**Attributes**:
- `agentId`: string (unique identifier)
- `name`: string (display name: Spot, Gordo, Gordon Gekko)
- `type`: AgentType (tutor, semi_autonomous, autonomous)
- `status`: AgentStatus (active, inactive, paused, error)
- `autonomyLevel`: AutonomyLevel (permission requirements)
- `capabilities`: AgentCapability[] (supported features)
- `riskParameters`: RiskParameters (trading limits)
- `performance`: AgentPerformance (historical metrics)
- `configuration`: AgentConfiguration (user settings)

**Relationships**:
- Managed by `AgentController`
- Executes through `TradingExecutor`
- Monitored by `PerformanceTracker`
- Configured through `AgentConfigPanel`

#### AgentConfigPanel
**Description**: Configuration interface for agent settings
**Attributes**:
- `panelId`: string (unique identifier)
- `targetAgent`: TradingAgent (agent being configured)
- `riskSettings`: RiskSettings (risk management parameters)
- `tradingSettings`: TradingSettings (execution preferences)
- `permissionSettings`: PermissionSettings (autonomy controls)
- `notificationSettings`: NotificationSettings (alert preferences)
- `isDirty`: boolean (unsaved changes indicator)

**Relationships**:
- Configures `TradingAgent` instances
- Validates through `ConfigurationValidator`
- Persists via `SettingsManager`

### Trading and Portfolio

#### TradingInterface
**Description**: Direct trading execution interface
**Attributes**:
- `interfaceId`: string (unique identifier)
- `activeWallet`: WalletConnection (connected wallet)
- `orderForm`: OrderForm (trade input form)
- `orderHistory`: TradingOrder[] (recent orders)
- `positionSummary`: PositionSummary (current positions)
- `riskMetrics`: RiskMetrics (real-time risk assessment)

**Relationships**:
- Connects to `WalletConnection` instances
- Submits `TradingOrder` requests
- Displays `TradingPosition` data
- Validates through `RiskManager`

#### TradingOrder
**Description**: Individual trading order with execution details
**Attributes**:
- `orderId`: string (unique identifier)
- `symbol`: string (trading pair)
- `side`: OrderSide (buy, sell)
- `type`: OrderType (market, limit, stop)
- `quantity`: number (order size)
- `price`: number (limit price, if applicable)
- `status`: OrderStatus (pending, filled, cancelled, rejected)
- `timestamp`: Date (order creation time)
- `executionPrice`: number (actual fill price)
- `fees`: number (transaction fees)
- `walletId`: string (executing wallet)

**Relationships**:
- Submitted through `TradingInterface`
- Executed by `OrderExecutor`
- Tracked in `OrderHistory`
- Affects `TradingPosition`

#### TradingPosition
**Description**: Current trading position in an asset
**Attributes**:
- `positionId`: string (unique identifier)
- `symbol`: string (asset symbol)
- `side`: PositionSide (long, short)
- `size`: number (position size)
- `entryPrice`: number (average entry price)
- `currentPrice`: number (current market price)
- `unrealizedPnL`: number (unrealized profit/loss)
- `realizedPnL`: number (realized profit/loss)
- `openTime`: Date (position open timestamp)
- `walletId`: string (holding wallet)

**Relationships**:
- Created by `TradingOrder` execution
- Displayed on `MainChartPanel`
- Managed by `PositionManager`
- Monitored by `RiskManager`

### Wallet and Connection Management

#### WalletConnection
**Description**: Connection to external wallet providers
**Attributes**:
- `connectionId`: string (unique identifier)
- `walletType`: WalletType (metamask, coinbase, walletconnect)
- `address`: string (wallet address)
- `chainId`: number (blockchain network)
- `status`: ConnectionStatus (connected, disconnected, error)
- `permissions`: WalletPermission[] (granted permissions)
- `lastActivity`: Date (last interaction time)
- `balance`: AssetBalance[] (wallet balances)

**Relationships**:
- Managed by `WalletManager`
- Used by `TradingInterface`
- Monitored by `ConnectionMonitor`
- Secured by `SecurityManager`

#### AssetBalance
**Description**: Balance of a specific asset in a wallet
**Attributes**:
- `asset`: string (asset symbol)
- `balance`: number (available balance)
- `locked`: number (locked/reserved balance)
- `value`: number (USD value)
- `lastUpdated`: Date (last balance update)

**Relationships**:
- Belongs to `WalletConnection`
- Updated by `BalanceTracker`
- Displayed in `PortfolioDashboard`

### Real-Time Data Management

#### MarketDataStream
**Description**: Real-time market data feed management
**Attributes**:
- `streamId`: string (unique identifier)
- `subscribedSymbols`: string[] (active subscriptions)
- `connectionStatus`: ConnectionStatus (stream health)
- `latency`: number (data latency in ms)
- `messageRate`: number (messages per second)
- `lastUpdate`: Date (last data received)

**Relationships**:
- Feeds data to `MainChartPanel`
- Managed by `DataStreamManager`
- Monitored by `LatencyMonitor`

#### WebSocketConnection
**Description**: WebSocket connection to backend services
**Attributes**:
- `connectionId`: string (unique identifier)
- `endpoint`: string (WebSocket URL)
- `status`: ConnectionStatus (connection state)
- `reconnectAttempts`: number (retry counter)
- `lastPing`: Date (last heartbeat)
- `subscriptions`: Subscription[] (active subscriptions)

**Relationships**:
- Managed by `WebSocketManager`
- Used by `MarketDataStream`
- Monitored by `ConnectionHealthMonitor`

## Value Objects

### Configuration Objects

#### LayoutConfiguration
**Attributes**:
- `leftSidebarWidth`: number (news sidebar width)
- `rightSidebarWidth`: number (agent sidebar width)
- `chartAreaHeight`: number (main chart height)
- `panelSpacing`: number (gap between panels)
- `isLeftSidebarCollapsed`: boolean
- `isRightSidebarCollapsed`: boolean

#### ThemeConfiguration
**Attributes**:
- `themeName`: string (theme identifier)
- `primaryColor`: string (main accent color)
- `backgroundColor`: string (background color)
- `textColor`: string (text color)
- `chartColors`: ChartColorScheme (chart-specific colors)
- `isDarkMode`: boolean (dark/light mode)

#### RiskParameters
**Attributes**:
- `maxPositionSize`: number (maximum position size)
- `maxDailyLoss`: number (daily loss limit)
- `stopLossPercentage`: number (automatic stop loss)
- `takeProfitPercentage`: number (automatic take profit)
- `maxOpenPositions`: number (position count limit)

### Data Transfer Objects

#### MarketDataPoint
**Attributes**:
- `symbol`: string (asset symbol)
- `timestamp`: Date (data timestamp)
- `open`: number (opening price)
- `high`: number (high price)
- `low`: number (low price)
- `close`: number (closing price)
- `volume`: number (trading volume)

#### TradingSignal
**Attributes**:
- `signalId`: string (unique identifier)
- `symbol`: string (target asset)
- `direction`: SignalDirection (buy, sell, hold)
- `strength`: number (signal strength 0-1)
- `confidence`: number (confidence level 0-1)
- `source`: SignalSource (agent, indicator, sentiment)
- `timestamp`: Date (signal generation time)

## Enumerations

### UI State Enums

```typescript
enum WindowState {
  NORMAL = "normal",
  MINIMIZED = "minimized", 
  MAXIMIZED = "maximized",
  FULLSCREEN = "fullscreen"
}

enum ConnectionStatus {
  CONNECTED = "connected",
  DISCONNECTED = "disconnected",
  CONNECTING = "connecting",
  ERROR = "error",
  RECONNECTING = "reconnecting"
}

enum AgentType {
  TUTOR = "tutor",
  SEMI_AUTONOMOUS = "semi_autonomous", 
  AUTONOMOUS = "autonomous"
}

enum AgentStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  PAUSED = "paused",
  ERROR = "error",
  CONFIGURING = "configuring"
}
```

### Trading Enums

```typescript
enum OrderSide {
  BUY = "buy",
  SELL = "sell"
}

enum OrderType {
  MARKET = "market",
  LIMIT = "limit",
  STOP = "stop",
  STOP_LIMIT = "stop_limit"
}

enum OrderStatus {
  PENDING = "pending",
  FILLED = "filled",
  PARTIALLY_FILLED = "partially_filled",
  CANCELLED = "cancelled",
  REJECTED = "rejected"
}

enum PositionSide {
  LONG = "long",
  SHORT = "short"
}
```

### Chart Enums

```typescript
enum ChartType {
  CANDLESTICK = "candlestick",
  LINE = "line",
  AREA = "area",
  HEIKIN_ASHI = "heikin_ashi"
}

enum TimeframeType {
  ONE_MINUTE = "1m",
  FIVE_MINUTES = "5m",
  FIFTEEN_MINUTES = "15m",
  ONE_HOUR = "1h",
  FOUR_HOURS = "4h",
  ONE_DAY = "1d",
  ONE_WEEK = "1w"
}

enum IndicatorType {
  SMA = "sma",
  EMA = "ema",
  RSI = "rsi",
  MACD = "macd",
  BOLLINGER_BANDS = "bollinger_bands",
  VOLUME = "volume"
}
```

## Domain Services

### Core Controllers

#### ApplicationController
**Responsibilities**:
- Manage application lifecycle
- Coordinate window management
- Handle application-level events
- Manage global state

#### ChartController
**Responsibilities**:
- Manage chart rendering and updates
- Handle user interactions with charts
- Coordinate indicator calculations
- Manage chart overlays

#### AgentController
**Responsibilities**:
- Manage AI agent lifecycle
- Handle agent configuration changes
- Coordinate agent execution
- Monitor agent performance

#### TradingController
**Responsibilities**:
- Manage trading operations
- Validate trading requests
- Coordinate order execution
- Handle trading errors

### Data Management Services

#### DataStreamManager
**Responsibilities**:
- Manage real-time data connections
- Handle data subscription management
- Coordinate data distribution
- Monitor connection health

#### StateManager
**Responsibilities**:
- Manage application state
- Handle state persistence
- Coordinate state synchronization
- Manage state validation

#### CacheManager
**Responsibilities**:
- Manage data caching strategies
- Handle cache invalidation
- Optimize data retrieval
- Manage memory usage

## Domain Events

### Application Events

```typescript
interface ApplicationStartedEvent {
  applicationId: string;
  version: string;
  timestamp: Date;
}

interface WindowStateChangedEvent {
  windowId: string;
  previousState: WindowState;
  newState: WindowState;
  timestamp: Date;
}
```

### Trading Events

```typescript
interface OrderSubmittedEvent {
  orderId: string;
  symbol: string;
  side: OrderSide;
  quantity: number;
  timestamp: Date;
}

interface PositionOpenedEvent {
  positionId: string;
  symbol: string;
  side: PositionSide;
  size: number;
  entryPrice: number;
  timestamp: Date;
}
```

### Agent Events

```typescript
interface AgentActivatedEvent {
  agentId: string;
  agentType: AgentType;
  configuration: AgentConfiguration;
  timestamp: Date;
}

interface TradingSignalGeneratedEvent {
  signalId: string;
  agentId: string;
  symbol: string;
  direction: SignalDirection;
  strength: number;
  timestamp: Date;
}
```

## Domain Rules and Invariants

### Business Rules

1. **Agent Autonomy Rule**: Autonomous agents can execute trades without user confirmation, semi-autonomous agents require approval for trades above configured thresholds
2. **Risk Management Rule**: All trading operations must pass risk validation before execution
3. **Connection Security Rule**: All external connections must be authenticated and encrypted
4. **Data Consistency Rule**: UI state must remain consistent with backend data sources
5. **Performance Rule**: UI updates must not block user interactions

### Data Invariants

1. **Position Consistency**: Sum of position sizes must equal wallet balances
2. **Order Validation**: Orders cannot exceed available balances
3. **Agent Configuration**: Agent risk parameters must be within system limits
4. **Connection State**: Only one active connection per wallet type per session
5. **Chart Data Integrity**: Chart data must be chronologically ordered

## Integration Boundaries

### External System Integrations

#### Phase 1 Backend Integration
- **Wallet Providers**: MetaMask, Coinbase, WalletConnect
- **Exchange APIs**: Real-time market data and order execution
- **Authentication**: Secure session management

#### Phase 2 Backend Integration
- **NFT Services**: Collection data and trading interfaces
- **DeFi Protocols**: Yield farming and liquidity provision
- **Derivatives**: Futures and options trading

#### Phase 3 Backend Integration
- **AI Models**: Predictive analytics and sentiment analysis
- **Market Making**: Automated liquidity provision
- **Flash Loans**: Arbitrage opportunity detection

### Internal Service Boundaries

#### UI Layer Boundaries
- **Presentation**: React components and UI logic
- **State Management**: Redux store and middleware
- **Data Layer**: API clients and WebSocket managers

#### Cross-Cutting Concerns
- **Security**: Authentication, authorization, encryption
- **Logging**: Application events and error tracking
- **Monitoring**: Performance metrics and health checks
- **Configuration**: Environment-specific settings

This domain model provides the foundation for implementing the Phase 4 Frontend UI Overhaul with clear entity relationships, well-defined boundaries, and comprehensive integration points with all backend systems.