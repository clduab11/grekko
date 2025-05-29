# Metamask Integration Service - Deployment Guide

This document provides comprehensive instructions for deploying, configuring, and scaling the Metamask Integration Service in production environments using Kubernetes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Setup](#database-setup)
- [Security Configuration](#security-configuration)
- [Scaling Configuration](#scaling-configuration)
- [Health Checks and Monitoring](#health-checks-and-monitoring)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting Deployment](#troubleshooting-deployment)

---

## Prerequisites

### System Requirements

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| **Kubernetes** | v1.24+ | Container orchestration |
| **CPU** | 2 cores minimum, 4 cores recommended | Service execution |
| **Memory** | 4GB minimum, 8GB recommended | Browser automation and caching |
| **Storage** | 20GB minimum, 100GB recommended | Session data and logs |
| **Network** | 1Gbps minimum | Real-time communication |

### Infrastructure Dependencies

```yaml
# Required infrastructure components
dependencies:
  - postgresql: ">=14.0"
  - redis: ">=6.0" 
  - kafka: ">=3.0"
  - prometheus: ">=2.40"
  - grafana: ">=9.0"
```

### Browser Requirements

```bash
# Chrome/Chromium installation for browser automation
apt-get update && apt-get install -y \
    chromium-browser \
    chromium-chromedriver \
    fonts-liberation \
    xvfb
```

---

## Environment Configuration

### Environment Variables

```yaml
# Production environment configuration
env:
  # Application Configuration
  - name: ENVIRONMENT
    value: "production"
  - name: LOG_LEVEL
    value: "INFO"
  - name: API_HOST
    value: "0.0.0.0"
  - name: API_PORT
    value: "8000"
  
  # Security Configuration
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: metamask-secrets
        key: jwt-secret
  - name: ALLOWED_ORIGINS
    value: "https://app.grekko.com,https://admin.grekko.com"
  
  # Database Configuration
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: database-secrets
        key: postgresql-url
  - name: DATABASE_POOL_SIZE
    value: "20"
  - name: DATABASE_MAX_OVERFLOW
    value: "30"
  
  # Redis Configuration
  - name: REDIS_URL
    valueFrom:
      secretKeyRef:
        name: redis-secrets
        key: redis-url
  - name: REDIS_SESSION_DB
    value: "0"
  - name: REDIS_RATE_LIMIT_DB
    value: "1"
  
  # Kafka Configuration
  - name: KAFKA_BOOTSTRAP_SERVERS
    value: "kafka-1.kafka.svc.cluster.local:9092,kafka-2.kafka.svc.cluster.local:9092"
  - name: KAFKA_SECURITY_PROTOCOL
    value: "SASL_SSL"
  
  # Browser Configuration
  - name: BROWSER_HEADLESS
    value: "true"
  - name: BROWSER_TIMEOUT
    value: "30000"
  - name: METAMASK_EXTENSION_PATH
    value: "/opt/metamask"
  
  # Monitoring Configuration
  - name: METRICS_ENABLED
    value: "true"
  - name: TRACING_ENABLED
    value: "true"
  - name: JAEGER_ENDPOINT
    value: "http://jaeger-collector.monitoring.svc.cluster.local:14268"
```

### Secret Management

```yaml
# Create secrets for sensitive data
apiVersion: v1
kind: Secret
metadata:
  name: metamask-secrets
  namespace: trading-system
type: Opaque
data:
  jwt-secret: <base64-encoded-secret>
  
---
apiVersion: v1
kind: Secret
metadata:
  name: database-secrets
  namespace: trading-system
type: Opaque
data:
  postgresql-url: <base64-encoded-connection-string>
  
---
apiVersion: v1
kind: Secret
metadata:
  name: redis-secrets
  namespace: trading-system
type: Opaque
data:
  redis-url: <base64-encoded-redis-url>
```

---

## Kubernetes Deployment

### Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamask-integration
  namespace: trading-system
  labels:
    app: metamask-integration
    component: wallet-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: metamask-integration
  template:
    metadata:
      labels:
        app: metamask-integration
        component: wallet-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/path: "/metrics"
        prometheus.io/port: "8000"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: metamask-integration
        image: grekko/metamask-integration:v1.0.0
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 8080
          name: metrics
        env:
          # Environment variables from above
        envFrom:
        - configMapRef:
            name: metamask-config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: browser-data
          mountPath: /tmp/browser-sessions
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: browser-data
        emptyDir:
          sizeLimit: 1Gi
      - name: logs
        emptyDir:
          sizeLimit: 2Gi
```

### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: metamask-integration-service
  namespace: trading-system
  labels:
    app: metamask-integration
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: metrics
  selector:
    app: metamask-integration
```

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: metamask-integration-ingress
  namespace: trading-system
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.grekko.com
    secretName: metamask-integration-tls
  rules:
  - host: api.grekko.com
    http:
      paths:
      - path: /api/v1/metamask
        pathType: Prefix
        backend:
          service:
            name: metamask-integration-service
            port:
              number: 80
```

---

## Database Setup

### PostgreSQL Database Initialization

```sql
-- Create database and user
CREATE DATABASE metamask_integration;
CREATE USER metamask_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE metamask_integration TO metamask_user;

-- Connect to metamask_integration database
\c metamask_integration;

-- Create tables
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

CREATE TABLE wallet_states (
    wallet_address VARCHAR(42) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    network_id INT NOT NULL,
    balance_eth DECIMAL(36,18),
    nonce INT DEFAULT 0,
    last_transaction_hash VARCHAR(66),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);

CREATE TABLE transaction_history (
    id BIGSERIAL PRIMARY KEY,
    transaction_hash VARCHAR(66) UNIQUE,
    wallet_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    value DECIMAL(36,18) NOT NULL,
    gas_limit INT NOT NULL,
    gas_price DECIMAL(36,18) NOT NULL,
    nonce INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    block_number BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP NULL,
    INDEX idx_wallet_address (wallet_address),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### Database Migration

```bash
# Run database migrations
kubectl exec -it deployment/metamask-integration -n trading-system -- \
  python -m alembic upgrade head
```

---

## Security Configuration

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: metamask-integration-netpol
  namespace: trading-system
spec:
  podSelector:
    matchLabels:
      app: metamask-integration
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector:
        matchLabels:
          name: kafka
    ports:
    - protocol: TCP
      port: 9092
```

### Pod Security Policy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: metamask-integration-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

---

## Scaling Configuration

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: metamask-integration-hpa
  namespace: trading-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: metamask-integration
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

### Vertical Pod Autoscaler

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: metamask-integration-vpa
  namespace: trading-system
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: metamask-integration
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: metamask-integration
      maxAllowed:
        memory: 8Gi
        cpu: 4000m
      minAllowed:
        memory: 1Gi
        cpu: 500m
```

---

## Health Checks and Monitoring

### Health Check Endpoints

```python
# Health check implementation
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    # Check database connectivity
    db_healthy = await check_database_connection()
    # Check Redis connectivity  
    redis_healthy = await check_redis_connection()
    # Check Kafka connectivity
    kafka_healthy = await check_kafka_connection()
    
    if all([db_healthy, redis_healthy, kafka_healthy]):
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")
```

### Monitoring Integration

```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: metamask-integration-monitor
  namespace: trading-system
spec:
  selector:
    matchLabels:
      app: metamask-integration
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

---

## Backup and Recovery

### Database Backup Strategy

```bash
# Automated database backup script
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/metamask-integration"
DB_NAME="metamask_integration"

# Create backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/metamask_backup_$TIMESTAMP.sql"

# Compress backup
gzip "$BACKUP_DIR/metamask_backup_$TIMESTAMP.sql"

# Retain last 30 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Disaster Recovery Procedures

```bash
# Recovery from backup
#!/bin/bash
BACKUP_FILE="$1"

# Restore database
gunzip -c $BACKUP_FILE | psql $DATABASE_URL

# Restart application pods
kubectl rollout restart deployment/metamask-integration -n trading-system

# Verify service health
kubectl get pods -l app=metamask-integration -n trading-system
```

---

## Troubleshooting Deployment

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Pod Startup Failure** | CrashLoopBackOff | Check environment variables and secrets |
| **Database Connection** | Connection refused | Verify database credentials and network policies |
| **Browser Automation Failure** | Chrome crash | Increase memory limits and check security context |
| **Rate Limiting** | 429 errors | Adjust rate limit configuration |
| **High Memory Usage** | OOMKilled | Increase memory limits or optimize browser usage |

### Debugging Commands

```bash
# Check pod status
kubectl get pods -l app=metamask-integration -n trading-system

# View pod logs
kubectl logs -f deployment/metamask-integration -n trading-system

# Access pod shell
kubectl exec -it deployment/metamask-integration -n trading-system -- /bin/bash

# Check service endpoints
kubectl get endpoints metamask-integration-service -n trading-system

# Monitor resource usage
kubectl top pods -l app=metamask-integration -n trading-system
```

### Performance Monitoring

```bash
# Monitor key metrics
curl http://metamask-integration-service:8080/metrics | grep -E "(cpu|memory|requests)"

# Check database connections
kubectl exec -it postgres-pod -- psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE datname='metamask_integration';"

# Monitor Redis usage
kubectl exec -it redis-pod -- redis-cli info memory
```

---

*This deployment guide provides production-ready configuration for the Metamask Integration Service. For security considerations, see [Security Documentation](metamask_security_documentation.md). For monitoring setup, see [Monitoring Guide](2_metamask_monitoring_guide.md).*