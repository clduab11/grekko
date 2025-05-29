import { io, Socket } from 'socket.io-client';
import { store } from '../store/store';
import { 
  updateCandlestickData, 
  updateTicker, 
  updateOrderBook,
  setConnectionStatus 
} from '../store/slices/marketDataSlice';
import { 
  updateAgentStatus, 
  addAgentMessage, 
  updateAgentMetrics 
} from '../store/slices/agentSlice';
import { 
  addTrade, 
  updatePosition, 
  setBotStatus,
  updateMetrics,
  updateBalance 
} from '../store/slices/tradingSlice';
import { addNotification } from '../store/slices/uiSlice';

export class WebSocketService {
  private static instance: WebSocketService;
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  private constructor() {}

  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  public async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Connect to the FastAPI WebSocket endpoint
        this.socket = io('ws://localhost:8000', {
          transports: ['websocket'],
          timeout: 5000,
        });

        this.socket.on('connect', () => {
          console.log('WebSocket connected');
          store.dispatch(setConnectionStatus('connected'));
          this.reconnectAttempts = 0;
          
          store.dispatch(addNotification({
            type: 'success',
            title: 'Connected',
            message: 'Real-time data connection established',
          }));
          
          resolve();
        });

        this.socket.on('disconnect', () => {
          console.log('WebSocket disconnected');
          store.dispatch(setConnectionStatus('disconnected'));
          
          store.dispatch(addNotification({
            type: 'warning',
            title: 'Disconnected',
            message: 'Real-time data connection lost',
          }));
          
          this.handleReconnect();
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          store.dispatch(setConnectionStatus('disconnected'));
          reject(error);
        });

        // Bot status updates
        this.socket.on('bot_status', (data) => {
          console.log('Bot status update:', data);
          store.dispatch(setBotStatus({
            isRunning: data.is_running,
            startTime: data.start_time ? new Date(data.start_time).getTime() : null,
          }));
        });

        // New token detection
        this.socket.on('new_token', (data) => {
          console.log('New token detected:', data);
          store.dispatch(addAgentMessage({
            agentId: 'spot',
            message: {
              timestamp: Date.now(),
              type: 'info',
              content: `New token detected: ${data.token_address}`,
              data: data,
            },
          }));
          
          store.dispatch(addNotification({
            type: 'info',
            title: 'New Token',
            message: `Detected: ${data.token_address.slice(0, 8)}...`,
          }));
        });

        // Safety analysis results
        this.socket.on('safety_analysis', (data) => {
          console.log('Safety analysis:', data);
          const messageType = data.safety_score >= 70 ? 'success' : 
                            data.safety_score >= 50 ? 'warning' : 'error';
          
          store.dispatch(addAgentMessage({
            agentId: 'spot',
            message: {
              timestamp: Date.now(),
              type: messageType,
              content: `Safety analysis: ${data.safety_score}/100 - ${data.verdict}`,
              data: data,
            },
          }));
        });

        // Trade execution results
        this.socket.on('trade_result', (data) => {
          console.log('Trade result:', data);
          
          if (data.success) {
            store.dispatch(addTrade({
              id: `trade_${Date.now()}`,
              symbol: data.token_address,
              side: 'buy',
              size: data.tokens_received,
              price: data.amount_spent / data.tokens_received,
              fee: 0,
              timestamp: Date.now(),
              type: 'market',
              status: 'filled',
            }));
            
            store.dispatch(addNotification({
              type: 'success',
              title: 'Trade Executed',
              message: `Bought ${data.tokens_received.toFixed(2)} tokens for ${data.amount_spent.toFixed(4)} SOL`,
            }));
            
            store.dispatch(addAgentMessage({
              agentId: 'gekko',
              message: {
                timestamp: Date.now(),
                type: 'success',
                content: `Trade executed: ${data.tokens_received.toFixed(2)} tokens for ${data.amount_spent.toFixed(4)} SOL`,
                data: data,
              },
            }));
          } else {
            store.dispatch(addNotification({
              type: 'error',
              title: 'Trade Failed',
              message: data.error || 'Unknown error',
            }));
            
            store.dispatch(addAgentMessage({
              agentId: 'gekko',
              message: {
                timestamp: Date.now(),
                type: 'error',
                content: `Trade failed: ${data.error}`,
                data: data,
              },
            }));
          }
        });

        // Generic error messages
        this.socket.on('error', (data) => {
          console.error('WebSocket error:', data);
          store.dispatch(addNotification({
            type: 'error',
            title: 'Error',
            message: data.error || 'An error occurred',
          }));
        });

        // Market data updates (if implemented)
        this.socket.on('price_update', (data) => {
          store.dispatch(updateTicker({
            symbol: data.symbol,
            price: data.price,
            change24h: data.change24h || 0,
            changePercent24h: data.changePercent24h || 0,
            volume24h: data.volume24h || 0,
            high24h: data.high24h || data.price,
            low24h: data.low24h || data.price,
            lastUpdate: Date.now(),
          }));
        });

        this.socket.on('candle_update', (data) => {
          store.dispatch(updateCandlestickData({
            time: data.time,
            open: data.open,
            high: data.high,
            low: data.low,
            close: data.close,
            volume: data.volume,
          }));
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  public emit(event: string, data?: any): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      store.dispatch(setConnectionStatus('connecting'));
      
      setTimeout(() => {
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect().catch(() => {
          // Reconnection failed, will try again if within limit
        });
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      store.dispatch(addNotification({
        type: 'error',
        title: 'Connection Lost',
        message: 'Failed to reconnect. Please refresh the page.',
      }));
    }
  }

  public isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export default WebSocketService;
