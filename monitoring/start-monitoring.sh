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
