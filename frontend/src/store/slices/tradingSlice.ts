import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  openTime: number;
  stopLoss?: number;
  takeProfit?: number;
  status: 'open' | 'closed';
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  size: number;
  price: number;
  fee: number;
  timestamp: number;
  positionId?: string;
  type: 'market' | 'limit' | 'stop';
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
}

export interface TradingMetrics {
  totalPnl: number;
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  maxDrawdown: number;
  sharpeRatio: number;
  totalVolume: number;
  averageWin: number;
  averageLoss: number;
}

export interface BotConfig {
  maxBuyAmountSol: number;
  minSafetyScore: number;
  slippageBps: number;
  useJito: boolean;
  priorityFeeLamports: number;
  jitoTipLamports: number;
}

export interface TradingState {
  positions: Record<string, Position>;
  trades: Trade[];
  botStatus: {
    isRunning: boolean;
    startTime: number | null;
    config: BotConfig;
  };
  metrics: TradingMetrics;
  balance: {
    sol: number;
    usdt: number;
    totalValue: number;
  };
  isLoading: boolean;
  error: string | null;
}

const initialState: TradingState = {
  positions: {},
  trades: [],
  botStatus: {
    isRunning: false,
    startTime: null,
    config: {
      maxBuyAmountSol: 0.1,
      minSafetyScore: 70,
      slippageBps: 300,
      useJito: true,
      priorityFeeLamports: 10000,
      jitoTipLamports: 100000,
    },
  },
  metrics: {
    totalPnl: 0,
    totalTrades: 0,
    winRate: 0,
    profitFactor: 0,
    maxDrawdown: 0,
    sharpeRatio: 0,
    totalVolume: 0,
    averageWin: 0,
    averageLoss: 0,
  },
  balance: {
    sol: 0,
    usdt: 0,
    totalValue: 0,
  },
  isLoading: false,
  error: null,
};

const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    updatePosition: (state, action: PayloadAction<Position>) => {
      const position = action.payload;
      state.positions[position.id] = position;
    },
    closePosition: (state, action: PayloadAction<string>) => {
      const positionId = action.payload;
      if (state.positions[positionId]) {
        state.positions[positionId].status = 'closed';
      }
    },
    addTrade: (state, action: PayloadAction<Trade>) => {
      state.trades.unshift(action.payload);
      // Keep only last 1000 trades
      if (state.trades.length > 1000) {
        state.trades = state.trades.slice(0, 1000);
      }
    },
    updateTrade: (state, action: PayloadAction<Trade>) => {
      const trade = action.payload;
      const index = state.trades.findIndex(t => t.id === trade.id);
      if (index !== -1) {
        state.trades[index] = trade;
      }
    },
    setBotStatus: (state, action: PayloadAction<Partial<typeof state.botStatus>>) => {
      state.botStatus = {
        ...state.botStatus,
        ...action.payload,
      };
    },
    updateBotConfig: (state, action: PayloadAction<Partial<BotConfig>>) => {
      state.botStatus.config = {
        ...state.botStatus.config,
        ...action.payload,
      };
    },
    updateMetrics: (state, action: PayloadAction<Partial<TradingMetrics>>) => {
      state.metrics = {
        ...state.metrics,
        ...action.payload,
      };
    },
    updateBalance: (state, action: PayloadAction<Partial<typeof state.balance>>) => {
      state.balance = {
        ...state.balance,
        ...action.payload,
      };
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearTrades: (state) => {
      state.trades = [];
    },
    clearPositions: (state) => {
      state.positions = {};
    },
  },
});

export const {
  updatePosition,
  closePosition,
  addTrade,
  updateTrade,
  setBotStatus,
  updateBotConfig,
  updateMetrics,
  updateBalance,
  setLoading,
  setError,
  clearTrades,
  clearPositions,
} = tradingSlice.actions;

export default tradingSlice.reducer;
