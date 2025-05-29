# Production Deployment Guide - Grekko Trading System

## Overview

This guide provides comprehensive instructions for deploying the Grekko Trading System to production using blue-green deployment strategy with zero-downtime updates, comprehensive monitoring, and disaster recovery capabilities.

## Architecture Overview

### Core Components
- **MetaMask Integration Service** - Web3 wallet automation with SecurityManager
- **Coinbase Integration Service** - CEX trading and market data
- **Risk Management Service** - Real-time risk monitoring and compliance
- **Agent Coordination Service** - Multi-agent orchestration and consensus
- **Infrastructure Services** - Kafka, PostgreSQL, Redis, InfluxDB clusters
- **Monitoring Stack** - Prometheus, Grafana, AlertManager
- **Service Mesh** - Istio for traffic management and security

### Deployment Strategy
- **Blue-Green Deployment** - Zero-downtime updates with instant rollback
- **Auto-scaling** - HPA based on CPU/memory utilization
- **Health Checks** - Comprehensive liveness and readiness probes
- **Security** - Network policies, RBAC, secret management
- **Monitoring** - Full observability with metrics, logs, and traces

## Prerequisites

### Infrastructure Requirements
- Kubernetes cluster (v1.28+) with 9 nodes (3 masters, 6 workers)
- Minimum 40 CPU cores and 80GB RAM
- 500GB+ storage for backups
- Load balancer with SSL termination
- Container registry access
- Secret management system

### Tools Required
- `kubectl` (v1.28+)
- `docker` (for image scanning)
- `helm` (v3.0+)
- `trivy` (for security scanning)
- Access to cloud storage (S3/GCS) for backups

### Secrets Configuration
Before deployment, ensure these secrets are configured:

```bash
# Database credentials
kubectl create secret generic postgresql-credentials \
  --from-literal=password=<POSTGRES_PASSWORD> \
  -n trading-prod

kubectl create secret generic influxdb-credentials \
  --from-literal=token=<INFLUX_TOKEN> \
  -n trading-prod

# Trading API credentials
kubectl create secret generic trading-secrets \
  --from-literal=coinbase_api_key=<COINBASE_API_KEY> \
  --from-literal=coinbase_api_secret=<COINBASE_API_SECRET> \
  --from-literal=metamask_private_key=<METAMASK_PRIVATE_KEY> \
  --from-literal=database_url=<DATABASE_URL> \
  --from-literal=redis_url=<REDIS_URL> \
  --from-literal=kafka_brokers=<KAFKA_BROKERS> \
  -n trading-prod

# Monitoring credentials
kubectl create secret generic monitoring-secrets \
  --from-literal=prometheus_auth_token=<PROMETHEUS_TOKEN> \
  --from-literal=grafana_admin_password=<GRAFANA_PASSWORD> \
  --from-literal=slack_webhook_url=<SLACK_WEBHOOK> \
  --from-literal=pagerduty_routing_key=<PAGERDUTY_KEY> \
  -n monitoring
```

## Deployment Process

### 1. Pre-Deployment Validation

```bash
# Validate Kubernetes configurations
kubectl apply --dry-run=client -f k8s/

# Check cluster resources
kubectl top nodes
kubectl get nodes -o wide

# Verify secrets
kubectl get secrets -n trading-prod
kubectl get secrets -n monitoring
```

### 2. Infrastructure Deployment

Deploy infrastructure components first:

```bash
# Deploy cluster configuration
kubectl apply -f k8s/cluster/cluster-config.yaml

# Deploy service mesh
kubectl apply -f k8s/service-mesh/istio-config.yaml

# Deploy databases
kubectl apply -f k8s/databases/
kubectl wait --for=condition=available --timeout=600s deployment/postgresql-cluster -n trading-prod
kubectl wait --for=condition=available --timeout=600s deployment/redis-cluster -n trading-prod
kubectl wait --for=condition=available --timeout=600s deployment/influxdb-cluster -n trading-prod

# Deploy message bus
kubectl apply -f k8s/message-bus/kafka-cluster.yaml
kubectl wait --for=condition=available --timeout=600s deployment/kafka-cluster -n trading-prod

# Deploy monitoring stack
kubectl apply -f k8s/monitoring/
kubectl wait --for=condition=available --timeout=600s deployment/prometheus -n monitoring
kubectl wait --for=condition=available --timeout=600s deployment/grafana -n monitoring
```

