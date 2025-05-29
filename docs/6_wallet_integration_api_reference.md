# Wallet Integration API Reference

This document provides comprehensive API documentation for the Grekko wallet integration system, covering backend endpoints, wallet provider methods, and integration patterns.

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Wallet Provider API](#wallet-provider-api)
4. [Wallet Manager API](#wallet-manager-api)
5. [HTTP Endpoints](#http-endpoints)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [SDK Examples](#sdk-examples)

---

## API Overview

The Grekko wallet integration API provides secure, non-custodial wallet management capabilities through RESTful endpoints and Python SDK interfaces.

### Base URL

```
https://api.grekko.io/v1/wallet
```

### Supported Protocols

- **HTTP/HTTPS**: REST API endpoints
- **WebSocket**: Real-time wallet events
- **gRPC**: High-performance internal communication

### API Versioning

All APIs are versioned using URL path versioning:
- Current version: `v1`
- Backward compatibility: Maintained for 12 months
- Deprecation notice: 3 months advance warning

---

## Authentication

### API Key Authentication

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Wallet Signature Authentication

For wallet-specific operations, signatures are required:

```python
# Generate signature for wallet authentication
import hashlib
import hmac

def generate_wallet_signature(message: str, private_key: str) -> str:
    """Generate HMAC-SHA256 signature for wallet operations"""
    return hmac.new(
        private_key.encode(),
        message.encode(), 
        hashlib.sha256
    ).hexdigest()
```

---

## Wallet Provider API

### WalletProvider Interface

Base abstract class for all wallet implementations.

#### `connect(connection_params: Dict[str, Any]) -> bool`

Establishes connection to a wallet provider.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `network` | `str` | Yes | Blockchain network identifier |
| `chain_id` | `int` | Yes | Chain ID for the network |
| `address` | `str` | No | Wallet address (if known) |
| `timeout` | `int` | No | Connection timeout in seconds (default: 30) |

**Returns:**
- `bool`: True if connection successful, False otherwise

**Example:**

```python
# Connect to MetaMask provider
metamask = MetaMaskProvider()
success = metamask.connect({
    "network": "ethereum",
    "chain_id": 1,
    "address": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
    "timeout": 30
})
```

#### `is_connected() -> bool`

Checks current connection status.

**Returns:**
- `bool`: True if wallet is connected

**Example:**

```python
if metamask.is_connected():
    print("Wallet is connected")
```

#### `get_address() -> Optional[str]`

Retrieves the wallet's public address.

**Returns:**
- `Optional[str]`: Wallet address or None if not available

**Example:**

```python
address = metamask.get_address()
# Returns: "0x742d35Cc6635C0532925a3b8D431d3C348739C4E"
```

#### `sign_transaction(transaction_data: Dict[str, Any]) -> Optional[str]`

Signs a transaction using the wallet's private key.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | `str` | Yes | Recipient address |
| `value` | `str` | Yes | Transaction value in wei |
| `gas` | `str` | Yes | Gas limit |
| `gasPrice` | `str` | Yes | Gas price in wei |
| `nonce` | `int` | Yes | Transaction nonce |
| `data` | `str` | No | Transaction data |

**Returns:**
- `Optional[str]`: Signed transaction hash or None if failed

**Example:**

```python
signed_tx = metamask.sign_transaction({
    "to": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
    "value": "1000000000000000000",  # 1 ETH in wei
    "gas": "21000",
    "gasPrice": "20000000000",  # 20 gwei
    "nonce": 42,
    "data": "0x"
})
```

#### `send_transaction(transaction_data: Dict[str, Any]) -> Optional[str]`

Sends a transaction through the wallet provider.

**Parameters:**
- Same as `sign_transaction`

**Returns:**
- `Optional[str]`: Transaction hash or None if failed

---

## Wallet Manager API

### Initialization

```python
from src.execution.decentralized_execution.wallet_manager import WalletManager
from src.utils.credentials_manager import CredentialsManager

# Initialize wallet manager
credentials_manager = CredentialsManager()
wallet_manager = WalletManager(
    credentials_manager=credentials_manager,
    config={
        "rotation_policies": {
            "ethereum": {
                "policy": "trade_based",
                "trades_threshold": 10
            }
        }
    }
)
```

### Core Methods

#### `register_external_provider(provider_name: str, provider_instance: WalletProvider) -> None`

Registers an external wallet provider.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider_name` | `str` | Yes | Provider identifier (e.g., "metamask") |
| `provider_instance` | `WalletProvider` | Yes | Wallet provider instance |

**Example:**

```python
metamask_provider = MetaMaskProvider()
wallet_manager.register_external_provider("metamask", metamask_provider)
```

#### `add_wallet(chain: str, wallet_info: Dict[str, Any], private_key: Optional[str] = None) -> bool`

Adds a new wallet to the manager.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | `str` | Yes | Blockchain network |
| `wallet_info` | `Dict` | Yes | Wallet metadata |
| `private_key` | `str` | No | Private key for hot wallets |

**Wallet Info Schema:**

```python
{
    "address": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
    "type": "external",  # "hot", "hardware", "multisig", "external"
    "name": "MetaMask Wallet",
    "network": "ethereum"
}
```

#### `get_wallet(chain: str, rotation_policy: Optional[str] = None) -> Optional[Dict[str, Any]]`

Retrieves the active wallet for a blockchain.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | `str` | Yes | Blockchain network |
| `rotation_policy` | `str` | No | Override rotation policy |

**Returns:**

```python
{
    "address": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
    "type": "external",
    "name": "MetaMask Wallet",
    "balance": {
        "native": 1.5,
        "tokens": {
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": 1000.0
        }
    },
    "last_balance_check": 1640995200
}
```

#### `check_balances(chain: Optional[str] = None, wallets: Optional[List[Dict]] = None) -> Dict[str, Dict[str, Any]]`

Checks wallet balances across networks.

**Returns:**

```python
{
    "ethereum": {
        "0x742d35Cc6635C0532925a3b8D431d3C348739C4E": {
            "native": 1.5,
            "tokens": {
                "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": 1000.0
            }
        }
    }
}
```

---

## HTTP Endpoints

### GET /api/wallet/status

Retrieves current wallet connection status.

**Response:**

```json
{
    "connected": true,
    "provider": "metamask",
    "address": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
    "network": "ethereum",
    "balance": {
        "native": 1.5,
        "tokens": {
            "USDC": 1000.0,
            "USDT": 1000.0
        }
    }
}
```

### POST /api/wallet/connect

Initiates wallet connection process.

**Request:**

```json
{
    "provider": "metamask",
    "network": "ethereum",
    "chain_id": 1
}
```

**Response:**

```json
{
    "success": true,
    "connection_id": "conn_123456789",
    "expires_at": "2024-01-01T12:00:00Z"
}
```

### POST /api/wallet/sign-transaction

Signs a transaction using the connected wallet.

**Request:**

```json
{
    "chain": "ethereum",
    "transaction": {
        "to": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
        "value": "1000000000000000000",
        "gas": "21000",
        "gasPrice": "20000000000",
        "nonce": 42
    }
}
```

**Response:**

```json
{
    "success": true,
    "signed_transaction": "0xf86c2a85...",
    "transaction_hash": "0x123456789abcdef..."
}
```

### GET /api/wallet/balance

Retrieves wallet balance information.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `chain` | `str` | No | Specific blockchain (default: all) |
| `address` | `str` | No | Specific address (default: active) |

**Response:**

```json
{
    "ethereum": {
        "0x742d35Cc6635C0532925a3b8D431d3C348739C4E": {
            "native": {
                "symbol": "ETH",
                "balance": "1.5",
                "value_usd": "3000.00"
            },
            "tokens": [
                {
                    "contract": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "symbol": "USDC",
                    "balance": "1000.0",
                    "value_usd": "1000.00"
                }
            ]
        }
    }
}
```

### POST /api/wallet/rotate

Triggers wallet rotation for privacy.

**Request:**

```json
{
    "chain": "ethereum",
    "policy": "immediate"
}
```

**Response:**

```json
{
    "success": true,
    "previous_address": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
    "new_address": "0x123456789abcdef123456789abcdef1234567890",
    "rotation_id": "rot_123456789"
}
```

---

## Error Handling

### Error Response Format

```json
{
    "error": {
        "code": "WALLET_CONNECTION_FAILED",
        "message": "Failed to connect to MetaMask wallet",
        "details": {
            "provider": "metamask",
            "network": "ethereum",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `WALLET_NOT_CONNECTED` | 400 | Wallet is not connected |
| `INVALID_NETWORK` | 400 | Unsupported blockchain network |
| `INSUFFICIENT_BALANCE` | 400 | Insufficient wallet balance |
| `TRANSACTION_FAILED` | 400 | Transaction signing/sending failed |
| `WALLET_CONNECTION_FAILED` | 500 | Failed to establish wallet connection |
| `PROVIDER_UNAVAILABLE` | 503 | Wallet provider is unavailable |

### Error Handling Examples

```python
try:
    wallet = await wallet_manager.get_wallet("ethereum")
except WalletNotConnectedException:
    # Handle wallet not connected
    print("Please connect your wallet first")
except UnsupportedNetworkException as e:
    # Handle unsupported network
    print(f"Network {e.network} is not supported")
```

---

## Rate Limiting

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/wallet/status` | 100 requests | 1 minute |
| `/api/wallet/balance` | 50 requests | 1 minute |
| `/api/wallet/sign-transaction` | 10 requests | 1 minute |
| `/api/wallet/connect` | 5 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## SDK Examples

### Python SDK

```python
from grekko_wallet_sdk import WalletClient

# Initialize client
client = WalletClient(api_key="your-api-key")

# Connect wallet
await client.connect_wallet("metamask", {
    "network": "ethereum",
    "chain_id": 1
})

# Check balance
balance = await client.get_balance()
print(f"ETH Balance: {balance['native']['balance']}")

# Sign transaction
tx_hash = await client.sign_transaction({
    "to": "0x742d35Cc6635C0532925a3b8D431d3C348739C4E",
    "value": "1000000000000000000"
})
```

### JavaScript SDK

```javascript
import { WalletClient } from '@grekko/wallet-sdk';

// Initialize client
const client = new WalletClient({ apiKey: 'your-api-key' });

// Connect wallet
await client.connectWallet('metamask', {
    network: 'ethereum',
    chainId: 1
});

// Check balance
const balance = await client.getBalance();
console.log(`ETH Balance: ${balance.native.balance}`);

// Sign transaction
const txHash = await client.signTransaction({
    to: '0x742d35Cc6635C0532925a3b8D431d3C348739C4E',
    value: '1000000000000000000'
});
```

---

## References

- [Implementation Guide](5_wallet_integration_implementation_guide.md)
- [System Architecture](phase_4_wallet_integration_system_architecture.md)
- [Frontend Integration Guide](7_wallet_integration_frontend_guide.md)
- [Troubleshooting Guide](8_wallet_integration_troubleshooting_guide.md)