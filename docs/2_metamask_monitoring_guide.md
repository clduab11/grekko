# Metamask Integration Service - Monitoring and Observability Guide

This document provides comprehensive monitoring, observability, and alerting setup for the Metamask Integration Service, including Prometheus metrics, Grafana dashboards, distributed tracing, and incident response procedures.

## Table of Contents

- [Monitoring Architecture](#monitoring-architecture)
- [Metrics Implementation](#metrics-implementation)
- [Grafana Dashboards](#grafana-dashboards)
- [Distributed Tracing](#distributed-tracing)
- [Log Management](#log-management)
- [Alerting Configuration](#alerting-configuration)
- [Performance Monitoring](#performance-monitoring)
- [Incident Response](#incident-response)

---

## Monitoring Architecture

### Observability Stack

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Prometheus    │    │     Grafana     │
│   Metrics       │───▶│   Collection    │───▶│   Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │      Loki       │              │
         └──────────────│   Log Storage   │──────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │     Jaeger      │
                        │ Distributed     │
                        │    Tracing      │
                        └─────────────────┘
```

### Component Integration

| Component | Purpose | Integration Method |
|-----------|---------|-------------------|
| **Prometheus** | Metrics collection and storage | HTTP `/metrics` endpoint |
| **Grafana** | Visualization and dashboards | Prometheus data source |
| **Loki** | Log aggregation and search | Structured JSON logs |
| **Jaeger** | Distributed tracing | OpenTelemetry integration |
| **AlertManager** | Alert routing and notification | Prometheus rules |

---

## Metrics Implementation

### Prometheus Client Setup

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Security Metrics
auth_failures_total = Counter(
    'metamask_auth_failures_total',
    'Total authentication failures',
    ['user_id', 'reason']
)

suspicious_transactions_total = Counter(
    'metamask_suspicious_transactions_detected_total',
    'Total suspicious transactions detected',
    ['transaction_type', 'reason']
)

# Performance Metrics
api_request_duration = Histogram(
    'metamask_api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint', 'method', 'status_code'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

api_requests_total = Counter(
    'metamask_api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status_code']
)

# Business Metrics
wallet_connections_total = Counter(
    'metamask_wallet_connection_attempts_total',
    'Total wallet connection attempts',
    ['status']
)

active_sessions = Gauge(
    'metamask_user_sessions_active',
    'Currently active user sessions'
)

transaction_duration = Histogram(
    'metamask_transaction_duration_seconds',
    'Transaction processing duration',
    ['transaction_type', 'status'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)
```

### Metrics Instrumentation

```python
from functools import wraps
import time

def monitor_api_calls(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint = func.__name__
        method = "POST"  # or extract from request
        status_code = 200
        
        try:
            result = await func(*args, **kwargs)
            return result
        except HTTPException as e:
            status_code = e.status_code
            raise
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            api_request_duration.labels(
                endpoint=endpoint,
                method=method,
                status_code=status_code
            ).observe(duration)
            
            api_requests_total.labels(
                endpoint=endpoint,
                method=method,
                status_code=status_code
            ).inc()
    
    return wrapper

# Usage example
@monitor_api_calls
async def wallet_connect(request: WalletConnectRequest):
    # Implementation
    pass
```

### Custom Metrics Collection

```python
class MetamaskMetrics:
    def __init__(self):
        self.dependency_health = Gauge(
            'metamask_dependency_health',
            'Health status of dependencies',
            ['dependency_name', 'status']
        )
        
        self.browser_automation_duration = Histogram(
            'metamask_browser_automation_duration_seconds',
            'Browser automation task duration',
            ['task_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0]
        )
    
    def track_dependency_health(self, dependency: str, healthy: bool):
        status = "healthy" if healthy else "unhealthy"
        self.dependency_health.labels(
            dependency_name=dependency,
            status=status
        ).set(1 if healthy else 0)
    
    def track_browser_task(self, task_type: str, duration: float):
        self.browser_automation_duration.labels(
            task_type=task_type
        ).observe(duration)
    
    def track_security_event(self, event_type: str, user_id: str):
        if event_type == "auth_failure":
            auth_failures_total.labels(
                user_id=user_id,
                reason="invalid_credentials"
            ).inc()
        elif event_type == "suspicious_transaction":
            suspicious_transactions_total.labels(
                transaction_type="transfer",
                reason="high_value"
            ).inc()
```

---

## Grafana Dashboards

### Main Service Dashboard

```json
{
  "dashboard": {
    "title": "Metamask Integration Service",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamask_api_requests_total[5m])",
            "legendFormat": "{{endpoint}} - {{status_code}}"
          }
        ]
      },
      {
        "title": "Response Time P95",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(metamask_api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "type": "singlestat",
        "targets": [
          {
            "expr": "metamask_user_sessions_active"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamask_api_requests_total{status_code=~\"4..|5..\"}[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

### Security Dashboard

```json
{
  "dashboard": {
    "title": "Metamask Security Monitoring",
    "panels": [
      {
        "title": "Authentication Failures",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamask_auth_failures_total[5m])",
            "legendFormat": "{{reason}}"
          }
        ]
      },
      {
        "title": "Suspicious Transactions",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamask_suspicious_transactions_detected_total[5m])",
            "legendFormat": "{{reason}}"
          }
        ]
      },
      {
        "title": "Rate Limit Violations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamask_api_requests_total{status_code=\"429\"}[5m])",
            "legendFormat": "Rate Limited Requests"
          }
        ]
      }
    ]
  }
}
```

---

## Distributed Tracing

### OpenTelemetry Configuration

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def setup_tracing():
    # Configure tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger-agent.monitoring.svc.cluster.local",
        agent_port=6831,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
    
    return tracer

# Usage in application code
tracer = setup_tracing()

async def process_transaction(transaction_data):
    with tracer.start_as_current_span("process_transaction") as span:
        span.set_attribute("transaction.value", transaction_data["value"])
        span.set_attribute("transaction.to", transaction_data["to"])
        
        # Add custom events
        span.add_event("validation_started")
        
        try:
            # Process transaction
            result = await validate_and_process(transaction_data)
            span.set_attribute("transaction.status", "success")
            return result
        except Exception as e:
            span.set_attribute("transaction.status", "failed")
            span.set_attribute("error.message", str(e))
            raise
```

