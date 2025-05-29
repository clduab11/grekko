# Metamask Integration Service Guide

This document provides comprehensive integration guidance for the Metamask Integration Service, covering service patterns, event flows, database integration, and real-time communication setup within the Grekko ecosystem.

## Table of Contents

- [Service Architecture](#service-architecture)
- [Service Integration Patterns](#service-integration-patterns)
- [Kafka Message Flows](#kafka-message-flows)
- [Database Integration](#database-integration)
- [WebSocket Real-time Communication](#websocket-real-time-communication)
- [Component Relationships](#component-relationships)
- [Integration Examples](#integration-examples)
- [Configuration Guidelines](#configuration-guidelines)

---

## Service Architecture

### Core Components

The Metamask Integration Service consists of several interconnected components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI REST  │    │ Browser Control │    │ Security Mgmt   │
│   API Layer     │    │ (Playwright)    │    │ & Validation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Kafka Producer  │    │ WebSocket Hub   │    │ Database Layer  │
│ Event Streams   │    │ Real-time Comm  │    │ State Storage   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Service Dependencies

| Component | Dependencies | Purpose |
|-----------|-------------|---------|
| [`api.py`](../src/services/metamask_integration/api.py) | FastAPI, SecurityManager, BrowserController | REST API endpoints |
| [`security_manager.py`](../src/services/metamask_integration/security_manager.py) | Redis, JWT | Security validation and session management |
| [`browser_controller.py`](../src/services/metamask_integration/browser_controller.py) | Playwright, SecurityManager | Browser automation |
| [`kafka_integration.py`](../src/services/metamask_integration/kafka_integration.py) | Kafka | Event streaming |
| [`websocket_handler.py`](../src/services/metamask_integration/websocket_handler.py) | WebSockets | Real-time communication |

---

## Service Integration Patterns

### 1. Agent Coordination Integration

The Metamask service integrates with the Agent Coordination service for orchestrated trading operations.

#### Message Flow Pattern
```python
# Agent Coordination → Metamask Integration
{
  "event_type": "transaction_request",
  "agent_id": "trading_agent_001",
  "session_token": "session-uuid",
  "transaction": {
    "to": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
    "value": 1000000000000000000,
    "gas": 21000,
    "gasPrice": 20000000000
  },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

#### Integration Implementation
```python
from src.services.agent_coordination.coordinator import Coordinator
from src.services.metamask_integration.api import app

# Register with agent coordination
coordinator = Coordinator()
coordinator.register_service("metamask_integration", {
    "capabilities": ["wallet_management", "transaction_signing"],
    "endpoints": ["/api/v1/wallet/connect", "/api/v1/transaction/sign"]
})
```

### 2. Risk Management Integration

Metamask service coordinates with Risk Management for transaction validation.

#### Pre-transaction Risk Check
```python
# Risk Management validation before Metamask signing
risk_assessment = {
    "transaction_value": 1000000000000000000,
    "destination_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
    "gas_price": 20000000000,
    "user_id": "user123"
}

# Send to Risk Management service
risk_response = await risk_service.validate_transaction(risk_assessment)
if risk_response["approved"]:
    # Proceed with Metamask signing
    pass
```

### 3. Coinbase Integration Cross-Service Pattern

Coordination between Metamask and Coinbase services for portfolio management.

#### Portfolio Synchronization
```python
# Metamask balance update → Coinbase portfolio sync
metamask_balance_event = {
    "event_type": "balance_update",
    "wallet_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
    "token": "ETH",
    "balance": "5.23847592",
    "timestamp": "2025-01-01T00:00:00Z"
}

# Published to portfolio-events topic
# Consumed by Coinbase service for portfolio reconciliation
```

---

## Kafka Message Flows

### Event Topics and Schemas

The Metamask Integration service produces and consumes events across multiple Kafka topics:

#### 1. Wallet Events Topic: `wallet-events`

**Producer:** Metamask Integration Service  
**Consumers:** Agent Coordination, Portfolio Management

```json
{
  "event_type": "wallet_connected|wallet_disconnected|address_changed",
  "wallet_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
  "user_id": "user123",
  "session_token": "session-uuid",
  "timestamp": "2025-01-01T00:00:00Z",
  "metadata": {
    "network": "mainnet",
    "chain_id": 1
  }
}
```

#### 2. Transaction Events Topic: `transaction-events`

**Producer:** Metamask Integration Service  
**Consumers:** Risk Management, Agent Coordination, Audit Service

```json
{
  "event_type": "transaction_prepared|transaction_signed|transaction_submitted|transaction_confirmed",
  "transaction_hash": "0xabc123...",
  "wallet_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
  "transaction": {
    "to": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
    "value": "1000000000000000000",
    "gas": 21000,
    "gasPrice": "20000000000",
    "nonce": 42
  },
  "user_id": "user123",
  "timestamp": "2025-01-01T00:00:00Z",
  "status": "success|failed|pending"
}
```

#### 3. Portfolio Events Topic: `portfolio-events`

**Producer:** Metamask Integration Service  
**Consumers:** Coinbase Integration, Portfolio Manager

```json
{
  "event_type": "balance_update|token_transfer",
  "wallet_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
  "token": {
    "symbol": "ETH",
    "contract_address": null,
    "decimals": 18
  },
  "balance": "5.23847592",
  "change": "+0.15000000",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

#### 4. Error Events Topic: `error-events`

**Producer:** Metamask Integration Service  
**Consumers:** Monitoring, Alert System

```json
{
  "event_type": "security_violation|transaction_failed|browser_error",
  "severity": "low|medium|high|critical",
  "error_code": "MM_SEC_001",
  "message": "Rate limit exceeded for user",
  "user_id": "user123",
  "context": {
    "endpoint": "/api/v1/wallet/connect",
    "ip_address": "192.168.1.100"
  },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

#### 5. Network Events Topic: `network-events`

**Producer:** Metamask Integration Service  
**Consumers:** Agent Coordination, Market Data Service

```json
{
  "event_type": "network_switched|network_connected|network_error",
  "wallet_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
  "network": {
    "name": "mainnet",
    "chain_id": 1,
    "rpc_url": "https://mainnet.infura.io/v3/..."
  },
  "previous_network": "goerli",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### Message Production Patterns

#### Asynchronous Event Publishing
```python
from kafka import KafkaProducer
import json

class MetamaskEventProducer:
    def __init__(self, bootstrap_servers):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
    
    async def publish_wallet_event(self, event_data):
        await self.producer.send(
            'wallet-events',
            key=event_data['wallet_address'],
            value=event_data
        )
    
    async def publish_transaction_event(self, event_data):
        await self.producer.send(
            'transaction-events',
            key=event_data['wallet_address'],
            value=event_data
        )
```

---

## Database Integration

### Data Models and Schemas

#### 1. Session Management
```sql
-- Session storage table
CREATE TABLE metamask_sessions (
    session_token VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    wallet_address VARCHAR(42),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);
```

#### 2. Wallet State Tracking
```sql
-- Wallet state persistence
CREATE TABLE wallet_states (
    wallet_address VARCHAR(42) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    network_id INT NOT NULL,
    balance_eth DECIMAL(36,18),
    nonce INT DEFAULT 0,
    last_transaction_hash VARCHAR(66),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);
```

#### 3. Transaction History
```sql
-- Transaction tracking and audit trail
CREATE TABLE transaction_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_hash VARCHAR(66) UNIQUE,
    wallet_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    value DECIMAL(36,18) NOT NULL,
    gas_limit INT NOT NULL,
    gas_price DECIMAL(36,18) NOT NULL,
    nonce INT NOT NULL,
    status ENUM('pending', 'confirmed', 'failed') DEFAULT 'pending',
    block_number BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP NULL,
    INDEX idx_wallet_address (wallet_address),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### Database Access Patterns

#### Connection Management
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

class DatabaseManager:
    def __init__(self, database_url):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self):
        return self.SessionLocal()
```

#### Session Management Integration
```python
class SessionStore:
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def create_session(self, user_id, wallet_address=None):
        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        with self.db.get_session() as db:
            session_record = SessionRecord(
                session_token=session_token,
                user_id=user_id,
                wallet_address=wallet_address,
                expires_at=expires_at
            )
            db.add(session_record)
            db.commit()
        
        return session_token
```

---

## WebSocket Real-time Communication

### WebSocket Architecture

#### Connection Management
```python
from fastapi import WebSocket
from typing import Dict, Set
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(json.dumps(message))
```

### Real-time Event Broadcasting

#### Transaction Status Updates
```python
# Real-time transaction status updates
@app.websocket("/ws/transactions/{user_id}")
async def websocket_transactions(websocket: WebSocket, user_id: str):
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Listen for transaction events from Kafka
            message = await kafka_consumer.receive()
            if message['user_id'] == user_id:
                await websocket_manager.send_to_user(user_id, {
                    "type": "transaction_update",
                    "data": message
                })
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, user_id)
```

#### Wallet State Synchronization
```python
# Real-time wallet state updates
async def broadcast_wallet_update(wallet_address: str, user_id: str):
    wallet_state = await get_wallet_state(wallet_address)
    message = {
        "type": "wallet_state_update",
        "wallet_address": wallet_address,
        "balance": wallet_state.balance_eth,
        "network": wallet_state.network_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    await websocket_manager.send_to_user(user_id, message)
```

---

## Component Relationships

### Service Communication Flow

```
1. Frontend Request → REST API
2. REST API → Security Manager (validation)
3. Security Manager → Browser Controller (if valid)
4. Browser Controller → Metamask Extension
5. Browser Controller → Database (state update)
6. Browser Controller → Kafka Producer (event publishing)
7. Kafka → Other Services (Agent Coordination, Risk Management)
8. WebSocket Manager → Frontend (real-time updates)
```

### Error Handling and Recovery

#### Circuit Breaker Pattern
```python
from circuit_breaker import CircuitBreaker

class MetamaskServiceIntegration:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=Exception
        )
    
    @circuit_breaker
    async def call_external_service(self, service_endpoint, payload):
        # Service call with automatic circuit breaking
        pass
```

---

## Integration Examples

### Complete Transaction Flow

```python
# 1. Agent requests transaction
async def process_agent_transaction_request(agent_request):
    # 2. Validate with Risk Management
    risk_check = await risk_service.validate_transaction(
        agent_request['transaction']
    )
    
    if not risk_check['approved']:
        await publish_error_event({
            "event_type": "transaction_rejected",
            "reason": risk_check['reason']
        })
        return
    
    # 3. Prepare transaction in Metamask
    transaction_response = await metamask_api.prepare_transaction(
        agent_request
    )
    
    # 4. Publish transaction event
    await kafka_producer.publish_transaction_event({
        "event_type": "transaction_prepared",
        "transaction": transaction_response
    })
    
    # 5. Sign transaction
    signed_transaction = await metamask_api.sign_transaction(
        transaction_response
    )
    
    # 6. Broadcast real-time update
    await websocket_manager.send_to_user(
        agent_request['user_id'],
        {"type": "transaction_signed", "data": signed_transaction}
    )
```

### Multi-Service Coordination

```python
# Cross-service portfolio synchronization
async def synchronize_portfolio_across_services():
    # 1. Get Metamask wallet balances
    metamask_balances = await metamask_service.get_wallet_balances()
    
    # 2. Get Coinbase portfolio
    coinbase_portfolio = await coinbase_service.get_portfolio()
    
    # 3. Calculate discrepancies
    discrepancies = calculate_portfolio_diff(
        metamask_balances, 
        coinbase_portfolio
    )
    
    # 4. Publish portfolio sync events
    for discrepancy in discrepancies:
        await kafka_producer.publish_portfolio_event({
            "event_type": "portfolio_discrepancy",
            "data": discrepancy
        })
```

---

## Configuration Guidelines

### Environment Configuration

```yaml
# metamask-integration-config.yaml
metamask_integration:
  api:
    host: "0.0.0.0"
    port: 8000
    cors_origins: ["https://app.grekko.com"]
  
  security:
    jwt_secret: "${JWT_SECRET}"
    session_timeout: 3600
    rate_limit: "10/minute"
  
  browser:
    metamask_extension_path: "/opt/metamask"
    headless: false
    user_data_dir: "/tmp/metamask_sessions"
  
  kafka:
    bootstrap_servers: ["kafka-1:9092", "kafka-2:9092"]
    topics:
      - "wallet-events"
      - "transaction-events"
      - "portfolio-events"
      - "error-events"
      - "network-events"
  
  database:
    url: "${DATABASE_URL}"
    pool_size: 10
    max_overflow: 20
  
  redis:
    url: "${REDIS_URL}"
    session_db: 0
    rate_limit_db: 1
```

### Service Discovery Integration

```python
# Service registration with discovery
from consul import Consul

class ServiceRegistry:
    def __init__(self):
        self.consul = Consul()
    
    def register_service(self):
        self.consul.agent.service.register(
            name="metamask-integration",
            service_id="metamask-integration-1",
            address="10.0.1.100",
            port=8000,
            check=Consul.Check.http("http://10.0.1.100:8000/health", 
                                   interval="10s")
        )
```

---

*This integration guide provides the foundation for integrating the Metamask Integration Service with the broader Grekko ecosystem. For specific API details, see [Metamask API Reference](metamask_api_reference.md). For deployment instructions, see the deployment documentation.*