### 3. Application Deployment

Use the automated deployment script:

```bash
# Execute production deployment
./scripts/deploy-production.sh

# Monitor deployment progress
kubectl get pods -n trading-prod -w

# Check service status
kubectl get services -n trading-prod
kubectl get ingress -n trading-prod
```

### 4. Post-Deployment Verification

```bash
# Health checks
kubectl exec -n trading-prod deployment/coinbase-integration-active -- curl -f http://localhost:8080/health
kubectl exec -n trading-prod deployment/metamask-integration-active -- curl -f http://localhost:8080/health
kubectl exec -n trading-prod deployment/risk-management-active -- curl -f http://localhost:8080/health
kubectl exec -n trading-prod deployment/agent-coordination-active -- curl -f http://localhost:8080/health

# Check metrics endpoints
kubectl port-forward -n trading-prod svc/coinbase-integration-active 9090:9090 &
curl http://localhost:9090/metrics

# Verify monitoring
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
kubectl port-forward -n monitoring svc/grafana 3000:3000 &
```

## Monitoring and Observability

### Prometheus Metrics
Access Prometheus at: `https://prometheus.grekko.trading`

Key metrics to monitor:
- `trading_order_execution_duration_seconds` - Order execution latency
- `trading_errors_total` - Error rates
- `metamask_transaction_attempts_total` - Transaction success rates
- `risk_exposure_current` - Current risk exposure
- `kafka_consumer_lag_sum` - Message processing lag

### Grafana Dashboards
Access Grafana at: `https://grafana.grekko.trading`

Pre-configured dashboards:
- **Trading System Overview** - High-level system metrics
- **MetaMask Integration** - Web3 transaction monitoring
- **Risk Management** - Risk exposure and compliance
- **Infrastructure** - Kubernetes cluster health
- **Database Performance** - PostgreSQL, Redis, InfluxDB metrics

### Alerting Rules
Critical alerts configured:
- Service downtime (>1 minute)
- High error rates (>5%)
- High latency (>1 second P95)
- Database connectivity issues
- Kafka consumer lag (>1000 messages)
- High resource utilization (>80%)

## Backup and Disaster Recovery

### Automated Backups
Daily backups are configured for:
- **PostgreSQL** - Full database dump at 2:00 AM
- **Redis** - RDB snapshot at 2:15 AM
- **InfluxDB** - Complete backup at 2:30 AM
- **Kafka** - Topic and consumer group metadata at 2:45 AM

Backups are stored with 30-day retention and uploaded to cloud storage.

### Disaster Recovery Procedure

1. **Assess the situation**
   ```bash
   kubectl get pods -n trading-prod
   kubectl get events -n trading-prod --sort-by='.lastTimestamp'
   ```

2. **Initiate rollback if needed**
   ```bash
   # Automatic rollback is triggered on deployment failure
   # Manual rollback:
   kubectl rollout undo deployment/coinbase-integration-active -n trading-prod
   kubectl rollout undo deployment/metamask-integration-active -n trading-prod
   kubectl rollout undo deployment/risk-management-active -n trading-prod
   kubectl rollout undo deployment/agent-coordination-active -n trading-prod
   ```

3. **Restore from backup if required**
   ```bash
   # Update restore job with backup date
   kubectl patch job disaster-recovery-restore -n backup-system \
     -p '{"spec":{"template":{"spec":{"containers":[{"name":"disaster-recovery","env":[{"name":"RESTORE_DATE","value":"20250529_020000"}]}]}}}}'
   
   # Execute restore
   kubectl create job --from=job/disaster-recovery-restore restore-$(date +%s) -n backup-system
   ```

## Security Considerations

### Network Security
- **Network Policies** - Default deny-all with explicit allow rules
- **Service Mesh** - mTLS encryption for all inter-service communication
- **Ingress** - TLS termination with valid certificates
- **Firewall Rules** - Restricted access to management interfaces

