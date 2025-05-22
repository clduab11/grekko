# Grekko Deployment Guide

This document provides comprehensive instructions for deploying the Grekko trading platform in various environments, from development to production. Grekko uses Docker for containerization to ensure consistent deployments across different environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Environments](#deployment-environments)
3. [Development Deployment](#development-deployment)
4. [Testing Deployment](#testing-deployment)
5. [Production Deployment](#production-deployment)
6. [Credentials Management](#credentials-management)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Security Considerations](#security-considerations)
10. [Scaling](#scaling)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying Grekko, ensure you have the following prerequisites:

- Docker (20.10+) and Docker Compose (2.0+)
- Git
- Python 3.11+ (for local development only)
- At least 2GB of RAM and 20GB of disk space
- Exchange API keys (for Binance, Coinbase, etc.)
- Network access to cryptocurrency exchanges (check firewall settings)

## Deployment Environments

Grekko supports three deployment environments:

1. **Development**: For development and testing with non-critical resources
2. **Staging**: For pre-production testing with limited funds
3. **Production**: For live trading with real funds

Each environment uses different configuration settings defined in the `config/` directory.

## Development Deployment

The development environment is designed for local development and testing. It uses Docker Compose to create a local development environment with all necessary services.

### Setup Steps

1. Clone the repository:

```bash
git clone https://github.com/clduab11/grekko.git
cd grekko
```

2. Create a credentials directory:

```bash
mkdir -p ~/.grekko
```

3. Create a development configuration:

```bash
cp config/main.yaml.example config/main.yaml
```

4. Start the development environment:

```bash
docker-compose -f docker/docker-compose.yml up -d
```

5. Check the logs:

```bash
docker-compose -f docker/docker-compose.yml logs -f grekko-app
```

### Development Environment Variables

The development environment uses the following environment variables:

- `CONFIG_ENV=development`: Sets the configuration environment
- `LOG_LEVEL=INFO`: Sets the logging level
- `PYTHONPATH=/app`: Sets the Python path within the container

These variables are defined in the `docker/docker-compose.yml` file.

## Testing Deployment

The testing environment is designed for automated testing and continuous integration. It uses Docker Compose to create an isolated environment for running tests.

### Setup Steps

1. Start the testing environment:

```bash
docker-compose -f docker/docker-compose.test.yml up -d
```

2. Run the tests:

```bash
docker-compose -f docker/docker-compose.test.yml exec grekko-app pytest
```

### Testing Environment Variables

The testing environment uses the following environment variables:

- `CONFIG_ENV=testing`: Sets the configuration environment
- `LOG_LEVEL=DEBUG`: Sets the logging level
- `PYTHONPATH=/app`: Sets the Python path within the container
- `TEST_MODE=True`: Enables test mode

## Production Deployment

The production environment is designed for live trading with real funds. It requires careful setup and monitoring.

### Recommended Infrastructure

For production deployment, we recommend:

- A dedicated server with at least 4GB RAM and 50GB SSD
- Ubuntu 20.04 LTS or newer
- Regular system updates and security patches
- Firewall configuration to allow only necessary connections
- Use of Docker with limited container capabilities

### Setup Steps

1. Clone the repository on your production server:

```bash
git clone https://github.com/clduab11/grekko.git
cd grekko
```

2. Create a production configuration:

```bash
cp config/main.yaml.example config/main.yaml
# Edit the configuration file with production settings
```

3. Set up the credentials vault:

```bash
mkdir -p /var/grekko/credentials
chmod 700 /var/grekko/credentials
```

4. Build and start the production environment:

```bash
docker-compose -f docker/docker-compose.prod.yml up -d
```

5. Set up monitoring (see [Monitoring and Logging](#monitoring-and-logging) section)

### Production Environment Variables

Create a `.env` file in your production environment with the following variables:

```
CONFIG_ENV=production
LOG_LEVEL=INFO
GREKKO_HOST=your-server-hostname
GREKKO_CREDENTIALS_PATH=/var/grekko/credentials
DATABASE_URL=postgresql://grekko:secure-password@postgres:5432/grekko
REDIS_URL=redis://redis:6379/0
```

### Securing the Production Environment

Additional steps for securing the production environment:

1. Use Docker secrets for sensitive information:

```bash
echo "your-secure-password" | docker secret create postgres_password -
```

2. Set up a reverse proxy with TLS termination (Nginx or Traefik)

3. Enable Docker's built-in security features:

```bash
# In docker-compose.prod.yml
services:
  grekko-app:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
```

## Credentials Management

Grekko uses a secure credential vault to store API keys and private keys. The credentials are encrypted at rest using AES-256-GCM encryption.

### Setting Up Credentials

1. Initialize the credentials vault:

```bash
python scripts/setup.py --init-vault
```

2. Add exchange API keys:

```bash
python scripts/setup.py --add-credential binance --key YOUR_API_KEY --secret YOUR_API_SECRET
```

3. Verify credentials:

```bash
python scripts/setup.py --list-credentials
```

### Credential Backup

Always back up your credentials vault to a secure location:

```bash
# Backup
tar -czvf grekko-credentials-backup.tar.gz ~/.grekko

# Restore
tar -xzvf grekko-credentials-backup.tar.gz -C /
```

## Monitoring and Logging

Grekko uses a comprehensive logging system that outputs to both files and standard output.

### Log Locations

- Docker logs: `docker-compose logs -f grekko-app`
- Application logs: `/app/logs/grekko_YYYY-MM-DD.log`

### Setting Up Monitoring

For production deployments, we recommend:

1. Prometheus for metrics collection:

```bash
docker-compose -f docker/docker-compose.monitoring.yml up -d
```

2. Grafana for visualization (available at http://your-server:3000)

3. Alert Manager for notifications on critical events

### Key Metrics to Monitor

- Trading activity (trades/minute)
- Error rates
- API call latency
- System resource usage
- P&L metrics
- Exchange connectivity status

## Backup and Recovery

Regular backups are essential for a production deployment.

### Database Backup

```bash
docker-compose -f docker/docker-compose.prod.yml exec postgres pg_dump -U grekko -d grekko > grekko-db-backup.sql
```

### Database Restore

```bash
cat grekko-db-backup.sql | docker-compose -f docker/docker-compose.prod.yml exec -T postgres psql -U grekko -d grekko
```

### Configuration Backup

```bash
tar -czvf grekko-config-backup.tar.gz config/
```

### Full System Backup

For a complete backup of all Grekko data:

```bash
./scripts/backup.sh --full
```

## Security Considerations

Security is paramount for a cryptocurrency trading system. Follow these best practices:

1. Never expose the Grekko API directly to the internet
2. Use a firewall to restrict access to essential ports only
3. Keep the host system updated with security patches
4. Regularly rotate API keys and credentials
5. Use the principle of least privilege for all components
6. Implement IP-based access controls for administrative functions
7. Enable Docker content trust:

```bash
export DOCKER_CONTENT_TRUST=1
```

8. Regularly scan for vulnerabilities:

```bash
docker scan grekko-app:latest
```

## Scaling

As your trading operations grow, you may need to scale the Grekko platform.

### Vertical Scaling

Increase resources for the existing deployment:

1. Stop the current deployment:

```bash
docker-compose -f docker/docker-compose.prod.yml down
```

2. Update your server resources (RAM, CPU)

3. Restart with increased container resources:

```bash
# In docker-compose.prod.yml, update resource limits
services:
  grekko-app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Horizontal Scaling

For advanced users, Grekko can be scaled horizontally:

1. Set up a load balancer (Nginx, HAProxy)
2. Deploy multiple Grekko instances, each handling different trading pairs
3. Use a shared Redis instance for coordination
4. Ensure database connections are properly managed

## Troubleshooting

Common issues and their solutions:

### Connection Issues

If Grekko cannot connect to exchanges:

1. Check network connectivity:

```bash
docker-compose exec grekko-app ping api.binance.com
```

2. Verify API keys are correctly set up:

```bash
docker-compose exec grekko-app python -c "from src.utils.credentials_manager import CredentialsManager; cm = CredentialsManager(); print(cm.test_credentials('binance'))"
```

### Database Issues

If the database connection fails:

1. Check if PostgreSQL is running:

```bash
docker-compose ps postgres
```

2. Verify database credentials:

```bash
docker-compose exec postgres psql -U grekko -c "SELECT 1"
```

### Resource Issues

If Grekko is running slow or crashing:

1. Check resource usage:

```bash
docker stats
```

2. Increase container resources in docker-compose file
3. Consider vertical scaling (see [Scaling](#scaling) section)

### Log Analysis

For detailed troubleshooting:

```bash
grep ERROR logs/grekko_*.log
```

Use the built-in log analyzer for more insights:

```bash
python scripts/analyze_logs.py --last-hour
```

## Appendix: Environment-Specific Configuration Files

Grekko uses different configuration files for different environments:

- Development: `config/environments/development.yaml`
- Testing: `config/environments/testing.yaml`
- Production: `config/environments/production.yaml`

These files override settings in the main configuration file (`config/main.yaml`).