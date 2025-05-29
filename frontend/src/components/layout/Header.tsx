import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Chip,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Fullscreen,
  FullscreenExit,
  Settings,
  TrendingUp,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../../store/store';
import { toggleSidebar, toggleFullscreen } from '../../store/slices/uiSlice';
import { setCurrentSymbol, setTimeframe } from '../../store/slices/marketDataSlice';
import {
  connectWalletStart,
  connectWalletSuccess,
  connectWalletFailure,
  disconnectWallet,
} from '../../store/slices/walletSlice';

const Header: React.FC = () => {
  const dispatch = useAppDispatch();
  const { sidebarOpen, isFullscreen } = useAppSelector(state => state.ui);
  const { currentSymbol, timeframe, connectionStatus } = useAppSelector(state => state.marketData);
  const { isRunning } = useAppSelector(state => state.trading.botStatus);
  const wallet = useAppSelector(state => state.wallet);

  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
  const symbols = ['SOL/USDT', 'BTC/USDT', 'ETH/USDT', 'BNB/USDT'];

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'success';
      case 'connecting': return 'warning';
      case 'disconnected': return 'error';
      default: return 'default';
    }
  };

  // Wallet connect handlers (stubbed for demo; real logic would use window.ethereum, etc.)
  const handleConnectMetaMask = async () => {
    dispatch(connectWalletStart('metamask'));
    try {
      // In production, use window.ethereum.request({ method: 'eth_requestAccounts' }) etc.
      // Here, simulate connection
      setTimeout(() => {
        dispatch(connectWalletSuccess({ provider: 'metamask', address: '0x1234...abcd' }));
      }, 500);
    } catch (err: any) {
      dispatch(connectWalletFailure('MetaMask connection failed'));
    }
  };

  const handleConnectCoinbase = async () => {
    dispatch(connectWalletStart('coinbase'));
    try {
      // In production, use Coinbase Wallet SDK
      setTimeout(() => {
        dispatch(connectWalletSuccess({ provider: 'coinbase', address: '0x9876...cdef' }));
      }, 500);
    } catch (err: any) {
      dispatch(connectWalletFailure('Coinbase Wallet connection failed'));
    }
  };

  const handleDisconnect = () => {
    dispatch(disconnectWallet());
  };

  return (
    <AppBar position="static" elevation={0}>
      <Toolbar sx={{ minHeight: '56px !important', px: 2 }}>
        {/* Logo and Menu */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => dispatch(toggleSidebar())}
            sx={{ mr: 1 }}
          >
            <MenuIcon />
          </IconButton>
          
          <TrendingUp sx={{ color: '#0088cc', fontSize: 28 }} />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 'bold',
              background: 'linear-gradient(45deg, #0088cc 30%, #42a5f5 90%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            GREKKO
          </Typography>
        </Box>

        {/* Trading Pair Selector */}
        <Box sx={{ mx: 3 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <Select
              value={currentSymbol}
              onChange={(e) => dispatch(setCurrentSymbol(e.target.value))}
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'transparent',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#363a45',
                },
              }}
            >
              {symbols.map((symbol) => (
                <MenuItem key={symbol} value={symbol}>
                  {symbol}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Timeframe Selector */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {timeframes.map((tf) => (
            <Chip
              key={tf}
              label={tf}
              onClick={() => dispatch(setTimeframe(tf))}
              variant={timeframe === tf ? 'filled' : 'outlined'}
              color={timeframe === tf ? 'primary' : 'default'}
              size="small"
              sx={{
                height: 28,
                fontSize: '0.75rem',
                fontWeight: 500,
              }}
            />
          ))}
        </Box>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Wallet Connect UI */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 2 }}>
          {!wallet.connected ? (
            <>
              <Chip
                label="Connect MetaMask"
                color="primary"
                size="small"
                onClick={handleConnectMetaMask}
                disabled={wallet.connecting}
                sx={{ cursor: 'pointer', fontWeight: 500 }}
              />
              <Chip
                label="Connect Coinbase"
                color="secondary"
                size="small"
                onClick={handleConnectCoinbase}
                disabled={wallet.connecting}
                sx={{ cursor: 'pointer', fontWeight: 500 }}
              />
            </>
          ) : (
            <>
              <Chip
                label={
                  wallet.provider === 'metamask'
                    ? `MetaMask: ${wallet.address}`
                    : `Coinbase: ${wallet.address}`
                }
                color="success"
                size="small"
                sx={{ fontWeight: 500 }}
                onDelete={handleDisconnect}
                variant="outlined"
              />
            </>
          )}
        </Box>

        {/* Status Indicators */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Bot Status */}
          <Chip
            label={isRunning ? 'BOT ACTIVE' : 'BOT INACTIVE'}
            color={isRunning ? 'success' : 'default'}
            size="small"
            sx={{
              fontWeight: 'bold',
              animation: isRunning ? 'pulse 2s infinite' : 'none',
            }}
          />

          {/* Connection Status */}
          <Chip
            label={connectionStatus.toUpperCase()}
            color={getConnectionStatusColor() as any}
            size="small"
            variant="outlined"
          />

          {/* Controls */}
          <IconButton
            color="inherit"
            onClick={() => dispatch(toggleFullscreen())}
            size="small"
          >
            {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
          </IconButton>

          <IconButton color="inherit" size="small">
            <Settings />
          </IconButton>
        </Box>
      </Toolbar>

      <style>
        {`
          @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
          }
        `}
      </style>
    </AppBar>
  );
};

export default Header;
