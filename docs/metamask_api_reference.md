# Metamask Integration API Reference

This document provides comprehensive API documentation for the Metamask Integration Service, including authentication, endpoints, request/response schemas, and security considerations.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base Configuration](#base-configuration)
- [API Endpoints](#api-endpoints)
- [Request/Response Schemas](#requestresponse-schemas)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Security Considerations](#security-considerations)

---

## Overview

The Metamask Integration API provides secure endpoints for wallet operations, transaction management, and network switching. Built with FastAPI, it implements enterprise-grade security features including JWT authentication, RBAC authorization, rate limiting, and comprehensive input validation.

**API Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Content Type:** `application/json`

---

## Authentication

### JWT Token Authentication

All endpoints require JWT bearer token authentication with role-based access control (RBAC).

#### Token Format
```http
Authorization: Bearer <jwt_token>
```

#### Token Payload Structure
```json
{
  "sub": "user_id",
  "roles": ["user", "admin"],
  "exp": 1234567890,
  "iat": 1234567800
}
```

#### Required Roles
- **user**: Basic wallet operations (connect, status, transactions)
- **admin**: Administrative operations and configuration

### Session Management

Session tokens are required for wallet operations and are validated against the SecurityManager.

```python
# Session creation example
session_token = security_manager.create_session(user_id)
```

---

## Base Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | Yes | - | JWT signing secret (production) |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection for rate limiting |
| `METAMASK_EXTENSION_PATH` | No | `/opt/metamask` | Path to Metamask extension |

### Rate Limiting Configuration

- **Default Rate Limit:** 10 requests per minute
- **Wallet Connect:** 5 requests per minute
- **Transaction Operations:** 5 requests per minute
- **Network Switch:** 3 requests per minute

---

## API Endpoints

### Health Check

#### `GET /api/v1/health`

Health check endpoint for service monitoring.

**Authentication:** None required

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

---

### API Version

#### `GET /api/v1/`

Returns API version information.

**Authentication:** None required

**Response:**
```json
{
  "version": "1.0.0",
  "service": "metamask_integration"
}
```

---

### Wallet Operations

#### `POST /api/v1/wallet/connect`

Establishes a secure connection to a Metamask wallet.

**Authentication:** Required (user role)  
**Rate Limit:** 5 requests per minute

**Request Body:**
```json
{
  "session_token": "uuid-session-token",
  "wallet_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123"
}
```

**Response:**
```json
{
  "status": "connected",
  "wallet": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123"
}
```

**Status Codes:**
- `200 OK`: Wallet connected successfully
- `400 Bad Request`: Invalid session or wallet address
- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`: Insufficient privileges
- `429 Too Many Requests`: Rate limit exceeded

---

#### `GET /api/v1/wallet/status`

Retrieves the current status of the connected wallet.

**Authentication:** Required (user role)  
**Rate Limit:** 10 requests per minute

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_token` | string | Yes | Valid session token |

**Response:**
```json
{
  "status": "active"
}
```

**Status Codes:**
- `200 OK`: Status retrieved successfully
- `401 Unauthorized`: Invalid session or JWT token
- `429 Too Many Requests`: Rate limit exceeded

---

### Transaction Operations

#### `POST /api/v1/transaction/prepare`

Prepares a transaction for signing with security validation.

**Authentication:** Required (user role)  
**Rate Limit:** 5 requests per minute

**Request Body:**
```json
{
  "session_token": "uuid-session-token",
  "to": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
  "value": 1000000000000000000,
  "gas": 21000,
  "gasPrice": 20000000000,
  "data": "0x"
}
```

**Response:**
```json
{
  "status": "prepared",
  "transaction": {
    "to": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
    "value": 1000000000000000000,
    "gas": 21000,
    "gasPrice": 20000000000,
    "data": "0x"
  }
}
```

**Status Codes:**
- `200 OK`: Transaction prepared successfully
- `400 Bad Request`: Invalid transaction parameters or security violation
- `401 Unauthorized`: Invalid session or JWT token
- `429 Too Many Requests`: Rate limit exceeded

---

#### `POST /api/v1/transaction/sign`

Signs a prepared transaction using Metamask.

**Authentication:** Required (user role)  
**Rate Limit:** 5 requests per minute

**Request Body:**
```json
{
  "session_token": "uuid-session-token",
  "transaction": {
    "to": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123",
    "value": 1000000000000000000,
    "gas": 21000,
    "gasPrice": 20000000000,
    "data": "0x"
  }
}
```

**Response:**
```json
{
  "status": "signed"
}
```

**Status Codes:**
- `200 OK`: Transaction signed successfully
- `400 Bad Request`: Invalid transaction or security violation
- `401 Unauthorized`: Invalid session or JWT token
- `429 Too Many Requests`: Rate limit exceeded

---

### Network Operations

#### `POST /api/v1/network/switch`

Switches the active network in Metamask.

**Authentication:** Required (user role)  
**Rate Limit:** 3 requests per minute

**Request Body:**
```json
{
  "session_token": "uuid-session-token",
  "network": "mainnet"
}
```

**Response:**
```json
{
  "status": "switched",
  "network": "mainnet"
}
```

**Status Codes:**
- `200 OK`: Network switched successfully
- `401 Unauthorized`: Invalid session or JWT token
- `429 Too Many Requests`: Rate limit exceeded

---

## Request/Response Schemas

### Pydantic Models

#### WalletConnectRequest
```python
class WalletConnectRequest(BaseModel):
    session_token: str = Field(..., min_length=32, max_length=128)
    wallet_address: str = Field(..., regex="^0x[a-fA-F0-9]{40}$")
```

#### TransactionPrepareRequest
```python
class TransactionPrepareRequest(BaseModel):
    session_token: str = Field(..., min_length=32, max_length=128)
    to: str = Field(..., regex="^0x[a-fA-F0-9]{40}$")
    value: int = Field(..., ge=0)
    gas: int = Field(..., ge=21000)
    gasPrice: int = Field(..., ge=0)
    data: Optional[str] = Field(default="0x")
```

#### NetworkSwitchRequest
```python
class NetworkSwitchRequest(BaseModel):
    session_token: str = Field(..., min_length=32, max_length=128)
    network: str = Field(..., min_length=1, max_length=32)
```

---

## Error Handling

### Error Response Format

All API errors follow a consistent response format:

```json
{
  "detail": "Error description"
}
```

### Common Error Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| `400 Bad Request` | Invalid request parameters | Malformed data, validation failures |
| `401 Unauthorized` | Authentication failure | Invalid/expired JWT token, invalid session |
| `403 Forbidden` | Authorization failure | Insufficient role permissions |
| `429 Too Many Requests` | Rate limit exceeded | Too many requests in time window |
| `500 Internal Server Error` | Server error | Unexpected server-side errors |

### Security-Related Errors

- **SecurityViolationError**: Transaction validation failures
- **RateLimitExceededError**: Rate limiting violations
- **PhishingDetectedError**: Malicious site detection
- **InvalidSessionError**: Session validation failures
- **SuspiciousActivityError**: Unusual activity patterns

---

## Rate Limiting

### Implementation

Rate limiting is implemented using Redis with the `slowapi` library, tracking requests by client IP address.

### Limits by Endpoint

| Endpoint | Limit | Window |
|----------|-------|--------|
| Default | 10 requests | 1 minute |
| `/wallet/connect` | 5 requests | 1 minute |
| `/wallet/status` | 10 requests | 1 minute |
| `/transaction/prepare` | 5 requests | 1 minute |
| `/transaction/sign` | 5 requests | 1 minute |
| `/network/switch` | 3 requests | 1 minute |

### Rate Limit Headers

Response headers include rate limiting information:

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1234567890
```

---

## Security Considerations

### OWASP API Security

The API implements OWASP API Security Top 10 best practices:

1. **Broken Object Level Authorization**: Role-based access control
2. **Broken User Authentication**: JWT with proper validation
3. **Excessive Data Exposure**: Minimal response data
4. **Lack of Resources & Rate Limiting**: Comprehensive rate limiting
5. **Broken Function Level Authorization**: Endpoint-level role checks
6. **Mass Assignment**: Pydantic validation with explicit fields
7. **Security Misconfiguration**: Secure defaults and validation
8. **Injection**: Input sanitization and validation
9. **Improper Assets Management**: API versioning and documentation
10. **Insufficient Logging & Monitoring**: Security event logging

### Input Validation

All inputs are validated using Pydantic models with:
- Type checking
- Length constraints
- Format validation (regex patterns)
- Range validation

### Security Features

- **CORS Configuration**: Configurable allowed origins
- **HTTPS Enforcement**: TLS/SSL required in production
- **Session Timeout**: Configurable session expiration
- **Transaction Limits**: Maximum value and gas price limits
- **Phishing Protection**: URL validation and known threat detection
- **Audit Logging**: Comprehensive security event logging

### Production Hardening

For production deployment:

1. Set secure `JWT_SECRET` environment variable
2. Restrict `ALLOWED_ORIGINS` to specific domains
3. Enable HTTPS/TLS encryption
4. Configure proper Redis security
5. Implement network-level security (firewalls, VPNs)
6. Regular security audits and vulnerability assessments

---

## Usage Examples

### Python Client Example

```python
import requests
import jwt

# JWT token creation (server-side)
token = jwt.encode({
    "sub": "user123",
    "roles": ["user"],
    "exp": datetime.utcnow() + timedelta(hours=1)
}, JWT_SECRET, algorithm="HS256")

# API request
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Connect wallet
response = requests.post(
    "https://api.example.com/api/v1/wallet/connect",
    headers=headers,
    json={
        "session_token": "session-uuid-here",
        "wallet_address": "0x742d35Cc6634C0532925a3b8D400768E5A9BA123"
    }
)

print(response.json())
```

### cURL Example

```bash
# Wallet status check
curl -X GET \
  "https://api.example.com/api/v1/wallet/status?session_token=session-uuid" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

---

*This documentation is for Metamask Integration API v1.0.0. For integration guides and deployment instructions, see the related documentation files.*