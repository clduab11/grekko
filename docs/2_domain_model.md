# Domain Model for Autonomous Cryptocurrency Trading System

## 1. Overview
This document defines the core entities, relationships, and data structures for the autonomous cryptocurrency trading system within the Grekko platform. The model ensures modularity, aligns with SPARC principles, and supports integration with existing components.

## 2. Core Entities and Attributes

### 2.1 TradingAgent
- **Description**: Represents an autonomous agent responsible for making trading decisions.
- **Attributes**:
  - AgentID: Unique identifier for the agent.
  - Mode: Operational mode (e.g., aggressive, conservative) influencing trading behavior.
  - Status: Current operational status (active, idle, error).
  - DecisionHistory: Record of past trading decisions for analysis.
- **Validation Rules**: Mode must be a predefined value; Status must reflect real-time state.

### 2.2 TradeOrder
- **Description**: Represents a trading instruction issued by an agent or system.
- **Attributes**:
  - OrderID: Unique identifier for the order.
  - AgentID: Reference to the issuing TradingAgent.
  - Type: Order type (buy, sell, limit, market).
  - Asset: Cryptocurrency or token being traded.
  - Quantity: Amount to trade.
  - Price: Target price or market price at execution.
  - Status: Order status (pending, executed, failed).
  - Timestamp: Time of order creation and execution.
- **Validation Rules**: Quantity and Price must be positive; Status must transition logically.

### 2.3 Wallet
- **Description**: Manages cryptocurrency holdings and interactions via Metamask or other providers.
- **Attributes**:
  - WalletID: Unique identifier for the wallet.
  - Address: Blockchain address for transactions.
  - Balance: Current holdings per asset.
  - ConnectionStatus: Status of connection to wallet provider (connected, disconnected).
- **Validation Rules**: Address must conform to blockchain format; Balance must be non-negative.

### 2.4 ExchangeConnection
- **Description**: Represents connectivity to an exchange like Coinbase for trading operations.
- **Attributes**:
  - ConnectionID: Unique identifier for the connection.
  - ExchangeName: Name of the exchange (e.g., Coinbase).
  - AuthenticationStatus: Status of API authentication (authenticated, expired, failed).
  - Latency: Current latency in milliseconds for API calls.
- **Validation Rules**: Latency must be monitored and reported; AuthenticationStatus must trigger alerts on failure.

### 2.5 MCPTool
- **Description**: Represents an MCP tool used for autonomous operations or research.
- **Attributes**:
  - ToolID: Unique identifier for the tool.
  - Name: Tool name (e.g., Playwright, Tavily).
  - Purpose: Intended use (automation, research).
  - IntegrationStatus: Status of integration with Grekko (active, inactive).
- **Validation Rules**: Purpose must align with trading system needs; IntegrationStatus must be verifiable.

## 3. Relationships

- **TradingAgent to TradeOrder**: One-to-Many. A single agent can issue multiple orders.
  - **Business Rule**: Agents must log all orders for audit and performance tracking.
- **TradeOrder to ExchangeConnection**: Many-to-One. Multiple orders can be routed through a single exchange connection.
  - **Business Rule**: Orders must be routed to the exchange with the lowest latency when possible.
- **Wallet to TradeOrder**: One-to-Many. A wallet can be associated with multiple orders for asset transactions.
  - **Business Rule**: Wallet balance must be sufficient before order execution.
- **TradingAgent to MCPTool**: Many-to-Many. Agents can utilize multiple MCP tools for decision-making or automation.
  - **Business Rule**: Tool usage must be logged and justified by agent mode.

## 4. Data Structures

### 4.1 AgentConfiguration
- **Purpose**: Defines settings for TradingAgent behavior based on mode.
- **Structure**:
  - Mode: String (enum: aggressive, conservative, balanced).
  - RiskTolerance: Float (0.0 to 1.0).
  - TradeFrequency: Integer (trades per hour limit).
  - PreferredAssets: List of Strings (symbols of focus assets).
- **Validation**: RiskTolerance must be within range; TradeFrequency must be positive.

### 4.2 OrderExecutionLog
- **Purpose**: Records details of trade order execution for audit and analysis.
- **Structure**:
  - OrderID: String (reference to TradeOrder).
  - ExecutionTime: Timestamp.
  - ActualPrice: Float.
  - Fees: Float.
  - Outcome: String (success, partial, failed).
  - ErrorMessage: String (if applicable).
- **Validation**: ExecutionTime must be after order creation; Fees must be non-negative.

### 4.3 RiskAssessment
- **Purpose**: Captures risk evaluation for trading decisions.
- **Structure**:
  - AssessmentID: String.
  - AgentID: String (reference to TradingAgent).
  - OrderID: String (reference to TradeOrder, if applicable).
  - RiskLevel: Float (0.0 to 1.0).
  - MitigationStrategy: String (description of action if risk is high).
- **Validation**: RiskLevel must be within range; MitigationStrategy must be defined for high risk.

## 5. State Transitions

### 5.1 TradeOrder Lifecycle
- **States**: Created -> Pending -> Executed/Failed/Cancelled.
- **Transitions**:
  - Created to Pending: On submission to exchange.
  - Pending to Executed: On successful trade completion.
  - Pending to Failed: On exchange rejection or timeout.
  - Pending to Cancelled: On agent or user intervention.
- **Business Rule**: All transitions must be logged with timestamps and reasons.

### 5.2 Agent Mode Switching
- **States**: Aggressive -> Conservative -> Balanced (and vice versa).
- **Transitions**:
  - Triggered by market conditions or manual configuration.
- **Business Rule**: Mode switch must not interrupt ongoing trades; must log rationale.

## 6. Invariants and Business Rules
- Wallet balance must always be sufficient for pending orders.
- Agent decisions must align with configured risk tolerance.
- Exchange connections must be re-authenticated on status failure.
- All trading actions must be traceable to an agent or system decision.

## 7. Domain-Specific Terminology
- **Agent Mode**: Configuration setting determining trading strategy aggressiveness.
- **Latency Optimization**: Techniques to minimize delay in trade execution.
- **Multi-Agent Coordination**: Protocols for consensus among multiple trading agents.

## 8. Aggregate Boundaries
- **Trading Cluster**: Includes TradingAgent, TradeOrder, and RiskAssessment.
  - **Consistency Rule**: All trades within a cluster must adhere to the agent's risk profile.
- **Execution Cluster**: Includes ExchangeConnection, TradeOrder, and OrderExecutionLog.
  - **Consistency Rule**: Execution logs must reflect the exact state of exchange interactions.

## 9. Events and Event Flows
- **TradeDecisionEvent**: Triggered by TradingAgent when a trade is decided.
  - Flow: Agent -> TradeOrder creation -> RiskAssessment.
- **OrderExecutionEvent**: Triggered by ExchangeConnection on order completion.
  - Flow: Exchange -> OrderExecutionLog -> Agent notification.
- **RiskThresholdBreachEvent**: Triggered by RiskAssessment if risk exceeds tolerance.
  - Flow: RiskAssessment -> Agent mode adjustment -> Trade cancellation if needed.

## 10. Queries and Read Models
- **AgentPerformanceQuery**: Retrieves historical decision accuracy and profit/loss for an agent.
- **OrderStatusReadModel**: Provides real-time status of all active orders for monitoring.
- **RiskExposureQuery**: Aggregates risk levels across all agents and orders for dashboard reporting.