### Secret Management
- **Kubernetes Secrets** - Encrypted at rest and in transit
- **Secret Rotation** - Automated rotation policies
- **Access Control** - RBAC with least-privilege principles
- **Audit Logging** - All secret access logged and monitored

### Container Security
- **Image Scanning** - Trivy security scans in CI/CD pipeline
- **Runtime Security** - Non-root containers with read-only filesystems
- **Resource Limits** - CPU and memory limits enforced
- **Security Contexts** - Restricted security contexts applied

## Scaling and Performance

### Horizontal Pod Autoscaling
Services automatically scale based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Custom metrics (order processing rate)

### Vertical Scaling
Resource requests and limits:
- **MetaMask Integration**: 1-2 CPU, 1-2GB RAM
- **Coinbase Integration**: 0.25-0.5 CPU, 0.5-1GB RAM
- **Risk Management**: 0.25-0.5 CPU, 0.5-1GB RAM
- **Agent Coordination**: 0.25-0.5 CPU, 0.5-1GB RAM

### Performance Optimization
- **Connection Pooling** - Database connection pooling enabled
- **Caching** - Redis caching for frequently accessed data
- **Load Balancing** - Intelligent load balancing with session affinity
- **CDN** - Static assets served via CDN

## Troubleshooting

### Common Issues

1. **Pod Startup Failures**
   ```bash
   kubectl describe pod <pod-name> -n trading-prod
   kubectl logs <pod-name> -n trading-prod --previous
   ```

2. **Service Discovery Issues**
   ```bash
   kubectl get endpoints -n trading-prod
   kubectl get services -n trading-prod
   ```

3. **Database Connection Problems**
   ```bash
   kubectl exec -n trading-prod deployment/postgresql-cluster -- pg_isready
   kubectl exec -n trading-prod deployment/redis-cluster -- redis-cli ping
   ```

4. **High Resource Usage**
   ```bash
   kubectl top pods -n trading-prod
   kubectl describe hpa -n trading-prod
   ```

### Log Analysis
Centralized logging with structured JSON format:
```bash
# View application logs
kubectl logs -f deployment/coinbase-integration-active -n trading-prod

# Search for errors
kubectl logs deployment/metamask-integration-active -n trading-prod | grep ERROR

# Monitor real-time logs
kubectl logs -f -l app.kubernetes.io/part-of=trading-system -n trading-prod
```

## Maintenance Procedures

### Regular Maintenance Tasks
- **Weekly**: Review monitoring dashboards and alerts
- **Monthly**: Update container images and security patches
- **Quarterly**: Disaster recovery testing and backup validation
- **Annually**: Security audit and penetration testing

### Update Procedures
1. **Security Updates** - Automated via CI/CD pipeline
2. **Feature Updates** - Blue-green deployment with validation
3. **Infrastructure Updates** - Rolling updates with zero downtime
4. **Database Updates** - Maintenance windows with backup/restore

### Health Checks
Regular health check procedures:
```bash
# System health overview
kubectl get nodes
kubectl get pods -n trading-prod
kubectl get services -n trading-prod

# Resource utilization
kubectl top nodes
kubectl top pods -n trading-prod

# Backup verification
kubectl get cronjobs -n backup-system
kubectl get jobs -n backup-system
```

## Support and Escalation

### Alert Escalation
1. **Level 1** - Slack notifications for warnings
2. **Level 2** - Email alerts for critical issues
3. **Level 3** - PagerDuty for service outages
4. **Level 4** - Emergency contact for security incidents

### Contact Information
- **DevOps Team**: devops@grekko.trading
- **Security Team**: security@grekko.trading
- **Trading Team**: trading@grekko.trading
- **Emergency Hotline**: +1-XXX-XXX-XXXX

### Documentation Links
- [System Architecture](./system_architecture.md)
- [API Documentation](./api_specifications.md)
- [Security Documentation](./metamask_security_documentation.md)
- [Monitoring Guide](./2_metamask_monitoring_guide.md)
- [Troubleshooting Guide](./3_metamask_troubleshooting_guide.md)

---

**Last Updated**: 2025-05-29  
**Version**: 1.0  
**Maintained By**: DevOps Team