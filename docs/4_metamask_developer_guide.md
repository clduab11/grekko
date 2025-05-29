# Metamask Integration Service - Developer Guide

This document provides comprehensive instructions for local development setup, testing procedures, code contribution guidelines, and development best practices for the Metamask Integration Service.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Local Development Workflow](#local-development-workflow)
- [Testing Framework](#testing-framework)
- [Code Quality Standards](#code-quality-standards)
- [Debugging and Development Tools](#debugging-and-development-tools)
- [Contribution Guidelines](#contribution-guidelines)
- [Release Process](#release-process)
- [Development Best Practices](#development-best-practices)

---

## Development Environment Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11+ | Runtime environment |
| **Docker** | 20.10+ | Containerization |
| **Docker Compose** | 2.0+ | Local orchestration |
| **Node.js** | 18+ | Frontend development |
| **Git** | 2.30+ | Version control |
| **Chrome/Chromium** | Latest | Browser automation testing |

### Local Installation

```bash
# Clone the repository
git clone https://github.com/company/metamask-integration.git
cd metamask-integration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your local configuration
```

### Environment Configuration

```bash
# .env file for local development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
API_HOST=localhost
API_PORT=8000

# Database (use local PostgreSQL or Docker)
DATABASE_URL=postgresql://postgres:password@localhost:5432/metamask_integration_dev

# Redis (use local Redis or Docker)
REDIS_URL=redis://localhost:6379/0

# Kafka (use Docker Compose)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Browser automation
BROWSER_HEADLESS=false  # Set to true for CI
BROWSER_TIMEOUT=30000
METAMASK_EXTENSION_PATH=./extensions/metamask

# Security (use development keys)
JWT_SECRET=dev-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# External APIs (use testnet endpoints)
ETHEREUM_RPC_URL=https://goerli.infura.io/v3/YOUR_PROJECT_ID
POLYGON_RPC_URL=https://rpc-mumbai.maticvigil.com
```

### Docker Development Setup

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: metamask_integration_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

volumes:
  postgres_data:
  redis_data:
```

```bash
# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
alembic upgrade head

# Start the development server
python -m uvicorn src.services.metamask_integration.api:app --reload --host 0.0.0.0 --port 8000
```

---

## Local Development Workflow

### Development Server

```bash
# Start with hot reload
python -m uvicorn src.services.metamask_integration.api:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level debug

# Or use the development script
python scripts/dev_server.py
```

### Database Management

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database (development only)
python scripts/reset_db.py
```

### Browser Extension Setup

```bash
# Download Metamask extension for development
mkdir -p extensions
cd extensions

# Download from Chrome Web Store (development version)
# Or build from source for custom modifications
git clone https://github.com/MetaMask/metamask-extension.git
cd metamask-extension
npm install
npm run build:dev
```

### API Testing

```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/v1/health

# Test wallet connection
curl -X POST http://localhost:8000/api/v1/wallet/connect \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'

# Test with authentication
curl -X GET http://localhost:8000/api/v1/wallet/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Testing Framework

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_wallet_manager.py
│   ├── test_transaction_handler.py
│   ├── test_security_manager.py
│   └── test_browser_controller.py
├── integration/             # Integration tests
│   ├── test_metamask_workflows.py
│   ├── test_api_endpoints.py
│   └── test_security_integration.py
├── e2e/                     # End-to-end tests
│   ├── test_full_workflow.py
│   └── test_browser_automation.py
├── fixtures/                # Test data and fixtures
│   ├── wallet_data.json
│   └── transaction_samples.json
└── conftest.py             # Pytest configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src/services/metamask_integration --cov-report=html

# Run specific test file
pytest tests/unit/test_wallet_manager.py

# Run with verbose output
pytest -v -s

# Run tests matching pattern
pytest -k "test_wallet_connect"
```

### Test Configuration

```python
# conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.services.metamask_integration.database import get_database
from src.services.metamask_integration.config import Settings

@pytest.fixture
def settings():
    return Settings(
        environment="test",
        database_url="sqlite:///test.db",
        redis_url="redis://localhost:6379/15",
        jwt_secret="test-secret"
    )

@pytest.fixture
async def db_session():
    # Create test database session
    engine = create_async_engine("sqlite+aiosqlite:///test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_browser():
    browser = AsyncMock()
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    return browser

@pytest.fixture
def mock_metamask_client():
    client = MagicMock()
    client.connect_wallet = AsyncMock()
    client.send_transaction = AsyncMock()
    client.get_balance = AsyncMock()
    return client
```

### Unit Test Examples

```python
# tests/unit/test_wallet_manager.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.metamask_integration.wallet_manager import WalletManager

class TestWalletManager:
    @pytest.fixture
    def wallet_manager(self, mock_metamask_client, db_session):
        return WalletManager(
            metamask_client=mock_metamask_client,
            db_session=db_session
        )
    
    async def test_connect_wallet_success(self, wallet_manager, mock_metamask_client):
        # Arrange
        user_id = "test-user-123"
        wallet_address = "0x742d35Cc6Bf8fE8a4C2C85b2b8b8b8b8b8b8b8b8"
        mock_metamask_client.connect_wallet.return_value = wallet_address
        
        # Act
        result = await wallet_manager.connect_wallet(user_id)
        
        # Assert
        assert result["wallet_address"] == wallet_address
        assert result["status"] == "connected"
        mock_metamask_client.connect_wallet.assert_called_once()
    
    async def test_connect_wallet_failure(self, wallet_manager, mock_metamask_client):
        # Arrange
        user_id = "test-user-123"
        mock_metamask_client.connect_wallet.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Connection failed"):
            await wallet_manager.connect_wallet(user_id)
    
    async def test_get_wallet_balance(self, wallet_manager, mock_metamask_client):
        # Arrange
        wallet_address = "0x742d35Cc6Bf8fE8a4C2C85b2b8b8b8b8b8b8b8b8"
        expected_balance = "1.5"
        mock_metamask_client.get_balance.return_value = expected_balance
        
        # Act
        balance = await wallet_manager.get_balance(wallet_address)
        
        # Assert
        assert balance == expected_balance
        mock_metamask_client.get_balance.assert_called_once_with(wallet_address)
```

### Integration Test Examples

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from src.services.metamask_integration.api import app

class TestAPIEndpoints:
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    async def test_health_endpoint(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    async def test_wallet_connect_endpoint(self, client):
        payload = {"user_id": "test-user-123"}
        response = await client.post("/api/v1/wallet/connect", json=payload)
        assert response.status_code == 200
        assert "session_token" in response.json()
    
    async def test_unauthorized_access(self, client):
        response = await client.get("/api/v1/wallet/status")
        assert response.status_code == 401
    
    @pytest.mark.parametrize("invalid_payload", [
        {},
        {"user_id": ""},
        {"user_id": None},
        {"invalid_field": "value"}
    ])
    async def test_invalid_wallet_connect_payload(self, client, invalid_payload):
        response = await client.post("/api/v1/wallet/connect", json=invalid_payload)
        assert response.status_code == 422
```

### End-to-End Test Examples

```python
# tests/e2e/test_full_workflow.py
import pytest
from playwright.async_api import async_playwright

class TestFullWorkflow:
    @pytest.fixture
    async def browser_context(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            yield context
            await browser.close()
    
    async def test_complete_wallet_workflow(self, browser_context):
        # This test requires a running development server
        page = await browser_context.new_page()
        
        # Navigate to application
        await page.goto("http://localhost:3000")
        
        # Click connect wallet button
        await page.click('[data-testid="connect-wallet"]')
        
        # Wait for Metamask popup and handle it
        # Note: This requires proper Metamask extension setup
        await page.wait_for_selector('[data-testid="wallet-connected"]')
        
        # Verify wallet connection
        wallet_address = await page.text_content('[data-testid="wallet-address"]')
        assert wallet_address.startswith("0x")
        
        # Test transaction flow
        await page.click('[data-testid="send-transaction"]')
        await page.fill('[data-testid="recipient-address"]', "0x742d35Cc...")
        await page.fill('[data-testid="amount"]', "0.1")
        await page.click('[data-testid="confirm-transaction"]')
        
        # Wait for transaction confirmation
        await page.wait_for_selector('[data-testid="transaction-success"]')
```

---

## Code Quality Standards

### Linting and Formatting

```bash
# Install development tools
pip install black isort flake8 mypy pre-commit

# Format code
black src/ tests/
isort src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/

# Run all checks
pre-commit run --all-files
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### Code Style Guidelines

```python
# Example of well-formatted code following project standards
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .models import WalletSession
from .schemas import WalletConnectRequest, WalletConnectResponse

logger = logging.getLogger(__name__)

class WalletManager:
    """Manages wallet connections and operations.
    
    This class handles all wallet-related operations including
    connection establishment, transaction management, and
    session handling.
    """
    
    def __init__(
        self,
        metamask_client: MetamaskClient,
        db_session: AsyncSession,
        redis_client: Redis
    ) -> None:
        """Initialize the WalletManager.
        
        Args:
            metamask_client: Client for Metamask interactions
            db_session: Database session for persistence
            redis_client: Redis client for caching
        """
        self.metamask_client = metamask_client
        self.db_session = db_session
        self.redis_client = redis_client
    
    async def connect_wallet(
        self,
        request: WalletConnectRequest
    ) -> WalletConnectResponse:
        """Connect a wallet for the specified user.
        
        Args:
            request: Wallet connection request containing user details
            
        Returns:
            WalletConnectResponse with connection details
            
        Raises:
            HTTPException: If wallet connection fails
        """
        try:
            logger.info(f"Connecting wallet for user: {request.user_id}")
            
            # Validate user permissions
            await self._validate_user_permissions(request.user_id)
            
            # Establish wallet connection
            wallet_address = await self.metamask_client.connect_wallet()
            
            # Create session record
            session = await self._create_wallet_session(
                user_id=request.user_id,
                wallet_address=wallet_address
            )
            
            logger.info(f"Wallet connected successfully: {wallet_address}")
            
            return WalletConnectResponse(
                session_token=session.session_token,
                wallet_address=wallet_address,
                status="connected"
            )
            
        except Exception as e:
            logger.error(f"Wallet connection failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to connect wallet"
            )
    
    async def _validate_user_permissions(self, user_id: str) -> None:
        """Validate user has permission to connect wallet."""
        # Implementation details...
        pass
    
    async def _create_wallet_session(
        self,
        user_id: str,
        wallet_address: str
    ) -> WalletSession:
        """Create a new wallet session record."""
        # Implementation details...
        pass
```

---

## Debugging and Development Tools

### Logging Configuration

```python
# Development logging setup
import logging
import sys

def setup_development_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('development.log')
        ]
    )
    
    # Set specific loggers
    logging.getLogger('src.services.metamask_integration').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
```

### Development Utilities

```python
# scripts/dev_utils.py
import asyncio
from src.services.metamask_integration.database import get_database
from src.services.metamask_integration.models import WalletSession

async def reset_test_data():
    """Reset test data for development."""
    async with get_database() as db:
        # Clear test sessions
        await db.execute("DELETE FROM wallet_sessions WHERE user_id LIKE 'test-%'")
        await db.commit()
        print("Test data reset complete")

async def create_test_user():
    """Create a test user for development."""
    # Implementation for creating test data
    pass

if __name__ == "__main__":
    asyncio.run(reset_test_data())
```

### Browser Debugging

```python
# Enable browser debugging in development
BROWSER_CONFIG = {
    "headless": False,  # Show browser window
    "devtools": True,   # Open DevTools
    "slow_mo": 1000,    # Slow down operations
    "args": [
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor"
    ]
}
```

---

## Contribution Guidelines

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/wallet-connection-improvements

# Make changes and commit
git add .
git commit -m "feat: improve wallet connection error handling"

# Push and create pull request
git push origin feature/wallet-connection-improvements
```

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks

**Examples:**
```
feat(wallet): add support for multiple wallet providers
fix(security): resolve JWT token validation issue
docs(api): update endpoint documentation
test(integration): add wallet connection tests
```

### Pull Request Process

1. **Create Feature Branch**: Branch from `main` for new features
2. **Write Tests**: Ensure adequate test coverage
3. **Update Documentation**: Update relevant documentation
4. **Run Quality Checks**: Ensure all linting and tests pass
5. **Create Pull Request**: Use the provided template
6. **Code Review**: Address reviewer feedback
7. **Merge**: Squash and merge after approval

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Security considerations are addressed
- [ ] Performance impact is considered
- [ ] Error handling is appropriate
- [ ] Logging is adequate

---

## Release Process

### Version Management

```bash
# Update version
bump2version patch  # 1.0.0 -> 1.0.1
bump2version minor  # 1.0.1 -> 1.1.0
bump2version major  # 1.1.0 -> 2.0.0

# Create release tag
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
```

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Security scan completed
- [ ] Performance benchmarks meet requirements
- [ ] Database migrations tested
- [ ] Deployment scripts updated
- [ ] Monitoring alerts configured

---

## Development Best Practices

### Security Considerations

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all inputs
- Implement proper error handling
- Use secure communication protocols
- Regular dependency updates

### Performance Guidelines

- Use async/await for I/O operations
- Implement proper caching strategies
- Monitor database query performance
- Use connection pooling
- Implement rate limiting
- Profile critical code paths

### Testing Best Practices

- Write tests before implementing features (TDD)
- Maintain high test coverage (>90%)
- Use meaningful test names
- Test edge cases and error conditions
- Mock external dependencies
- Use fixtures for test data

---

*This developer guide provides comprehensive instructions for contributing to the Metamask Integration Service. For deployment procedures, see [Deployment Guide](1_metamask_deployment_guide.md). For troubleshooting development issues, see [Troubleshooting Guide](3_metamask_troubleshooting_guide.md).*