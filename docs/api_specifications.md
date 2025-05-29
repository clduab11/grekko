# API Specifications for Autonomous Trading System

## 1. Overview

This document defines the REST API specifications for all microservices in the autonomous cryptocurrency trading system. All APIs follow OpenAPI 3.0 standards with consistent error handling, authentication, and response formats.

## 2. Common API Standards

### 2.1 Base URL Structure
```
https://api.grekko.trading/v1/{service}/{resource}
```

### 2.2 Authentication
All APIs use JWT Bearer tokens with the following header:
```
Authorization: Bearer <jwt_token>
```

### 2.3 Standard Response Format
```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid",
    "version": "v1"
  }
}
```

### 2.4 Error Response Format
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "quantity",
      "reason": "must be positive"
    }
  },
  "metadata": {
    "timestamp": "2025-01-01T00:00:00Z",
    "request_id": "uuid",
    "version": "v1"
  }
}
```

### 2.5 HTTP Status Codes
- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## 3. Agent Coordination Service API

### 3.1 Agent Management

#### Register Agent
```http
POST /v1/coordination/agents/register
Content-Type: application/json

{
  "agent_id": "uuid",
  "mode": "aggressive",
  "capabilities": ["trading", "risk_assessment"],
  "risk_tolerance": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "uuid",
    "status": "registered",
    "channel_id": "uuid",
    "registered_at": "2025-01-01T00:00:00Z"
  }
}
```

#### Get Agent Status
```http
GET /v1/coordination/agents/{agent_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "uuid",
    "mode": "aggressive",
    "status": "active",
    "last_activity": "2025-01-01T00:00:00Z",
    "coordination_stats": {
      "proposals_submitted": 15,
      "consensus_participation": 0.95,
      "success_rate": 0.87
    }
  }
}
```

### 3.2 Proposal Management

#### Submit Trade Proposal
```http
POST /v1/coordination/proposals
Content-Type: application/json

{
  "agent_id": "uuid",
  "proposal": {
    "symbol": "BTC-USD",
    "action": "buy",
    "quantity": 0.1,
    "price": 50000,
    "rationale": "Technical analysis indicates bullish trend"
  },
  "timeout_ms": 500
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "proposal_id": "uuid",
    "status": "pending",
    "submitted_at": "2025-01-01T00:00:00Z",
    "timeout_at": "2025-01-01T00:00:00.500Z"
  }
}
```

#### Get Proposal Status
```http
GET /v1/coordination/proposals/{proposal_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "proposal_id": "uuid",
    "status": "consensus_reached",
    "responses": [
      {
        "agent_id": "uuid",
        "response": "agree",
        "rationale": "Aligns with risk parameters",
        "responded_at": "2025-01-01T00:00:00.200Z"
      }
    ],
    "consensus": {
      "agreement_percentage": 0.8,
      "threshold_met": true,
      "final_decision": "approved"
    }
  }
}
```

## 4. Risk Management Service API

### 4.1 Risk Assessment

#### Assess Trade Risk
```http
POST /v1/risk/assess
Content-Type: application/json

