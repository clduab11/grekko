# Frontend Integration Guide

This document provides comprehensive guidance for integrating wallet functionality into React applications using Redux state management and modern UI patterns.

## Table of Contents

1. [Frontend Architecture](#frontend-architecture)
2. [Redux State Management](#redux-state-management)
3. [React Components](#react-components)
4. [Wallet Connection Flow](#wallet-connection-flow)
5. [Error Handling](#error-handling)
6. [UI/UX Best Practices](#uiux-best-practices)
7. [Performance Optimization](#performance-optimization)
8. [Testing Frontend Components](#testing-frontend-components)

---

## Frontend Architecture

### Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.2+ | Component framework |
| **Redux Toolkit** | 1.9+ | State management |
| **TypeScript** | 5.0+ | Type safety |
| **React Router** | 6.8+ | Navigation |
| **Styled Components** | 5.3+ | CSS-in-JS styling |

### Project Structure

```
frontend/src/
├── components/
│   ├── wallet/
│   │   ├── WalletConnector.tsx
│   │   ├── WalletBalance.tsx
│   │   ├── WalletModal.tsx
│   │   └── WalletStatus.tsx
│   └── layout/
│       ├── Header.tsx
│       └── MainLayout.tsx
├── store/
│   ├── store.ts
│   └── slices/
│       ├── walletSlice.ts
│       ├── tradingSlice.ts
│       └── uiSlice.ts
├── hooks/
│   ├── useWallet.ts
│   ├── useBalance.ts
│   └── useTransactions.ts
├── services/
│   ├── walletService.ts
│   └── websocketService.ts
└── types/
    ├── wallet.ts
    └── trading.ts
```

---

## Redux State Management

### Wallet State Schema

The [`walletSlice`](../frontend/src/store/slices/walletSlice.ts) manages all wallet-related state:

```typescript
interface WalletState {
  provider: WalletProviderType;
  address: string | null;
  connected: boolean;
  error: string | null;
  connecting: boolean;
  balance: TokenBalance | null;
  transactions: Transaction[];
  network: NetworkInfo | null;
}

type WalletProviderType = 'metamask' | 'coinbase' | null;

interface TokenBalance {
  native: {
    symbol: string;
    balance: string;
    valueUsd: string;
  };
  tokens: Array<{
    contract: string;
    symbol: string;
    balance: string;
    valueUsd: string;
  }>;
}
```

### Redux Actions

```typescript
// Wallet connection actions
export const {
  connectWalletStart,
  connectWalletSuccess,
  connectWalletFailure,
  disconnectWallet,
  updateBalance,
  addTransaction,
  setError,
  clearError
} = walletSlice.actions;

// Async thunks for wallet operations
export const connectWalletAsync = createAsyncThunk(
  'wallet/connect',
  async (provider: WalletProviderType, { dispatch, rejectWithValue }) => {
    try {
      dispatch(connectWalletStart(provider));
      
      const walletService = new WalletService();
      const { address, network } = await walletService.connect(provider);
      
      dispatch(connectWalletSuccess({ provider, address, network }));
      return { provider, address, network };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      dispatch(connectWalletFailure(message));
      return rejectWithValue(message);
    }
  }
);
```

### Store Configuration

```typescript
// store.ts
import { configureStore } from '@reduxjs/toolkit';
import walletSlice from './slices/walletSlice';
import tradingSlice from './slices/tradingSlice';
import uiSlice from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    wallet: walletSlice,
    trading: tradingSlice,
    ui: uiSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

---

## React Components

### WalletConnector Component

Main component for wallet connection and management:

```typescript
// components/wallet/WalletConnector.tsx
import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { connectWalletAsync, disconnectWallet } from '../../store/slices/walletSlice';
import { RootState, AppDispatch } from '../../store/store';

interface WalletConnectorProps {
  className?: string;
  showBalance?: boolean;
}

export const WalletConnector: React.FC<WalletConnectorProps> = ({
  className,
  showBalance = true
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const { connected, connecting, address, provider, error } = useSelector(
    (state: RootState) => state.wallet
  );
  const [showModal, setShowModal] = useState(false);

  const handleConnect = async (providerType: WalletProviderType) => {
    await dispatch(connectWalletAsync(providerType));
    setShowModal(false);
  };

  const handleDisconnect = () => {
    dispatch(disconnectWallet());
  };

  if (connected) {
    return (
      <div className={`wallet-connected ${className}`}>
        <div className="wallet-info">
          <span className="provider-badge">{provider}</span>
          <span className="address">{address?.slice(0, 6)}...{address?.slice(-4)}</span>
        </div>
        {showBalance && <WalletBalance />}
        <button onClick={handleDisconnect} className="disconnect-btn">
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <>
      <button 
        onClick={() => setShowModal(true)}
        disabled={connecting}
        className={`connect-wallet-btn ${className}`}
      >
        {connecting ? 'Connecting...' : 'Connect Wallet'}
      </button>
      
      {showModal && (
        <WalletModal
          onConnect={handleConnect}
          onClose={() => setShowModal(false)}
          error={error}
        />
      )}
    </>
  );
};
```

### WalletModal Component

Modal for wallet provider selection:

```typescript
// components/wallet/WalletModal.tsx
import React from 'react';
import { WalletProviderType } from '../../types/wallet';

interface WalletModalProps {
  onConnect: (provider: WalletProviderType) => void;
  onClose: () => void;
  error?: string | null;
}

export const WalletModal: React.FC<WalletModalProps> = ({
  onConnect,
  onClose,
  error
}) => {
  const walletProviders = [
    {
      name: 'MetaMask',
      id: 'metamask' as WalletProviderType,
      icon: '/icons/metamask.svg',
      description: 'Connect using MetaMask browser extension'
    },
    {
      name: 'Coinbase Wallet',
      id: 'coinbase' as WalletProviderType,
      icon: '/icons/coinbase.svg',
      description: 'Connect using Coinbase Wallet'
    }
  ];

  return (
    <div className="wallet-modal-overlay" onClick={onClose}>
      <div className="wallet-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Connect Wallet</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>
        
        <div className="modal-content">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div className="wallet-providers">
            {walletProviders.map((provider) => (
              <button
                key={provider.id}
                onClick={() => onConnect(provider.id)}
                className="wallet-provider-btn"
              >
                <img src={provider.icon} alt={provider.name} />
                <div className="provider-info">
                  <span className="provider-name">{provider.name}</span>
                  <span className="provider-description">{provider.description}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
```

### WalletBalance Component

Displays wallet balance information:

```typescript
// components/wallet/WalletBalance.tsx
import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../../store/store';
import { fetchBalanceAsync } from '../../store/slices/walletSlice';

export const WalletBalance: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { balance, address, connected } = useSelector(
    (state: RootState) => state.wallet
  );

  useEffect(() => {
    if (connected && address) {
      dispatch(fetchBalanceAsync());
      
      // Set up periodic balance updates
      const interval = setInterval(() => {
        dispatch(fetchBalanceAsync());
      }, 30000); // Update every 30 seconds
      
      return () => clearInterval(interval);
    }
  }, [connected, address, dispatch]);

  if (!balance) return null;

  return (
    <div className="wallet-balance">
      <div className="native-balance">
        <span className="balance-value">{balance.native.balance}</span>
        <span className="balance-symbol">{balance.native.symbol}</span>
        <span className="balance-usd">${balance.native.valueUsd}</span>
      </div>
      
      {balance.tokens.length > 0 && (
        <div className="token-balances">
          {balance.tokens.map((token) => (
            <div key={token.contract} className="token-balance">
              <span className="token-symbol">{token.symbol}</span>
              <span className="token-amount">{token.balance}</span>
              <span className="token-usd">${token.valueUsd}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## Wallet Connection Flow

### 1. User Initiates Connection

```typescript
// User clicks "Connect Wallet" button
const handleConnectClick = () => {
  setShowWalletModal(true);
};
```

### 2. Provider Selection

```typescript
// User selects wallet provider (MetaMask/Coinbase)
const handleProviderSelect = async (provider: WalletProviderType) => {
  try {
    await dispatch(connectWalletAsync(provider));
    setShowWalletModal(false);
  } catch (error) {
    // Error handling in Redux
  }
};
```

### 3. Wallet Connection Process

```typescript
// services/walletService.ts
export class WalletService {
  async connect(provider: WalletProviderType): Promise<ConnectionResult> {
    switch (provider) {
      case 'metamask':
        return this.connectMetaMask();
      case 'coinbase':
        return this.connectCoinbase();
      default:
        throw new Error(`Unsupported provider: ${provider}`);
    }
  }

  private async connectMetaMask(): Promise<ConnectionResult> {
    if (!window.ethereum) {
      throw new Error('MetaMask not installed');
    }

    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts'
    });

    const chainId = await window.ethereum.request({
      method: 'eth_chainId'
    });

    return {
      address: accounts[0],
      network: { chainId: parseInt(chainId, 16) }
    };
  }
}
```

### 4. State Updates

```typescript
// Redux automatically updates UI when state changes
const WalletStatus = () => {
  const { connected, address, provider } = useSelector(
    (state: RootState) => state.wallet
  );

  if (connected) {
    return (
      <div className="wallet-status connected">
        <span>{provider}</span>
        <span>{address}</span>
      </div>
    );
  }

  return <div className="wallet-status disconnected">Not Connected</div>;
};
```

---

## Error Handling

### Error Types and Handling

```typescript
// types/wallet.ts
export enum WalletErrorType {
  CONNECTION_REJECTED = 'CONNECTION_REJECTED',
  PROVIDER_NOT_FOUND = 'PROVIDER_NOT_FOUND',
  NETWORK_MISMATCH = 'NETWORK_MISMATCH',
  INSUFFICIENT_BALANCE = 'INSUFFICIENT_BALANCE',
  TRANSACTION_FAILED = 'TRANSACTION_FAILED'
}

export interface WalletError {
  type: WalletErrorType;
  message: string;
  details?: any;
}
```

### Error Display Component

```typescript
// components/wallet/ErrorBoundary.tsx
export const WalletErrorBoundary: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const error = useSelector((state: RootState) => state.wallet.error);

  if (error) {
    return (
      <div className="wallet-error">
        <h3>Wallet Error</h3>
        <p>{error}</p>
        <button onClick={() => dispatch(clearError())}>
          Dismiss
        </button>
      </div>
    );
  }

  return <>{children}</>;
};
```

---

## UI/UX Best Practices

### Loading States

```typescript
const LoadingButton: React.FC<{ loading: boolean; children: React.ReactNode }> = ({
  loading,
  children
}) => (
  <button disabled={loading} className={loading ? 'loading' : ''}>
    {loading ? <Spinner /> : children}
  </button>
);
```

### Responsive Design

```css
/* Responsive wallet components */
.wallet-connector {
  display: flex;
  align-items: center;
  gap: 1rem;
}

@media (max-width: 768px) {
  .wallet-connector {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .wallet-address {
    font-size: 0.875rem;
  }
}
```

### Accessibility

```typescript
// ARIA labels and keyboard navigation
<button
  onClick={handleConnect}
  aria-label="Connect wallet to access trading features"
  onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
>
  Connect Wallet
</button>
```

---

## Performance Optimization

### Memoization

```typescript
// Memoize expensive components
export const WalletBalance = React.memo(() => {
  const balance = useSelector(selectWalletBalance);
  return <BalanceDisplay balance={balance} />;
});

// Memoize selectors
export const selectWalletBalance = createSelector(
  (state: RootState) => state.wallet.balance,
  (balance) => balance
);
```

### Lazy Loading

```typescript
// Lazy load wallet components
const WalletModal = React.lazy(() => import('./WalletModal'));

const WalletConnector = () => {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <WalletModal />
    </Suspense>
  );
};
```

---

## Testing Frontend Components

### Component Testing

```typescript
// __tests__/WalletConnector.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { WalletConnector } from '../WalletConnector';
import { createMockStore } from '../../utils/testUtils';

describe('WalletConnector', () => {
  it('shows connect button when not connected', () => {
    const store = createMockStore({
      wallet: { connected: false, connecting: false }
    });

    render(
      <Provider store={store}>
        <WalletConnector />
      </Provider>
    );

    expect(screen.getByText('Connect Wallet')).toBeInTheDocument();
  });

  it('shows wallet info when connected', () => {
    const store = createMockStore({
      wallet: {
        connected: true,
        address: '0x123...789',
        provider: 'metamask'
      }
    });

    render(
      <Provider store={store}>
        <WalletConnector />
      </Provider>
    );

    expect(screen.getByText('metamask')).toBeInTheDocument();
    expect(screen.getByText('0x123...789')).toBeInTheDocument();
  });
});
```

### Integration Testing

```typescript
// __tests__/walletIntegration.test.tsx
describe('Wallet Integration', () => {
  it('completes full connection flow', async () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <App />
      </Provider>
    );

    // Click connect wallet
    fireEvent.click(screen.getByText('Connect Wallet'));

    // Select MetaMask
    fireEvent.click(screen.getByText('MetaMask'));

    // Wait for connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });
});
```

---

## References

- [Implementation Guide](5_wallet_integration_implementation_guide.md)
- [API Reference](6_wallet_integration_api_reference.md)
- [System Architecture](phase_4_wallet_integration_system_architecture.md)
- [Troubleshooting Guide](8_wallet_integration_troubleshooting_guide.md)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Redux Toolkit](https://redux-toolkit.js.org/)