#!/bin/bash

echo "Stopping Grekko Trading System Monitoring..."

# Stop monitoring stack
docker-compose down

echo "Monitoring services stopped."
