import React, { useEffect } from 'react';
import { Box } from '@mui/material';
import { useAppSelector, useAppDispatch } from './store/store';
import { setConnectionStatus } from './store/slices/marketDataSlice';

import Header from './components/layout/Header';
import MainLayout from './components/layout/MainLayout';
import WebSocketService from './services/websocketService';

function App() {
  const dispatch = useAppDispatch();
  const connectionStatus = useAppSelector(state => state.marketData.connectionStatus);

  useEffect(() => {
    // Initialize WebSocket connection
    const wsService = WebSocketService.getInstance();
    
    wsService.connect()
      .then(() => {
        dispatch(setConnectionStatus('connected'));
      })
      .catch((error) => {
        console.error('WebSocket connection failed:', error);
        dispatch(setConnectionStatus('disconnected'));
      });

    // Cleanup on unmount
    return () => {
      wsService.disconnect();
    };
  }, [dispatch]);

  return (
    <Box className="trading-container">
      <Header />
      <MainLayout />
    </Box>
  );
}

export default App;
