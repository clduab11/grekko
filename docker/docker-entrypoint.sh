#!/bin/bash
set -e

# Create necessary directories
mkdir -p /app/logs

# Wait for postgres
if [ "$WAIT_FOR_POSTGRES" = "true" ]; then
  echo "Waiting for postgres..."
  while ! nc -z postgres 5432; do
    sleep 0.1
  done
  echo "PostgreSQL started"
fi

# Wait for redis
if [ "$WAIT_FOR_REDIS" = "true" ]; then
  echo "Waiting for redis..."
  while ! nc -z redis 6379; do
    sleep 0.1
  done
  echo "Redis started"
fi

exec "$@"