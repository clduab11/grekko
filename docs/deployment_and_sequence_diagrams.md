# Deployment Architecture and Sequence Diagrams

## 1. Overview

This document provides detailed deployment architecture specifications and sequence diagrams for critical workflows in the autonomous cryptocurrency trading system. It complements the main system architecture document with operational and runtime perspectives.

## 2. Kubernetes Deployment Architecture

### 2.1 Cluster Layout
```
Production Cluster (6 Worker Nodes + 3 Masters)
├── Master Nodes (3) - Control Plane
│   ├── API Server, etcd, Scheduler
│   └── High Availability Configuration
├── Application Nodes (3)
│   ├── Agent Coordination Service
│   ├── Risk Management Service
│   ├── Execution Engine Service
│   ├── Data Ingestion Service
│   ├── Strategy Engine Service
│   └── MCP Integration Service
└── Data Nodes (3)
    ├── PostgreSQL Cluster
    ├── Redis Cluster
    ├── InfluxDB Cluster
    └── Monitoring Stack
```

### 2.2 Service Deployment Specifications

#### Agent Coordination Service
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-coordination
  namespace: trading-prod
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: agent-coordination
        image: grekko/agent-coordination:v1.0.0
        resources:
          requests: {memory: "256Mi", cpu: "250m"}
          limits: {memory: "512Mi", cpu: "500m"}
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef: {name: database-credentials, key: url}
```

#### Risk Management Service
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: risk-management
  namespace: trading-prod
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: risk-management
        image: grekko/risk-management:v1.0.0
        resources:
          requests: {memory: "512Mi", cpu: "500m"}
          limits: {memory: "1Gi", cpu: "1000m"}
```

### 2.3 Network Architecture

```
Internet → Load Balancer → API Gateway → Service Mesh → Services
                                      ↓
                                 Data Layer (PostgreSQL, Redis, InfluxDB)
```

**Security Layers:**
- TLS termination at load balancer
- mTLS between services via Istio
- Network policies for traffic isolation
- Encrypted storage and secrets management

## 3. Critical Workflow Sequence Diagrams

### 3.1 Trade Execution Workflow

```
Agent → Coordination → Risk Mgmt → Execution → Coinbase API
  │         │            │           │           │
  │ 1. Propose Trade     │           │           │
  ├────────▶│            │           │           │
  │         │ 2. Consensus (500ms)   │           │
  │         ├────────────┤           │           │
  │         │◀───────────┤           │           │
  │ 3. Consensus Result  │           │           │
  │◀────────┤            │           │           │
  │ 4. Risk Assessment   │           │           │
  ├─────────────────────▶│           │           │
  │         │            │ 5. Approved (100ms)  │
  │◀─────────────────────┤           │           │
  │ 6. Execute Order     │           │           │
  ├─────────────────────────────────▶│           │
  │         │            │           │ 7. Submit │
  │         │            │           ├──────────▶│
  │         │            │           │ 8. Confirm│
  │         │            │           │◀──────────┤
  │ 9. Execution Complete│           │           │
  │◀─────────────────────────────────┤           │
```

**Timing Requirements:**
- Consensus: ≤500ms
- Risk Assessment: ≤100ms
- Order Execution: ≤1000ms
- **Total: ≤1600ms**

### 3.2 Risk Circuit Breaker Activation

```
Risk Mgmt → Trading Agent → Agent Coord → Execution → Monitoring
    │           │              │            │           │
    │ 1. Threshold Breach      │            │           │
    │           │              │            │           │
    │ 2. Halt Trading          │            │           │
    ├──────────▶│              │            │           │
    │ 3. Notify Coordination   │            │           │
    ├─────────────────────────▶│            │           │
    │           │              │ 4. Emergency Stop     │
    │           │◀─────────────┤            │           │
    │ 5. Cancel Orders         │            │           │
    ├───────────────────────────────────────▶│           │
    │ 6. Alert Operations      │            │           │
    ├─────────────────────────────────────────────────▶│
```

**Timing Requirements:**
- Detection to Trigger: ≤50ms
- System Halt: ≤200ms
- Alerting: ≤1000ms

### 3.3 Multi-Agent Consensus Protocol

```
Agent A → Agent Coord → Agent B/C → Consensus Engine
   │          │           │             │
   │ 1. Proposal          │             │
   ├─────────▶│           │             │
   │          │ 2. Broadcast            │
   │          ├──────────▶│             │
   │          │           │ 3. Evaluate │
   │          │           │             │
   │          │ 4. Responses            │
   │          │◀──────────┤             │
   │          │ 5. Calculate Consensus  │
   │          ├────────────────────────▶│
   │          │           │             │ 6. Result
   │          │◀────────────────────────┤
   │ 7. Decision          │             │
   │◀─────────┤           │             │
```

**Timing Requirements:**
- Proposal Distribution: ≤200ms
- Agent Evaluation: ≤300ms
- Consensus Calculation: ≤100ms
- **Total: ≤600ms**

### 3.4 Market Data Streaming

```
Coinbase API → Data Ingestion → Message Bus → Agents → Strategy Engine
      │             │              │          │           │
      │ 1. Stream   │              │          │           │
      ├────────────▶│              │          │           │
      │             │ 2. Normalize │          │           │
      │             │              │          │           │
      │             │ 3. Publish   │          │           │
      │             ├─────────────▶│          │           │
      │             │              │ 4. Distribute       │
      │             │              ├─────────▶│           │
      │             │              ├──────────────────────▶│
      │             │              │          │ 5. Process│
      │             │              │          │           │
      │             │              │          │ 6. Signals│
      │             │              │          │◀──────────┤
```

**Timing Requirements:**
- Data Processing: ≤50ms
- Distribution: ≤20ms
- Signal Generation: ≤100ms
- **Total Freshness: ≤170ms**

