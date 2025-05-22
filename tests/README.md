# Grekko Testing Framework

This directory contains the testing framework for the Grekko cryptocurrency trading platform. The tests are structured to ensure the reliability, security, and performance of the platform.

## Test Structure

The test suite is organized into three main categories:

### 1. Unit Tests

Unit tests verify the functionality of individual components in isolation. These tests are located in the `unit/` directory and focus on:

- Component behavior
- Error handling
- Edge cases
- Proper parameter validation

### 2. Integration Tests

Integration tests verify that different components work together correctly. Located in the `integration/` directory, they test:

- Exchange connectivity
- Full trading pipeline execution
- Cross-component communication
- Error propagation between components

### 3. Simulation Tests

Simulation tests evaluate the platform's behavior in simulated market conditions. Located in the `simulation/` directory, they include:

- Backtesting of trading strategies
- Market simulation
- Performance benchmarking
- Stress testing under various market conditions

## Running Tests

### Prerequisites

Before running tests, ensure you have installed the required dependencies:

```bash
pip install -r requirements.txt
```

### Running All Tests

To run the entire test suite:

```bash
pytest tests/
```

### Running Specific Test Categories

To run only unit tests:

```bash
pytest tests/unit/
```

To run only integration tests:

```bash
pytest tests/integration/
```

To run only simulation tests:

```bash
pytest tests/simulation/
```

### Running Specific Test Files

To run tests in a specific file:

```bash
pytest tests/unit/test_risk_management.py
```

### Test Options

- `-v`: Verbose output
- `-x`: Stop after first failure
- `--pdb`: Start debugger on failures
- `--cov=src`: Generate coverage report for the `src` directory

Example:

```bash
pytest tests/ -v --cov=src
```

## Test Fixtures

Common test fixtures are defined in `conftest.py` and include:

- Mock exchange connections
- Sample market data
- Test configurations
- Mock credentials

## Writing New Tests

When adding new components to Grekko, please follow these guidelines for writing tests:

1. Create unit tests for all new functionality
2. Add integration tests for component interactions
3. Update simulation tests to evaluate real-world performance
4. Use the existing fixtures when possible
5. Follow the naming convention: `test_*.py` for files, `test_*` for functions

## Mocking External Services

Tests should not rely on external services like exchanges or APIs. Use the provided mocks:

- `mock_binance_exchange`
- `mock_credentials_manager`
- `sample_market_data`

## Continuous Integration

The test suite runs automatically on all pull requests through our CI pipeline. PRs cannot be merged until all tests pass.

## Test Coverage

We aim to maintain at least 80% test coverage for all production code. Coverage reports are generated during CI runs.