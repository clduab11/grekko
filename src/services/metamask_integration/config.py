"""Configuration

Manages environment-based configuration, including:
- Environment-based configuration
- Network RPC endpoints
- Browser automation settings
- Security parameters
- Performance tuning options

Provides centralized configuration management for all wallet operations.
"""
# Metrics configuration for Prometheus integration
METRICS_ENABLED = True
METRICS_PORT = 8000
METRICS_ENDPOINT = "/metrics"

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Database configuration
DATABASE_HOST = "localhost"
DATABASE_PORT = 5432
DATABASE_NAME = "metamask_db"
DATABASE_USER = "admin"
DATABASE_PASSWORD = "password"

# Web3 Provider configuration
WEB3_PROVIDER_URL = "http://localhost:8545"

# Browser automation configuration
BROWSER_TYPE = "chrome"
BROWSER_HEADLESS = True