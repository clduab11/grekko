# Metamask Integration Service - Troubleshooting Guide

This document provides comprehensive troubleshooting procedures, common issues, diagnostic tools, and resolution strategies for the Metamask Integration Service.

## Table of Contents

- [Diagnostic Tools](#diagnostic-tools)
- [Common Issues](#common-issues)
- [Browser Automation Problems](#browser-automation-problems)
- [Security and Authentication Issues](#security-and-authentication-issues)
- [Performance Problems](#performance-problems)
- [Network and Connectivity Issues](#network-and-connectivity-issues)
- [Database and Storage Issues](#database-and-storage-issues)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Emergency Procedures](#emergency-procedures)

---

## Diagnostic Tools

### Health Check Commands

```bash
# Check service status
kubectl get pods -l app=metamask-integration -n trading-system

# Check service logs
kubectl logs -f deployment/metamask-integration -n trading-system --tail=100

# Check service metrics
curl http://metamask-integration-service:8080/metrics

# Check API health
curl http://metamask-integration-service/api/v1/health

# Check dependencies
kubectl get pods -l app=postgresql -n database
kubectl get pods -l app=redis -n redis
kubectl get pods -l app=kafka -n kafka
```

### Log Analysis Tools

```bash
# Search for errors in logs
kubectl logs deployment/metamask-integration -n trading-system | grep -i error

# Search for security events
kubectl logs deployment/metamask-integration -n trading-system | grep "security_event"

# Search for specific user issues
kubectl logs deployment/metamask-integration -n trading-system | grep "user_id:user123"

# Check browser automation logs
kubectl logs deployment/metamask-integration -n trading-system | grep "browser_controller"
```

### Performance Monitoring

```bash
# Check resource usage
kubectl top pods -l app=metamask-integration -n trading-system

# Check memory usage
kubectl exec -it deployment/metamask-integration -n trading-system -- ps aux

# Check disk usage
kubectl exec -it deployment/metamask-integration -n trading-system -- df -h

# Monitor real-time metrics
watch -n 5 'curl -s http://metamask-integration-service:8080/metrics | grep -E "(cpu|memory|requests)"'
```

---

## Common Issues

### Issue: Service Won't Start

**Symptoms:**
- Pods in `CrashLoopBackOff` state
- Container exits immediately
- Health checks failing

**Diagnostic Steps:**
```bash
# Check pod status
kubectl describe pod <pod-name> -n trading-system

# Check container logs
kubectl logs <pod-name> -n trading-system

# Check events
kubectl get events -n trading-system --sort-by='.lastTimestamp'
```

**Common Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| **Missing environment variables** | Verify all required env vars are set in deployment |
| **Invalid database connection** | Check database credentials and connectivity |
| **Port conflicts** | Ensure ports 8000 and 8080 are available |
| **Resource limits** | Increase memory/CPU limits in deployment |
| **Image pull errors** | Verify image exists and registry access |

**Resolution Example:**
```bash
# Fix missing environment variable
kubectl patch deployment metamask-integration -n trading-system -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "metamask-integration",
            "env": [
              {
                "name": "DATABASE_URL",
                "valueFrom": {
                  "secretKeyRef": {
                    "name": "database-secrets",
                    "key": "postgresql-url"
                  }
                }
              }
            ]
          }
        ]
      }
    }
  }
}'
```

### Issue: High Memory Usage

**Symptoms:**
- Pods getting OOMKilled
- Memory usage consistently above 80%
- Browser processes consuming excessive memory

**Diagnostic Steps:**
```bash
# Check memory usage
kubectl top pods -l app=metamask-integration -n trading-system

# Check browser processes
kubectl exec -it deployment/metamask-integration -n trading-system -- ps aux | grep chrome

# Check memory metrics
curl -s http://metamask-integration-service:8080/metrics | grep memory
```

**Solutions:**
```bash
# Increase memory limits
kubectl patch deployment metamask-integration -n trading-system -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "metamask-integration",
            "resources": {
              "limits": {
                "memory": "8Gi"
              },
              "requests": {
                "memory": "4Gi"
              }
            }
          }
        ]
      }
    }
  }
}'

# Restart deployment to apply changes
kubectl rollout restart deployment/metamask-integration -n trading-system
```

### Issue: Rate Limiting Errors

**Symptoms:**
- HTTP 429 responses
- "Rate limit exceeded" errors
- Requests being rejected

**Diagnostic Steps:**
```bash
# Check rate limit metrics
curl -s http://metamask-integration-service:8080/metrics | grep rate_limit

# Check Redis rate limit data
kubectl exec -it redis-pod -n redis -- redis-cli keys "*rate_limit*"

# Check recent 429 responses
kubectl logs deployment/metamask-integration -n trading-system | grep "429"
```

**Solutions:**
```python
# Adjust rate limits in configuration
rate_limits = {
    "default": "20/minute",  # Increased from 10/minute
    "wallet_connect": "10/minute",  # Increased from 5/minute
    "transaction_operations": "10/minute"  # Increased from 5/minute
}

# Or implement exponential backoff in client
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

---

## Browser Automation Problems

### Issue: Chrome Browser Crashes

**Symptoms:**
- Browser automation timeouts
- Chrome process exits unexpectedly
- "Browser disconnected" errors

**Diagnostic Steps:**
```bash
# Check browser processes
kubectl exec -it deployment/metamask-integration -n trading-system -- ps aux | grep chrome

# Check browser logs
kubectl logs deployment/metamask-integration -n trading-system | grep -i "chrome\|browser"

# Check available memory
kubectl exec -it deployment/metamask-integration -n trading-system -- free -h
```

**Solutions:**
```python
# Optimize Chrome flags
chrome_args = [
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",  # Reduce memory usage
    "--disable-javascript",  # If not needed
    "--memory-pressure-off",
    "--max_old_space_size=4096"
]

# Implement browser restart mechanism
class BrowserManager:
    def __init__(self):
        self.browser = None
        self.restart_threshold = 10  # Restart after 10 operations
        self.operation_count = 0
    
    async def get_browser(self):
        if self.browser is None or self.operation_count >= self.restart_threshold:
            await self.restart_browser()
        return self.browser
    
    async def restart_browser(self):
        if self.browser:
            await self.browser.close()
        self.browser = await playwright.chromium.launch(args=chrome_args)
        self.operation_count = 0
```

### Issue: Metamask Extension Not Loading

**Symptoms:**
- Extension not found in browser
- Metamask UI not appearing
- Extension installation failures

**Diagnostic Steps:**
```bash
# Check extension path
kubectl exec -it deployment/metamask-integration -n trading-system -- ls -la /opt/metamask

# Check browser extension loading
kubectl logs deployment/metamask-integration -n trading-system | grep "extension"

# Verify extension permissions
kubectl exec -it deployment/metamask-integration -n trading-system -- ls -la /opt/metamask/manifest.json
```

**Solutions:**
```python
# Ensure proper extension loading
browser_context = await browser.new_context(
    user_data_dir="/tmp/browser-session",
    args=[
        f"--load-extension=/opt/metamask",
        "--disable-extensions-except=/opt/metamask"
    ]
)

# Verify extension is loaded
extensions = await browser_context.evaluate("""
    () => {
        return Object.keys(chrome.runtime.getManifest ? chrome.runtime : {});
    }
""")
```

---

## Security and Authentication Issues

### Issue: JWT Token Validation Failures

**Symptoms:**
- 401 Unauthorized responses
- "Invalid token" errors
- Authentication failures

**Diagnostic Steps:**
```bash
# Check JWT secret configuration
kubectl get secret metamask-secrets -n trading-system -o yaml

# Check authentication logs
kubectl logs deployment/metamask-integration -n trading-system | grep "auth"

# Verify token format
echo "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | base64 -d
```

**Solutions:**
```python
# Debug JWT validation
import jwt
import logging

def validate_jwt_token(token: str, secret: str):
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        logging.info(f"Token validated successfully: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        logging.error("Token has expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logging.error(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Check token expiration
def check_token_expiration(payload):
    exp = payload.get('exp')
    if exp and datetime.utcnow().timestamp() > exp:
        raise HTTPException(status_code=401, detail="Token expired")
```

### Issue: Session Management Problems

**Symptoms:**
- Sessions expiring prematurely
- Session not found errors
- Multiple sessions for same user

**Diagnostic Steps:**
```bash
# Check Redis session data
kubectl exec -it redis-pod -n redis -- redis-cli keys "*session*"

# Check session metrics
curl -s http://metamask-integration-service:8080/metrics | grep session

# Check session cleanup logs
kubectl logs deployment/metamask-integration -n trading-system | grep "session_cleanup"
```

**Solutions:**
```python
# Implement robust session management
class SessionManager:
    def __init__(self, redis_client, session_timeout=3600):
        self.redis = redis_client
        self.session_timeout = session_timeout
    
    async def create_session(self, user_id: str):
        session_token = str(uuid.uuid4())
        session_data = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_activity': time.time()
        }
        
        # Store with expiration
        await self.redis.setex(
            f"session:{session_token}",
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return session_token
    
    async def validate_session(self, session_token: str):
        session_data = await self.redis.get(f"session:{session_token}")
        if not session_data:
            raise InvalidSessionError("Session not found")
        
        # Update last activity
        data = json.loads(session_data)
        data['last_activity'] = time.time()
        await self.redis.setex(
            f"session:{session_token}",
            self.session_timeout,
            json.dumps(data)
        )
        
        return data
```

---

## Performance Problems

### Issue: Slow API Response Times

**Symptoms:**
- Response times > 5 seconds
- Timeout errors
- High P95 latency

**Diagnostic Steps:**
```bash
# Check response time metrics
curl -s http://metamask-integration-service:8080/metrics | grep duration

# Check database query performance
kubectl logs deployment/metamask-integration -n trading-system | grep "slow_query"

# Monitor real-time performance
curl -w "@curl-format.txt" -o /dev/null -s http://metamask-integration-service/api/v1/health
```

**Solutions:**
```python
# Implement caching
from functools import lru_cache
import asyncio

class PerformanceOptimizer:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    @lru_cache(maxsize=1000)
    async def get_cached_data(self, key: str):
        cached = await self.redis.get(f"cache:{key}")
        if cached:
            return json.loads(cached)
        return None
    
    async def set_cached_data(self, key: str, data: dict):
        await self.redis.setex(
            f"cache:{key}",
            self.cache_ttl,
            json.dumps(data)
        )

# Implement connection pooling
async def create_optimized_db_pool():
    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=10,
        max_size=20,
        command_timeout=30,
        server_settings={
            'application_name': 'metamask_integration',
            'tcp_keepalives_idle': '600',
            'tcp_keepalives_interval': '30',
            'tcp_keepalives_count': '3'
        }
    )
```

### Issue: Database Connection Pool Exhaustion

**Symptoms:**
- "Connection pool exhausted" errors
- Database timeouts
- Slow database operations

**Diagnostic Steps:**
```bash
# Check database connections
kubectl exec -it postgres-pod -n database -- psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE datname='metamask_integration';"

# Check connection pool metrics
curl -s http://metamask-integration-service:8080/metrics | grep db_connections

# Check database logs
kubectl logs postgres-pod -n database | grep -i connection
```

**Solutions:**
```python
# Optimize connection pool settings
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}

# Implement connection monitoring
class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(
            DATABASE_URL,
            **DATABASE_CONFIG,
            echo_pool=True  # Enable connection pool logging
        )
    
    async def get_pool_status(self):
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
```

---

## Network and Connectivity Issues

### Issue: External API Timeouts

**Symptoms:**
- Blockchain RPC timeouts
- External service connection failures
- Network-related errors

**Diagnostic Steps:**
```bash
# Test external connectivity
kubectl exec -it deployment/metamask-integration -n trading-system -- curl -I https://mainnet.infura.io/v3/

# Check DNS resolution
kubectl exec -it deployment/metamask-integration -n trading-system -- nslookup mainnet.infura.io

# Check network policies
kubectl get networkpolicies -n trading-system
```

**Solutions:**
```python
# Implement retry logic with exponential backoff
import aiohttp
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class NetworkManager:
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async def get_session(self):
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
        return self.session
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def make_request(self, url: str, **kwargs):
        session = await self.get_session()
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.json()
```

---

## Database and Storage Issues

### Issue: Database Migration Failures

**Symptoms:**
- Migration scripts failing
- Schema version mismatches
- Database initialization errors

**Diagnostic Steps:**
```bash
# Check migration status
kubectl exec -it deployment/metamask-integration -n trading-system -- alembic current

# Check migration history
kubectl exec -it deployment/metamask-integration -n trading-system -- alembic history

# Check database schema
kubectl exec -it postgres-pod -n database -- psql -U postgres -d metamask_integration -c "\dt"
```

**Solutions:**
```bash
# Run migrations manually
kubectl exec -it deployment/metamask-integration -n trading-system -- alembic upgrade head

# Rollback if needed
kubectl exec -it deployment/metamask-integration -n trading-system -- alembic downgrade -1

# Check for conflicts
kubectl exec -it deployment/metamask-integration -n trading-system -- alembic show head
```

---

## Monitoring and Alerting

### Issue: Missing Metrics

**Symptoms:**
- Prometheus not scraping metrics
- Missing data in Grafana
- Alert rules not firing

**Diagnostic Steps:**
```bash
# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Check service monitor
kubectl get servicemonitor metamask-integration-monitor -n trading-system

# Test metrics endpoint
curl http://metamask-integration-service:8080/metrics
```

**Solutions:**
```yaml
# Fix ServiceMonitor configuration
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

## Emergency Procedures

### Service Outage Response

```bash
# 1. Immediate assessment
kubectl get pods -l app=metamask-integration -n trading-system
kubectl get events -n trading-system --sort-by='.lastTimestamp' | tail -20

# 2. Scale up if needed
kubectl scale deployment metamask-integration --replicas=5 -n trading-system

# 3. Check dependencies
kubectl get pods -n database
kubectl get pods -n redis
kubectl get pods -n kafka

# 4. Emergency rollback if needed
kubectl rollout undo deployment/metamask-integration -n trading-system

# 5. Monitor recovery
watch kubectl get pods -l app=metamask-integration -n trading-system
```

### Security Incident Response

```bash
# 1. Isolate service if compromised
kubectl patch deployment metamask-integration -n trading-system -p '{"spec":{"replicas":0}}'

# 2. Collect evidence
kubectl logs deployment/metamask-integration -n trading-system > incident-logs.txt

# 3. Check for suspicious activity
grep -i "security_event\|suspicious\|unauthorized" incident-logs.txt

# 4. Rotate secrets if needed
kubectl delete secret metamask-secrets -n trading-system
kubectl create secret generic metamask-secrets --from-literal=jwt-secret=NEW_SECRET

# 5. Restart with new secrets
kubectl rollout restart deployment/metamask-integration -n trading-system
```

---

*This troubleshooting guide provides comprehensive diagnostic and resolution procedures for the Metamask Integration Service. For deployment issues, see [Deployment Guide](1_metamask_deployment_guide.md). For monitoring setup, see [Monitoring Guide](2_metamask_monitoring_guide.md).*