# Grekko - Enterprise Cryptocurrency Trading System

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Kubernetes](https://img.shields.io/badge/platform-Kubernetes-326ce5.svg)](https://kubernetes.io/)
[![Production Ready](https://img.shields.io/badge/status-Production%20Ready-green.svg)](docs/production_deployment_guide.md)

---

**Grekko** is a sophisticated, production-ready cryptocurrency trading system built on microservices architecture with enterprise-grade security, monitoring, and scalability. Designed for institutional trading operations with sub-second execution latency and comprehensive risk management.

## 🏗️ System Architecture

### Microservices Architecture
Grekko implements an event-driven microservices pattern with CQRS and Event Sourcing, optimized for high-frequency trading and multi-agent coordination.

```
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  Authentication │ Rate Limiting │ Request Routing │ Load Balancing│
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Services Layer                          │
├─────────────────────────────────────────────────────────────────┤
│ Agent Coordination │ Risk Management │ Execution Engine          │
│ Data Ingestion     │ Strategy Engine │ MCP Integration           │
│ Wallet Management  │ Monitoring      │                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                          │
├─────────────────────────────────────────────────────────────────┤
│ Message Bus (Kafka) │ Databases │ Caching │ Secret Management   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Service | Responsibility | SLA | Scaling Strategy |
|---------|---------------|-----|------------------|
| **Agent Coordination** | Multi-agent consensus, communication channel | 500ms consensus | Horizontal (stateless) |
| **Risk Management** | Circuit breakers, exposure limits, safety controls | 100ms evaluation | Vertical (CPU-intensive) |
| **Execution Engine** | Trade routing, order management, latency optimization | 1s execution | Horizontal (high throughput) |
| **Data Ingestion** | Market data aggregation, real-time streaming | 50ms data freshness | Horizontal (data volume) |
| **Coinbase Integration** | CEX trading and market data | 200ms API response | Horizontal (API calls) |
| **MetaMask Integration** | Web3 wallet automation, transaction signing | 3s transaction | Vertical (security) |
| **MCP Integration** | Browser automation, tool orchestration | 2s automation | Horizontal (parallel tasks) |
| **Monitoring** | Metrics collection, alerting, observability | 1s alert latency | Horizontal (data volume) |

## 🚀 Production-Ready Features

### ✅ **Deployed Infrastructure**
- **Kubernetes Orchestration**: Production cluster with 9 nodes (3 masters, 6 workers)
- **Service Mesh**: Istio for traffic management and mTLS security
- **Message Bus**: Apache Kafka cluster for event streaming
- **Databases**: PostgreSQL, Redis, and InfluxDB clusters
- **Monitoring Stack**: Prometheus + Grafana + AlertManager
- **CI/CD Pipeline**: GitHub Actions with ArgoCD deployment

### ✅ **Trading Capabilities**
- **Multi-Exchange Support**: Coinbase Pro, Binance integration
- **DEX Integration**: Uniswap, SushiSwap execution engines
- **Real-Time Market Data**: Sub-50ms data freshness
- **Order Execution**: <1s end-to-end execution latency
- **Risk Management**: Real-time circuit breakers and exposure monitoring

### ✅ **Web3 Integration**
- **MetaMask Automation**: Browser-based wallet interaction
- **Transaction Management**: Secure signing and validation
- **Network Support**: Ethereum mainnet with multi-chain capability
- **Security Manager**: Comprehensive transaction validation

### ✅ **Enterprise Security**
- **Zero-Trust Architecture**: mTLS for all inter-service communication
- **Secret Management**: Kubernetes secrets with rotation policies
- **Network Policies**: Default deny-all with explicit allow rules
- **Container Security**: Non-root containers with security contexts

## 📊 Performance Metrics

### Production SLAs
- **Order Execution**: <1s end-to-end (95th percentile)
- **Risk Assessment**: <100ms evaluation time
- **Market Data**: <50ms freshness guarantee
- **System Availability**: 99.9% uptime target
- **Agent Consensus**: <500ms decision time

### Scalability
- **Throughput**: 1000+ orders per second capacity
- **Concurrent Users**: 10K+ supported
- **Auto-scaling**: HPA based on CPU/memory utilization
- **Resource Efficiency**: <5% cost increase per 100% capacity growth

## 🛠️ Technology Stack

### Backend Services
- **Language**: Python 3.9+ with FastAPI
- **Message Bus**: Apache Kafka with Redis Streams
- **Databases**: PostgreSQL (transactional), Redis (cache), InfluxDB (metrics)
- **Authentication**: JWT Bearer tokens with RBAC

### Frontend Dashboard
- **Framework**: React 18+ with TypeScript
- **State Management**: Redux Toolkit with RTK Query
- **Real-Time**: WebSocket connections for live data
- **UI Components**: Material-UI with custom trading components

### Infrastructure
- **Orchestration**: Kubernetes 1.28+ with Istio service mesh
- **Monitoring**: Prometheus, Grafana, Jaeger distributed tracing
- **Storage**: Persistent volumes with automated backups
- **Networking**: Load balancers with SSL termination

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (v1.28+) with 9 nodes minimum
- `kubectl`, `docker`, `helm` installed
- Container registry access
- Cloud storage for backups

### 1. Environment Setup
```bash
git clone https://github.com/your-org/grekko.git
cd grekko
chmod +x scripts/*.sh
```

### 2. Configure Secrets
```bash
# Database credentials
kubectl create secret generic postgresql-credentials \
  --from-literal=password=<POSTGRES_PASSWORD> \
  -n trading-prod

# Trading API credentials
kubectl create secret generic trading-secrets \
  --from-literal=coinbase_api_key=<COINBASE_API_KEY> \
  --from-literal=coinbase_api_secret=<COINBASE_API_SECRET> \
  --from-literal=database_url=<DATABASE_URL> \
  --from-literal=redis_url=<REDIS_URL> \
  --from-literal=kafka_brokers=<KAFKA_BROKERS> \
  -n trading-prod
```

### 3. Deploy Infrastructure
```bash
# Deploy cluster configuration
kubectl apply -f k8s/cluster/cluster-config.yaml

# Deploy service mesh
kubectl apply -f k8s/service-mesh/istio-config.yaml

# Deploy databases and message bus
kubectl apply -f k8s/databases/
kubectl apply -f k8s/message-bus/kafka-cluster.yaml

# Deploy monitoring stack
kubectl apply -f k8s/monitoring/
```

### 4. Deploy Application Services
```bash
# Execute production deployment
./scripts/deploy-production.sh

# Monitor deployment progress
kubectl get pods -n trading-prod -w
```

### 5. Verify Deployment
```bash
# Health checks
kubectl exec -n trading-prod deployment/coinbase-integration-active -- curl -f http://localhost:8080/health
kubectl exec -n trading-prod deployment/metamask-integration-active -- curl -f http://localhost:8080/health
kubectl exec -n trading-prod deployment/risk-management-active -- curl -f http://localhost:8080/health

# Access monitoring dashboards
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

## 📡 API Reference

### Core Endpoints

#### Agent Coordination
```http
POST /v1/coordination/agents/register
GET  /v1/coordination/agents/{agent_id}
POST /v1/coordination/proposals
GET  /v1/coordination/proposals/{proposal_id}
```

#### Risk Management
```http
POST /v1/risk/assess
GET  /v1/risk/exposure/{agent_id}
POST /v1/risk/circuit-breaker/trigger
```

#### Execution Engine
```http
POST /v1/execution/orders
GET  /v1/execution/orders/{order_id}
GET  /v1/execution/metrics
```

#### Market Data
```http
GET  /v1/data/market/{symbol}/realtime
POST /v1/data/market/subscribe
GET  /v1/data/market/{symbol}/history
```

### WebSocket Streams
- **Market Data**: `wss://api.grekko.trading/v1/data/stream`
- **Agent Coordination**: Real-time proposal notifications
- **Risk Alerts**: Circuit breaker and threshold notifications

### Authentication
All APIs use JWT Bearer tokens:
```http
Authorization: Bearer <jwt_token>
```

## 🔒 Security Features

### Network Security
- **Service Mesh**: Istio with mTLS for all inter-service communication
- **Network Policies**: Default deny-all with explicit allow rules
- **TLS Termination**: Valid certificates with automatic renewal
- **Firewall Rules**: Restricted access to management interfaces

### Data Protection
- **Encryption**: AES-256 for data at rest, TLS 1.3 for data in transit
- **Secret Management**: Kubernetes secrets with automated rotation
- **Access Control**: RBAC with least-privilege principles
- **Audit Logging**: Comprehensive audit trail for all operations

### Container Security
- **Image Scanning**: Trivy security scans in CI/CD pipeline
- **Runtime Security**: Non-root containers with read-only filesystems
- **Resource Limits**: CPU and memory limits enforced
- **Security Contexts**: Restricted security contexts applied

## 📈 Monitoring and Observability

### Metrics (Prometheus)
- **Business Metrics**: Trading volume, success rates, P&L tracking
- **Technical Metrics**: Response times, error rates, resource utilization
- **Infrastructure Metrics**: CPU, memory, disk, network throughput

### Dashboards (Grafana)
- **Trading System Overview**: High-level system metrics
- **MetaMask Integration**: Web3 transaction monitoring
- **Risk Management**: Risk exposure and compliance
- **Infrastructure**: Kubernetes cluster health

### Alerting
- **Critical**: Service downtime, security breaches (PagerDuty)
- **Warning**: Performance degradation, approaching limits (Email)
- **Info**: Configuration changes, maintenance (Slack)

## 🔄 Backup and Disaster Recovery

### Automated Backups
- **PostgreSQL**: Continuous WAL archiving + daily full backups
- **Redis**: RDB snapshots every hour + AOF persistence
- **InfluxDB**: Incremental backups every 4 hours
- **Retention**: 30 days daily, 12 weeks weekly, 12 months monthly

### High Availability
- **Service Redundancy**: Minimum 3 replicas for critical services
- **Multi-Zone Deployment**: Fault tolerance across availability zones
- **Auto-Failover**: Automatic failover for database clusters
- **Circuit Breakers**: Graceful degradation under load

### Recovery Targets
- **Critical Services**: RTO 15 minutes, RPO 1 minute
- **Non-Critical Services**: RTO 1 hour, RPO 15 minutes
- **Data Recovery**: RTO 30 minutes, RPO 5 minutes

## 📚 Documentation

### System Documentation
- [**System Architecture**](docs/system_architecture.md) - Comprehensive architecture overview
- [**API Specifications**](docs/api_specifications.md) - Complete API documentation
- [**Production Deployment Guide**](docs/production_deployment_guide.md) - Deployment procedures
- [**Monitoring Strategy**](docs/monitoring_strategy.md) - Observability and alerting

### Component Documentation
- [**MetaMask Integration**](docs/metamask_integration_guide.md) - Web3 wallet automation
- [**Risk Management**](docs/4_pseudocode_risk_management.md) - Risk assessment and controls
- [**Agent Coordination**](docs/7_pseudocode_multi_agent_coordination.md) - Multi-agent consensus
- [**AI Ensemble System**](docs/5_pseudocode_ai_ensemble_system.md) - AI decision making

### Operations Documentation
- [**Kubectl Configuration**](docs/kubectl_configuration_guide.md) - Cluster access setup
- [**Troubleshooting Guide**](docs/3_metamask_troubleshooting_guide.md) - Common issues and solutions
- [**Security Documentation**](docs/metamask_security_documentation.md) - Security policies and procedures

## 🤝 Contributing

Grekko follows enterprise development practices with comprehensive testing and security reviews.

### Development Workflow
1. **Feature Branches**: All development in feature branches
2. **Code Review**: Mandatory peer review for all changes
3. **Testing**: 90%+ test coverage requirement
4. **Security Scan**: Automated security scanning in CI/CD
5. **Deployment**: Blue-green deployment with automatic rollback

### Testing Requirements
- **Unit Tests**: 90%+ coverage for all services
- **Integration Tests**: End-to-end workflow validation
- **Security Tests**: Penetration testing and vulnerability scanning
- **Performance Tests**: Load testing for 10K+ concurrent users

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

## 🏢 Enterprise Support

For enterprise deployments, custom integrations, or support:
- **Technical Support**: support@grekko.trading
- **Security Issues**: security@grekko.trading
- **Business Inquiries**: business@grekko.trading

---

**Grekko** - *Enterprise-Grade Cryptocurrency Trading Infrastructure*  
**Built for scale. Designed for security. Optimized for performance.** 🚀