## 4. Infrastructure as Code

### 4.1 Terraform Configuration

#### EKS Cluster
```hcl
resource "aws_eks_cluster" "trading_cluster" {
  name     = "grekko-trading-prod"
  role_arn = aws_iam_role.cluster_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.cluster_encryption.arn
    }
    resources = ["secrets"]
  }
}

resource "aws_eks_node_group" "trading_nodes" {
  cluster_name    = aws_eks_cluster.trading_cluster.name
  node_group_name = "trading-workers"
  node_role_arn   = aws_iam_role.node_role.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = ["m5.xlarge"]
  scaling_config {
    desired_size = 6
    max_size     = 12
    min_size     = 3
  }
}
```

#### RDS PostgreSQL
```hcl
resource "aws_db_instance" "trading_db" {
  identifier = "grekko-trading-prod"
  engine     = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"
  
  allocated_storage = 100
  storage_encrypted = true
  
  db_name  = "trading"
  username = "trading_admin"
  password = random_password.db_password.result
  
  backup_retention_period = 30
  skip_final_snapshot = false
}
```

#### Redis Cluster
```hcl
resource "aws_elasticache_replication_group" "trading_redis" {
  replication_group_id = "grekko-trading-redis"
  description = "Redis cluster for trading system"
  
  node_type = "cache.r6g.large"
  num_cache_clusters = 3
  
  automatic_failover_enabled = true
  multi_az_enabled = true
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}
```

### 4.2 Helm Chart Structure

```yaml
# Chart.yaml
apiVersion: v2
name: trading-services
description: Grekko Trading System Services
version: 1.0.0

dependencies:
- name: postgresql
  version: 12.1.9
  repository: https://charts.bitnami.com/bitnami
- name: redis
  version: 17.3.7
  repository: https://charts.bitnami.com/bitnami
- name: prometheus
  version: 15.18.0
  repository: https://prometheus-community.github.io/helm-charts
```

```yaml
# values.yaml
global:
  imageRegistry: "grekko.azurecr.io"
  imagePullSecrets: ["acr-secret"]

agentCoordination:
  replicaCount: 3
  image:
    repository: agent-coordination
    tag: "v1.0.0"
  resources:
    requests: {memory: "256Mi", cpu: "250m"}
    limits: {memory: "512Mi", cpu: "500m"}

riskManagement:
  replicaCount: 2
  image:
    repository: risk-management
    tag: "v1.0.0"
  resources:
    requests: {memory: "512Mi", cpu: "500m"}
    limits: {memory: "1Gi", cpu: "1000m"}
```

## 5. Service Mesh Configuration

### 5.1 Istio Virtual Service
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: trading-services
spec:
  hosts: ["api.grekko.trading"]
  http:
  - match:
    - uri: {prefix: "/v1/coordination"}
    route:
    - destination: {host: agent-coordination, port: {number: 8080}}
    timeout: 5s
    retries: {attempts: 3, perTryTimeout: 2s}
  - match:
    - uri: {prefix: "/v1/risk"}
    route:
    - destination: {host: risk-management, port: {number: 8080}}
    timeout: 2s
    retries: {attempts: 2, perTryTimeout: 1s}
```

### 5.2 Circuit Breaker Configuration
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: trading-services-dr
spec:
  host: "*.trading-prod.svc.cluster.local"
  trafficPolicy:
    tls: {mode: ISTIO_MUTUAL}
    connectionPool:
      tcp: {maxConnections: 100}
      http: {http1MaxPendingRequests: 50}
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

## 6. Monitoring and Observability

### 6.1 Prometheus Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'trading-services'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ['trading-prod']
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### 6.2 Grafana Dashboards
```json
{
  "dashboard": {
    "title": "Trading System Overview",
    "panels": [
      {
        "title": "Order Execution Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, trading_order_execution_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Risk Assessment Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(trading_risk_assessments_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## 7. CI/CD Pipeline

### 7.1 GitHub Actions Workflow
```yaml
name: Deploy Trading Services
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and Push Images
      run: |
        docker build -t ${{ secrets.REGISTRY }}/agent-coordination:${{ github.sha }} .
        docker push ${{ secrets.REGISTRY }}/agent-coordination:${{ github.sha }}
    - name: Deploy to Kubernetes
      run: |
        helm upgrade --install trading-services ./helm/trading-services \
          --set global.imageTag=${{ github.sha }} \
          --namespace trading-prod
```

### 7.2 Deployment Strategy
- **Blue-Green Deployment**: Zero-downtime deployments
- **Canary Releases**: Gradual rollout with traffic splitting
- **Automated Rollback**: Automatic rollback on health check failures
- **Feature Flags**: Runtime configuration changes without deployment

## 8. Disaster Recovery

### 8.1 Backup Strategy
- **Database**: Continuous WAL archiving + daily snapshots
- **Redis**: RDB snapshots every hour + AOF persistence
- **Configuration**: Git-based versioning with automated backups
- **Secrets**: Encrypted backups in multiple regions

### 8.2 Recovery Procedures
1. **Service Failure**: Automatic pod restart via Kubernetes
2. **Node Failure**: Automatic pod rescheduling
3. **Zone Failure**: Traffic rerouting to healthy zones
4. **Region Failure**: Manual failover to DR region

### 8.3 RTO/RPO Targets
- **Critical Services**: RTO 15 minutes, RPO 1 minute
- **Non-Critical Services**: RTO 1 hour, RPO 15 minutes
- **Data Recovery**: RTO 30 minutes, RPO 5 minutes

---

*This deployment architecture provides the operational foundation for the autonomous cryptocurrency trading system, ensuring high availability, scalability, and maintainability in production environments.*