### Trace Context Propagation

```python
from opentelemetry.propagate import inject, extract
from opentelemetry import context

async def call_external_service(data):
    # Create headers for context propagation
    headers = {}
    inject(headers)
    
    # Make HTTP request with trace context
    response = await http_client.post(
        "https://external-service.com/api",
        json=data,
        headers=headers
    )
    
    return response

async def kafka_message_handler(message):
    # Extract trace context from Kafka message headers
    ctx = extract(message.headers)
    
    with tracer.start_as_current_span("kafka_message_processing", context=ctx):
        # Process message
        await process_message(message.value)
```

---

## Log Management

### Structured Logging Configuration

```python
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service_name": "metamask-integration-service",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'transaction_id'):
            log_entry['transaction_id'] = record.transaction_id
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        
        return json.dumps(log_entry)

# Configure logger
logger = logging.getLogger("metamask_integration")
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Security Event Logging

```python
def log_security_event(event_type: str, user_id: str, details: dict):
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "security_event": True,
            **details
        }
    )

# Usage examples
log_security_event("authentication_failure", "user123", {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "failure_reason": "invalid_password"
})

log_security_event("suspicious_transaction", "user456", {
    "transaction_value": "100.0",
    "destination_address": "0x742d35Cc...",
    "risk_score": 0.85
})
```

---

## Alerting Configuration

### Prometheus Alert Rules

```yaml
groups:
- name: metamask_integration_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(metamask_api_requests_total{status_code=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"
  
  - alert: HighAuthenticationFailures
    expr: rate(metamask_auth_failures_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High authentication failure rate"
      description: "Authentication failure rate is {{ $value }} per second"
  
  - alert: SuspiciousTransactionSpike
    expr: rate(metamask_suspicious_transactions_detected_total[5m]) > 0.05
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Spike in suspicious transactions"
      description: "Suspicious transaction rate is {{ $value }} per second"
  
  - alert: ServiceDown
    expr: up{job="metamask-integration"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Metamask Integration Service is down"
      description: "Service has been down for more than 1 minute"
```

### AlertManager Configuration

```yaml
global:
  smtp_smarthost: 'smtp.company.com:587'
  smtp_from: 'alerts@company.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://slack-webhook.company.com/alerts'

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@company.com'
    subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  
- name: 'warning-alerts'
  email_configs:
  - to: 'team@company.com'
    subject: 'WARNING: {{ .GroupLabels.alertname }}'
```

---

## Performance Monitoring

### Key Performance Indicators

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **API Response Time (P95)** | < 500ms | > 1000ms |
| **Error Rate** | < 1% | > 5% |
| **Availability** | > 99.9% | < 99% |
| **Transaction Success Rate** | > 95% | < 90% |
| **Browser Automation Time** | < 30s | > 60s |

### Performance Queries

```promql
# API Response Time P95
histogram_quantile(0.95, rate(metamask_api_request_duration_seconds_bucket[5m]))

# Error Rate
rate(metamask_api_requests_total{status_code=~"4..|5.."}[5m]) / rate(metamask_api_requests_total[5m]) * 100

# Availability
avg_over_time(up{job="metamask-integration"}[24h]) * 100

# Transaction Success Rate
rate(metamask_transaction_completed_total[5m]) / rate(metamask_transaction_attempts_total[5m]) * 100

# Active Sessions Trend
increase(metamask_user_sessions_active[1h])
```

---

## Incident Response

### Incident Classification

| Severity | Response Time | Description |
|----------|---------------|-------------|
| **P0 - Critical** | 15 minutes | Service completely down, security breach |
| **P1 - High** | 1 hour | Significant degradation, high error rates |
| **P2 - Medium** | 4 hours | Moderate impact, some features affected |
| **P3 - Low** | 24 hours | Minor issues, monitoring alerts |

### Runbook Examples

#### High Error Rate Response

```bash
# 1. Check service status
kubectl get pods -l app=metamask-integration -n trading-system

# 2. Check recent logs
kubectl logs -f deployment/metamask-integration -n trading-system --tail=100

# 3. Check metrics
curl http://metamask-integration-service:8080/metrics | grep error

# 4. Scale if needed
kubectl scale deployment metamask-integration --replicas=5 -n trading-system

# 5. Check dependencies
kubectl get pods -l app=postgresql -n database
kubectl get pods -l app=redis -n redis
```

#### Security Incident Response

```bash
# 1. Check security logs
kubectl logs deployment/metamask-integration -n trading-system | grep "security_event"

# 2. Review authentication failures
curl -s "http://prometheus:9090/api/v1/query?query=rate(metamask_auth_failures_total[5m])"

# 3. Check for suspicious patterns
kubectl logs deployment/metamask-integration -n trading-system | grep "suspicious"

# 4. If confirmed breach, isolate service
kubectl patch deployment metamask-integration -n trading-system -p '{"spec":{"replicas":0}}'
```

### Monitoring Health Checks

```python
async def health_check_dependencies():
    health_status = {
        "database": await check_database_health(),
        "redis": await check_redis_health(),
        "kafka": await check_kafka_health(),
        "external_apis": await check_external_apis()
    }
    
    # Update metrics
    for dependency, healthy in health_status.items():
        metrics.track_dependency_health(dependency, healthy)
    
    return health_status

async def check_database_health():
    try:
        async with database.get_session() as session:
            await session.execute("SELECT 1")
        return True
    except Exception:
        return False
```

---

*This monitoring guide provides comprehensive observability for the Metamask Integration Service. For deployment instructions, see [Deployment Guide](1_metamask_deployment_guide.md). For security monitoring details, see [Security Documentation](metamask_security_documentation.md).*