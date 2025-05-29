#!/bin/bash

# Local Development Monitoring Setup Script
# This script sets up basic monitoring tools for local development
# and prepares the foundation for production monitoring

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    log_info "Checking Docker status..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
}

# Create monitoring directories
create_directories() {
    log_info "Creating monitoring directories..."
    
    mkdir -p monitoring/prometheus/config
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/provisioning/dashboards
    mkdir -p monitoring/grafana/provisioning/datasources
    mkdir -p monitoring/logs
    mkdir -p monitoring/data/prometheus
    mkdir -p monitoring/data/grafana
    
    log_success "Monitoring directories created"
}

# Create Prometheus configuration
create_prometheus_config() {
    log_info "Creating Prometheus configuration..."
    
    cat > monitoring/prometheus/config/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'grekko-services'
    static_configs:
      - targets: 
        - 'host.docker.internal:8000'  # Main API
        - 'host.docker.internal:8001'  # Agent Coordination
        - 'host.docker.internal:8002'  # Risk Management
        - 'host.docker.internal:8003'  # Coinbase Integration
        - 'host.docker.internal:8004'  # MetaMask Integration
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']
EOF

    log_success "Prometheus configuration created"
}

# Create Prometheus alert rules
create_alert_rules() {
    log_info "Creating Prometheus alert rules..."
    
    cat > monitoring/prometheus/config/alert_rules.yml << 'EOF'
groups:
  - name: grekko_trading_alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute."

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is {{ $value }} errors per second."

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time on {{ $labels.instance }}"
          description: "95th percentile response time is {{ $value }} seconds."

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 80%."

      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 80%."
EOF

    log_success "Alert rules created"
}

# Create Grafana datasource configuration
create_grafana_datasource() {
    log_info "Creating Grafana datasource configuration..."
    
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    log_success "Grafana datasource configuration created"
}

# Create Grafana dashboard provisioning
create_grafana_dashboard_config() {
    log_info "Creating Grafana dashboard configuration..."
    
    cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Grafana dashboard configuration created"
}

# Create basic Grafana dashboard
create_basic_dashboard() {
    log_info "Creating basic Grafana dashboard..."
    
    cat > monitoring/grafana/dashboards/grekko-overview.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Grekko Trading System Overview",
    "tags": ["grekko", "trading"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up",
            "legendFormat": "{{ instance }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ instance }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{ instance }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{ instance }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "5s"
  }
}
EOF

    log_success "Basic dashboard created"
}

# Create Docker Compose for monitoring stack
create_docker_compose() {
    log_info "Creating Docker Compose configuration..."
    
    cat > monitoring/docker-compose.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: grekko-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/config:/etc/prometheus
      - ./data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grekko-grafana
    ports:
      - "3000:3000"
    volumes:
      - ./data/grafana:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: grekko-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: grekko-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager:/etc/alertmanager
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
EOF

    log_success "Docker Compose configuration created"
}

# Create AlertManager configuration
create_alertmanager_config() {
    log_info "Creating AlertManager configuration..."
    
    mkdir -p monitoring/alertmanager
    
    cat > monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@grekko.trading'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

    log_success "AlertManager configuration created"
}

# Create monitoring startup script
create_startup_script() {
    log_info "Creating monitoring startup script..."
    
    cat > monitoring/start-monitoring.sh << 'EOF'
#!/bin/bash

echo "Starting Grekko Trading System Monitoring..."

# Start monitoring stack
docker-compose up -d

echo "Monitoring services starting..."
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "AlertManager: http://localhost:9093"
echo "Node Exporter: http://localhost:9100"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo "Checking service health..."
curl -s http://localhost:9090/-/healthy > /dev/null && echo "✓ Prometheus is healthy" || echo "✗ Prometheus is not responding"
curl -s http://localhost:3000/api/health > /dev/null && echo "✓ Grafana is healthy" || echo "✗ Grafana is not responding"
curl -s http://localhost:9093/-/healthy > /dev/null && echo "✓ AlertManager is healthy" || echo "✗ AlertManager is not responding"

echo "Monitoring setup complete!"
EOF

    chmod +x monitoring/start-monitoring.sh
    log_success "Startup script created"
}

# Create monitoring stop script
create_stop_script() {
    log_info "Creating monitoring stop script..."
    
    cat > monitoring/stop-monitoring.sh << 'EOF'
#!/bin/bash

echo "Stopping Grekko Trading System Monitoring..."

# Stop monitoring stack
docker-compose down

echo "Monitoring services stopped."
EOF

    chmod +x monitoring/stop-monitoring.sh
    log_success "Stop script created"
}

# Set proper permissions
set_permissions() {
    log_info "Setting proper permissions..."
    
    # Make sure Grafana can write to its data directory
    sudo chown -R 472:472 monitoring/data/grafana 2>/dev/null || {
        log_warning "Could not set Grafana permissions. You may need to run: sudo chown -R 472:472 monitoring/data/grafana"
    }
    
    log_success "Permissions set"
}

# Main execution
main() {
    echo "========================================"
    echo "Grekko Trading System - Local Monitoring Setup"
    echo "========================================"
    echo ""
    
    check_docker
    create_directories
    create_prometheus_config
    create_alert_rules
    create_grafana_datasource
    create_grafana_dashboard_config
    create_basic_dashboard
    create_docker_compose
    create_alertmanager_config
    create_startup_script
    create_stop_script
    set_permissions
    
    echo ""
    log_success "Local monitoring setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. cd monitoring"
    echo "2. ./start-monitoring.sh"
    echo "3. Open http://localhost:3000 (Grafana - admin/admin)"
    echo "4. Open http://localhost:9090 (Prometheus)"
    echo ""
    echo "To add metrics to your services, implement Prometheus metrics endpoints"
    echo "See: docs/monitoring_strategy.md for more details"
}

# Run main function
main "$@"