{
  "agent_id": "uuid",
  "trade": {
    "symbol": "BTC-USD",
    "action": "buy",
    "quantity": 0.1,
    "price": 50000
  },
  "portfolio_context": {
    "current_positions": [
      {
        "symbol": "BTC-USD",
        "quantity": 0.5,
        "avg_price": 48000
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "assessment_id": "uuid",
    "risk_level": 0.3,
    "risk_category": "low",
    "factors": [
      {
        "type": "position_size",
        "impact": 0.1,
        "description": "Position size within limits"
      },
      {
        "type": "correlation",
        "impact": 0.2,
        "description": "High correlation with existing positions"
      }
    ],
    "recommendation": "approved",
    "mitigation_strategies": [
      "Set stop-loss at 5% below entry"
    ]
  }
}
```

### 4.2 Exposure Management

#### Get Portfolio Exposure
```http
GET /v1/risk/exposure/{agent_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "uuid",
    "total_exposure": 125000,
    "risk_metrics": {
      "var_95": 5000,
      "max_drawdown": 0.15,
      "sharpe_ratio": 1.2
    },
    "position_breakdown": [
      {
        "symbol": "BTC-USD",
        "exposure": 50000,
        "percentage": 0.4,
        "risk_contribution": 0.6
      }
    ],
    "limits": {
      "max_position_size": 0.3,
      "max_total_exposure": 200000,
      "max_daily_loss": 0.05
    }
  }
}
```

### 4.3 Circuit Breaker

#### Trigger Circuit Breaker
```http
POST /v1/risk/circuit-breaker/trigger
Content-Type: application/json

{
  "reason": "daily_loss_limit_exceeded",
  "agent_id": "uuid",
  "details": {
    "current_loss": 0.06,
    "limit": 0.05,
    "trigger_time": "2025-01-01T00:00:00Z"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "circuit_breaker_id": "uuid",
    "status": "activated",
    "affected_agents": ["uuid1", "uuid2"],
    "estimated_recovery_time": "2025-01-01T01:00:00Z"
  }
}
```

## 5. Execution Engine Service API

### 5.1 Order Management

#### Submit Order
```http
POST /v1/execution/orders
Content-Type: application/json

{
  "agent_id": "uuid",
  "order": {
    "symbol": "BTC-USD",
    "side": "buy",
    "type": "market",
    "quantity": 0.1,
    "price": null,
    "time_in_force": "IOC"
  },
  "routing_preferences": {
    "preferred_exchange": "coinbase",
    "max_latency_ms": 1000,
    "min_liquidity": 1000000
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "order_id": "uuid",
    "status": "submitted",
    "exchange": "coinbase",
    "submitted_at": "2025-01-01T00:00:00Z",
    "estimated_execution_time": "2025-01-01T00:00:01Z"
  }
}
```

#### Get Order Status
```http
GET /v1/execution/orders/{order_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "order_id": "uuid",
    "status": "executed",
    "execution_details": {
      "executed_quantity": 0.1,
      "executed_price": 50050,
      "fees": 25.025,
      "execution_time": "2025-01-01T00:00:00.750Z"
    },
    "routing_info": {
      "exchange": "coinbase",
      "latency_ms": 750,
      "slippage": 0.001
    }
  }
}
```

### 5.2 Performance Metrics

#### Get Execution Metrics
```http
GET /v1/execution/metrics?agent_id={agent_id}&timeframe=1h
```

**Response:**
```json
{
  "success": true,
  "data": {
    "timeframe": "1h",
    "metrics": {
      "total_orders": 45,
      "successful_executions": 43,
      "success_rate": 0.956,
      "average_latency_ms": 850,
      "p95_latency_ms": 1200,
      "total_volume": 15.5,
      "average_slippage": 0.0015
    },
    "exchange_breakdown": [
      {
        "exchange": "coinbase",
        "orders": 30,
        "success_rate": 0.967,
        "avg_latency_ms": 800
      }
    ]
  }
}
```

## 6. Data Ingestion Service API

### 6.1 Market Data

#### Get Real-time Market Data
```http
GET /v1/data/market/{symbol}/realtime
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC-USD",
    "price": 50000,
    "bid": 49995,
    "ask": 50005,
    "volume_24h": 1500000000,
    "change_24h": 0.025,
    "timestamp": "2025-01-01T00:00:00Z",
    "sources": [
      {
        "exchange": "coinbase",
        "price": 50000,
        "volume": 500000000,
        "last_update": "2025-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### Subscribe to Market Data Stream
```http
POST /v1/data/market/subscribe
Content-Type: application/json

{
  "symbols": ["BTC-USD", "ETH-USD"],
  "data_types": ["price", "volume", "orderbook"],
  "callback_url": "https://agent.example.com/webhook/market-data"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subscription_id": "uuid",
    "websocket_url": "wss://api.grekko.trading/v1/data/stream",
    "auth_token": "jwt_token",
    "expires_at": "2025-01-01T01:00:00Z"
  }
}
```

### 6.2 Historical Data

#### Get Historical Market Data
```http
GET /v1/data/market/{symbol}/history?start=2025-01-01T00:00:00Z&end=2025-01-01T23:59:59Z&interval=1m
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC-USD",
    "interval": "1m",
    "data_points": [
      {
        "timestamp": "2025-01-01T00:00:00Z",
        "open": 49900,
        "high": 50100,
        "low": 49850,
        "close": 50000,
        "volume": 1500000
      }
    ],
    "metadata": {
      "total_points": 1440,
      "data_quality": 0.995,
      "sources": ["coinbase", "binance"]
    }
  }
}
```

## 7. Strategy Engine Service API

### 7.1 Strategy Management

#### Execute Strategy
```http
POST /v1/strategy/execute
Content-Type: application/json

{
  "agent_id": "uuid",
  "strategy_type": "momentum",
  "parameters": {
    "lookback_period": 20,
    "threshold": 0.02,
    "position_size": 0.1
  },
  "market_context": {
    "symbol": "BTC-USD",
    "current_price": 50000,
    "trend": "bullish"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "strategy_execution_id": "uuid",
    "decision": {
      "action": "buy",
      "confidence": 0.85,
      "recommended_quantity": 0.1,
      "target_price": 50000,
      "stop_loss": 47500,
      "take_profit": 52500
    },
    "analysis": {
      "signals": [
        {
          "type": "momentum",
          "strength": 0.8,
          "direction": "bullish"
        }
      ],
      "risk_factors": [
        {
          "type": "volatility",
          "level": "medium",
          "impact": 0.3
        }
      ]
    }
  }
}
```

### 7.2 Mode Management

#### Update Agent Mode
```http
PUT /v1/strategy/agents/{agent_id}/mode
Content-Type: application/json

{
  "mode": "conservative",
  "reason": "market_volatility_increased",
  "effective_immediately": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "uuid",
    "previous_mode": "aggressive",
    "new_mode": "conservative",
    "changed_at": "2025-01-01T00:00:00Z",
    "affected_strategies": [
      "momentum",
      "mean_reversion"
    ]
  }
}
```

## 8. MCP Integration Service API

### 8.1 Tool Management

#### Execute MCP Tool
```http
POST /v1/mcp/tools/execute
Content-Type: application/json

{
  "tool_name": "playwright",
  "action": "navigate_and_extract",
  "parameters": {
    "url": "https://coinmarketcap.com/currencies/bitcoin/",
    "selectors": {
      "price": ".priceValue",
      "change": ".sc-15yy2pl-0"
    },
    "timeout_ms": 5000
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "uuid",
    "status": "completed",
    "results": {
      "price": "$50,000.00",
      "change": "+2.5%"
    },
    "execution_time_ms": 3500,
    "screenshots": [
      {
        "timestamp": "2025-01-01T00:00:00Z",
        "url": "https://storage.example.com/screenshots/uuid.png"
      }
    ]
  }
}
```

### 8.2 Browser Session Management

#### Create Browser Session
```http
POST /v1/mcp/sessions
Content-Type: application/json

{
  "browser_type": "chromium",
  "headless": true,
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "user_agent": "custom_trading_bot/1.0"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "status": "active",
    "created_at": "2025-01-01T00:00:00Z",
    "expires_at": "2025-01-01T01:00:00Z",
    "capabilities": [
      "navigation",
      "form_interaction",
      "screenshot",
      "pdf_generation"
    ]
  }
}
```

## 9. Wallet Management Service API

### 9.1 Wallet Operations

#### Connect Wallet
```http
POST /v1/wallet/connect
Content-Type: application/json

{
  "wallet_type": "metamask",
  "connection_method": "browser_extension",
  "network": "ethereum_mainnet"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "wallet_id": "uuid",
    "address": "0x742d35Cc6634C0532925a3b8D4C9db96590b5b8c",
    "network": "ethereum_mainnet",
    "connection_status": "connected",
    "balance": {
      "ETH": "2.5",
      "USDC": "10000.0"
    }
  }
}
```

#### Sign Transaction
```http
POST /v1/wallet/{wallet_id}/sign
Content-Type: application/json

{
  "transaction": {
    "to": "0x742d35Cc6634C0532925a3b8D4C9db96590b5b8c",
    "value": "1000000000000000000",
    "gas": "21000",
    "gasPrice": "20000000000",
    "data": "0x"
  },
  "confirmation_required": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transaction_id": "uuid",
    "status": "pending_signature",
    "signed_transaction": null,
    "confirmation_url": "https://app.example.com/confirm/uuid"
  }
}
```

## 10. Monitoring Service API

### 10.1 Health Checks

#### Get Service Health
```http
GET /v1/monitoring/health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "services": [
      {
        "name": "agent-coordination",
        "status": "healthy",
        "response_time_ms": 45,
        "last_check": "2025-01-01T00:00:00Z"
      },
      {
        "name": "risk-management",
        "status": "degraded",
        "response_time_ms": 1200,
        "last_check": "2025-01-01T00:00:00Z",
        "issues": ["high_latency"]
      }
    ],
    "dependencies": [
      {
        "name": "postgresql",
        "status": "healthy",
        "connection_pool": {
          "active": 5,
          "idle": 15,
          "max": 20
        }
      }
    ]
  }
}
```

### 10.2 Metrics

#### Get System Metrics
```http
GET /v1/monitoring/metrics?service=execution-engine&timeframe=1h
```

**Response:**
```json
{
  "success": true,
  "data": {
    "service": "execution-engine",
    "timeframe": "1h",
    "metrics": [
      {
        "name": "request_rate",
        "value": 150.5,
        "unit": "requests/minute",
        "trend": "increasing"
      },
      {
        "name": "error_rate",
        "value": 0.002,
        "unit": "percentage",
        "trend": "stable"
      },
      {
        "name": "response_time_p95",
        "value": 850,
        "unit": "milliseconds",
        "trend": "decreasing"
      }
    ]
  }
}
```

## 11. WebSocket API Specifications

### 11.1 Real-time Market Data Stream

**Connection:**
```
wss://api.grekko.trading/v1/data/stream
```

**Authentication:**
```json
{
  "type": "auth",
  "token": "jwt_token"
}
```

**Subscribe to Symbol:**
```json
{
  "type": "subscribe",
  "channel": "market_data",
  "symbols": ["BTC-USD", "ETH-USD"],
  "data_types": ["price", "volume"]
}
```

**Market Data Message:**
```json
{
  "type": "market_data",
  "symbol": "BTC-USD",
  "data": {
    "price": 50000,
    "volume": 1500000,
    "timestamp": "2025-01-01T00:00:00Z"
  }
}
```

### 11.2 Agent Coordination Stream

**Subscribe to Coordination Events:**
```json
{
  "type": "subscribe",
  "channel": "coordination",
  "agent_id": "uuid"
}
```

**Proposal Notification:**
```json
{
  "type": "proposal",
  "proposal_id": "uuid",
  "from_agent": "uuid",
  "proposal": {
    "symbol": "BTC-USD",
    "action": "buy",
    "quantity": 0.1,
    "rationale": "Technical analysis indicates bullish trend"
  },
  "timeout_ms": 500
}
```

**Response Message:**
```json
{
  "type": "proposal_response",
  "proposal_id": "uuid",
  "response": "agree",
  "rationale": "Aligns with risk parameters"
}
```

## 12. Rate Limiting

### 12.1 Rate Limit Headers
All API responses include rate limiting headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### 12.2 Rate Limits by Service

| Service | Endpoint Type | Limit | Window |
|---------|---------------|-------|--------|
| **Agent Coordination** | Proposal submission | 100/hour | 1 hour |
| **Risk Management** | Risk assessment | 1000/hour | 1 hour |
| **Execution Engine** | Order submission | 500/hour | 1 hour |
| **Data Ingestion** | Market data requests | 10000/hour | 1 hour |
| **Strategy Engine** | Strategy execution | 200/hour | 1 hour |
| **MCP Integration** | Tool execution | 50/hour | 1 hour |
| **Wallet Management** | Transaction signing | 100/hour | 1 hour |
| **Monitoring** | Health checks | Unlimited | - |

## 13. Error Codes Reference

### 13.1 Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `AUTHENTICATION_REQUIRED` | Valid authentication required | 401 |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions | 403 |
| `RESOURCE_NOT_FOUND` | Requested resource not found | 404 |
| `RESOURCE_CONFLICT` | Resource state conflict | 409 |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded | 429 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

### 13.2 Service-Specific Error Codes

#### Agent Coordination Service
- `AGENT_NOT_REGISTERED`: Agent not found in registry
- `CONSENSUS_TIMEOUT`: Consensus not reached within timeout
- `INVALID_PROPOSAL`: Proposal format or content invalid

#### Risk Management Service
- `RISK_THRESHOLD_EXCEEDED`: Operation exceeds risk limits
- `CIRCUIT_BREAKER_ACTIVE`: Trading halted by circuit breaker
- `INSUFFICIENT_BALANCE`: Insufficient funds for operation

#### Execution Engine Service
- `EXCHANGE_UNAVAILABLE`: Target exchange not available
- `ORDER_REJECTED`: Order rejected by exchange
- `EXECUTION_TIMEOUT`: Order execution timed out

---

*This API specification provides the foundation for all service integrations and should be kept synchronized with actual implementations.*