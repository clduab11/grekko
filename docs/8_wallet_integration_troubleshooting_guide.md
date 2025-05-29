# Wallet Integration Troubleshooting Guide

This document provides comprehensive troubleshooting guidance for common issues encountered with the Grekko wallet integration system, along with debugging techniques and resolution procedures.

## Table of Contents

1. [Common Connection Issues](#common-connection-issues)
2. [Provider-Specific Problems](#provider-specific-problems)
3. [Transaction Failures](#transaction-failures)
4. [Balance and Display Issues](#balance-and-display-issues)
5. [Network and Chain Issues](#network-and-chain-issues)
6. [Debugging Techniques](#debugging-techniques)
7. [Error Recovery Procedures](#error-recovery-procedures)
8. [Performance Issues](#performance-issues)
9. [Security Considerations](#security-considerations)
10. [Getting Help](#getting-help)

---

## Common Connection Issues

### Issue: Wallet Connection Fails

**Symptoms:**
- "Connect Wallet" button unresponsive
- Error message: "Failed to connect to wallet"
- Connection modal appears but nothing happens

**Causes & Solutions:**

#### 1. Browser Extension Not Installed

```javascript
// Check if MetaMask is installed
if (typeof window.ethereum === 'undefined') {
  throw new Error('MetaMask not installed. Please install MetaMask extension.');
}

// Check if Coinbase Wallet is installed
if (typeof window.ethereum === 'undefined' || !window.ethereum.isCoinbaseWallet) {
  throw new Error('Coinbase Wallet not installed.');
}
```

**Resolution:**
- Install the required wallet extension
- Refresh the page after installation
- Clear browser cache if issues persist

#### 2. Extension Not Enabled

```javascript
// Check if extension is enabled
const accounts = await window.ethereum.request({ 
  method: 'eth_accounts' 
});

if (accounts.length === 0) {
  // Request account access
  await window.ethereum.request({ 
    method: 'eth_requestAccounts' 
  });
}
```

**Resolution:**
- Open wallet extension
- Ensure extension is unlocked
- Grant permission to connect accounts

#### 3. Network Connection Issues

```python
# Backend: Check network connectivity
async def test_network_connection():
    try:
        response = await aiohttp.get('https://eth-mainnet.alchemyapi.io/v2/demo')
        return response.status == 200
    except Exception as e:
        logger.error(f"Network connection failed: {e}")
        return False
```

**Resolution:**
- Check internet connectivity
- Verify RPC endpoint accessibility
- Try alternative RPC providers

### Issue: Connection Drops Unexpectedly

**Symptoms:**
- Wallet shows as connected but operations fail
- User redirected to connection screen repeatedly

**Debugging Steps:**

```javascript
// Monitor connection state
window.ethereum.on('accountsChanged', (accounts) => {
  if (accounts.length === 0) {
    console.log('Wallet disconnected');
    dispatch(disconnectWallet());
  }
});

window.ethereum.on('chainChanged', (chainId) => {
  console.log('Network changed:', chainId);
  // Reload the page or update network state
  window.location.reload();
});
```

**Resolution:**
- Implement connection state monitoring
- Add automatic reconnection logic
- Store connection state in localStorage

---

## Provider-Specific Problems

### MetaMask Issues

#### Issue: MetaMask Not Detected

```javascript
// Robust MetaMask detection
const detectMetaMask = () => {
  if (window.ethereum) {
    if (window.ethereum.isMetaMask) {
      return true;
    }
    // Check for MetaMask in multi-wallet scenarios
    if (window.ethereum.providers) {
      return window.ethereum.providers.some(p => p.isMetaMask);
    }
  }
  return false;
};
```

#### Issue: Wrong Network

```javascript
// Check and switch network
const switchToEthereum = async () => {
  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: '0x1' }], // Ethereum mainnet
    });
  } catch (switchError) {
    // Network might not be added to MetaMask
    if (switchError.code === 4902) {
      await addEthereumChain();
    }
  }
};
```

### Coinbase Wallet Issues

#### Issue: Mobile vs Desktop Differences

```javascript
// Handle different Coinbase Wallet environments
const connectCoinbaseWallet = async () => {
  if (window.ethereum?.isCoinbaseWallet) {
    // Browser extension
    return connectViaBrowserExtension();
  } else {
    // WalletLink for mobile
    return connectViaWalletLink();
  }
};
```

---

## Transaction Failures

### Issue: Transaction Rejected by User

**Error:** `User rejected the request`

```typescript
// Handle user rejection gracefully
const handleTransactionRequest = async (txData: TransactionData) => {
  try {
    const txHash = await walletProvider.sendTransaction(txData);
    return txHash;
  } catch (error) {
    if (error.code === 4001) {
      // User rejected transaction
      dispatch(setError('Transaction was cancelled by user'));
      return null;
    }
    throw error;
  }
};
```

### Issue: Insufficient Gas

**Error:** `Gas limit too low` or `Out of gas`

```javascript
// Estimate gas with buffer
const estimateGasWithBuffer = async (transaction) => {
  const gasEstimate = await web3.eth.estimateGas(transaction);
  return Math.floor(gasEstimate * 1.2); // 20% buffer
};

// Use dynamic gas pricing
const getGasPrice = async () => {
  const gasPrice = await web3.eth.getGasPrice();
  return Math.floor(gasPrice * 1.1); // 10% above current price
};
```

### Issue: Nonce Too Low

**Error:** `Nonce too low`

```python
# Backend: Manage nonce correctly
class NonceManager:
    def __init__(self):
        self.pending_nonces = {}
    
    async def get_next_nonce(self, address: str) -> int:
        # Get confirmed nonce
        confirmed_nonce = await web3.eth.get_transaction_count(address)
        
        # Track pending transactions
        pending_count = self.pending_nonces.get(address, 0)
        next_nonce = confirmed_nonce + pending_count
        
        self.pending_nonces[address] = pending_count + 1
        return next_nonce
```

---

## Balance and Display Issues

### Issue: Balance Not Updating

**Symptoms:**
- Balance shows as 0 or outdated value
- Token balances missing

**Debugging:**

```typescript
// Debug balance fetching
const debugBalanceCheck = async (address: string) => {
  console.log('Checking balance for:', address);
  
  try {
    // Check native balance
    const nativeBalance = await web3.eth.getBalance(address);
    console.log('Native balance (wei):', nativeBalance);
    console.log('Native balance (ETH):', web3.utils.fromWei(nativeBalance, 'ether'));
    
    // Check token balances
    const tokenContract = new web3.eth.Contract(ERC20_ABI, TOKEN_ADDRESS);
    const tokenBalance = await tokenContract.methods.balanceOf(address).call();
    console.log('Token balance:', tokenBalance);
    
  } catch (error) {
    console.error('Balance check failed:', error);
  }
};
```

**Resolution:**

```typescript
// Implement robust balance checking
const checkBalanceWithRetry = async (address: string, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const balance = await getBalance(address);
      return balance;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

### Issue: Token Balance Incorrect

```javascript
// Verify token contract and decimals
const getTokenBalance = async (tokenAddress, walletAddress) => {
  const contract = new web3.eth.Contract(ERC20_ABI, tokenAddress);
  
  // Get decimals for proper formatting
  const decimals = await contract.methods.decimals().call();
  const balance = await contract.methods.balanceOf(walletAddress).call();
  
  // Format balance correctly
  return (balance / Math.pow(10, decimals)).toFixed(4);
};
```

---

## Network and Chain Issues

### Issue: Wrong Network Connected

**Symptoms:**
- Transactions fail with network errors
- Balance shows 0 on wrong network

**Detection:**

```javascript
// Monitor and validate network
const validateNetwork = async () => {
  const chainId = await window.ethereum.request({ method: 'eth_chainId' });
  const expectedChainId = '0x1'; // Ethereum mainnet
  
  if (chainId !== expectedChainId) {
    throw new Error(`Wrong network. Expected: ${expectedChainId}, Got: ${chainId}`);
  }
};
```

**Resolution:**

```javascript
// Auto-switch to correct network
const ensureCorrectNetwork = async () => {
  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: '0x1' }],
    });
  } catch (error) {
    if (error.code === 4902) {
      // Add network if not present
      await window.ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [{
          chainId: '0x1',
          chainName: 'Ethereum Mainnet',
          rpcUrls: ['https://mainnet.infura.io/v3/YOUR_KEY'],
          nativeCurrency: {
            name: 'Ethereum',
            symbol: 'ETH',
            decimals: 18
          }
        }]
      });
    }
  }
};
```

---

## Debugging Techniques

### Enable Debug Logging

```typescript
// Frontend debug configuration
const DEBUG_WALLET = process.env.NODE_ENV === 'development';

const debugLog = (message: string, data?: any) => {
  if (DEBUG_WALLET) {
    console.log(`[WALLET DEBUG] ${message}`, data);
  }
};

// Usage
debugLog('Attempting wallet connection', { provider: 'metamask' });
```

```python
# Backend debug logging
import logging

logger = logging.getLogger('wallet_integration')
logger.setLevel(logging.DEBUG if os.getenv('DEBUG') else logging.INFO)

# Add detailed logging
def debug_wallet_operation(operation: str, data: dict):
    logger.debug(f"Wallet operation: {operation}", extra=data)
```

### Monitor Network Requests

```javascript
// Monitor Web3 requests
const originalRequest = window.ethereum.request;
window.ethereum.request = async (args) => {
  console.log('Web3 Request:', args);
  try {
    const result = await originalRequest(args);
    console.log('Web3 Response:', result);
    return result;
  } catch (error) {
    console.error('Web3 Error:', error);
    throw error;
  }
};
```

### State Inspection Tools

```typescript
// Redux DevTools for state debugging
const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV !== 'production',
});

// Add state logging middleware
const stateLogger = (store) => (next) => (action) => {
  if (action.type.startsWith('wallet/')) {
    console.log('Wallet Action:', action);
    console.log('Previous State:', store.getState().wallet);
  }
  
  const result = next(action);
  
  if (action.type.startsWith('wallet/')) {
    console.log('New State:', store.getState().wallet);
  }
  
  return result;
};
```

---

## Error Recovery Procedures

### Automatic Recovery

```typescript
// Implement automatic error recovery
const withRetry = async <T>(
  operation: () => Promise<T>, 
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      console.log(`Attempt ${attempt} failed, retrying in ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2; // Exponential backoff
    }
  }
  throw new Error('All retry attempts failed');
};
```

### Connection Recovery

```typescript
// Implement connection recovery
const recoverConnection = async () => {
  try {
    // Clear existing state
    dispatch(disconnectWallet());
    
    // Wait before attempting reconnection
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Attempt to reconnect
    const provider = localStorage.getItem('last_wallet_provider');
    if (provider) {
      await dispatch(connectWalletAsync(provider as WalletProviderType));
    }
  } catch (error) {
    console.error('Connection recovery failed:', error);
  }
};
```

---

## Performance Issues

### Issue: Slow Balance Updates

**Optimization:**

```typescript
// Batch balance checks
const batchBalanceCheck = async (addresses: string[]) => {
  const balancePromises = addresses.map(address => 
    checkBalanceWithRetry(address)
  );
  
  const results = await Promise.allSettled(balancePromises);
  
  return results.map((result, index) => ({
    address: addresses[index],
    balance: result.status === 'fulfilled' ? result.value : null,
    error: result.status === 'rejected' ? result.reason : null
  }));
};
```

### Issue: Memory Leaks

**Prevention:**

```typescript
// Cleanup event listeners
useEffect(() => {
  const handleAccountsChanged = (accounts: string[]) => {
    // Handle account change
  };
  
  window.ethereum?.on('accountsChanged', handleAccountsChanged);
  
  return () => {
    window.ethereum?.removeListener('accountsChanged', handleAccountsChanged);
  };
}, []);
```

---

## Security Considerations

### Validate All Inputs

```typescript
// Validate addresses
const isValidAddress = (address: string): boolean => {
  return /^0x[a-fA-F0-9]{40}$/.test(address);
};

// Validate transaction data
const validateTransaction = (tx: TransactionData): void => {
  if (!isValidAddress(tx.to)) {
    throw new Error('Invalid recipient address');
  }
  
  if (parseFloat(tx.value) <= 0) {
    throw new Error('Invalid transaction amount');
  }
};
```

### Secure Error Handling

```typescript
// Don't expose sensitive information in errors
const sanitizeError = (error: any): string => {
  const sensitivePatterns = [
    /private.*key/i,
    /mnemonic/i,
    /seed.*phrase/i
  ];
  
  let message = error.message || 'Unknown error';
  
  sensitivePatterns.forEach(pattern => {
    message = message.replace(pattern, '[REDACTED]');
  });
  
  return message;
};
```

---

## Getting Help

### Collect Debug Information

```typescript
// Debug information collection
const collectDebugInfo = async () => {
  const info = {
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    walletState: store.getState().wallet,
    networkInfo: {
      chainId: await window.ethereum?.request({ method: 'eth_chainId' }),
      accounts: await window.ethereum?.request({ method: 'eth_accounts' })
    },
    errors: getRecentErrors(),
    version: process.env.REACT_APP_VERSION
  };
  
  // Remove sensitive data
  delete info.walletState.privateKey;
  
  return info;
};
```

### Support Channels

- **GitHub Issues**: [Grekko Wallet Integration Issues](https://github.com/grekko/wallet-integration/issues)
- **Discord**: [Grekko Community](https://discord.gg/grekko)
- **Documentation**: [Complete Integration Guide](5_wallet_integration_implementation_guide.md)

### Before Reporting Issues

1. **Check existing documentation**
2. **Verify latest version usage**
3. **Collect debug information**
4. **Provide reproduction steps**
5. **Include error logs and screenshots**

---

## Quick Reference

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 4001 | User rejected request | User action required |
| 4100 | Unauthorized | Check permissions |
| 4200 | Unsupported method | Update wallet/provider |
| 4900 | Disconnected | Reconnect wallet |
| 4902 | Unrecognized chain | Add/switch network |
| -32603 | Internal error | Check RPC connection |

### Emergency Recovery

```bash
# Clear browser cache and data
# Chrome: Settings > Privacy > Clear browsing data
# Firefox: Settings > Privacy > Clear Data

# Reset wallet connection
localStorage.removeItem('wallet_connection_state');
sessionStorage.clear();

# Restart browser extension
# Disable and re-enable wallet extension
```

---

## References

- [Implementation Guide](5_wallet_integration_implementation_guide.md)
- [API Reference](6_wallet_integration_api_reference.md)
- [Frontend Guide](7_wallet_integration_frontend_guide.md)
- [MetaMask Documentation](https://docs.metamask.io/)
- [Coinbase Wallet Documentation](https://docs.cloud.coinbase.com/wallet-sdk/docs/)