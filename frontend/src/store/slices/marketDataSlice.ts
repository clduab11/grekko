import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface CandlestickData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketTicker {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  lastUpdate: number;
}

export interface OrderBookLevel {
  price: number;
  quantity: number;
  total: number;
}

export interface OrderBook {
  symbol: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  lastUpdate: number;
}

export interface MarketDataState {
  currentSymbol: string;
  timeframe: string;
  candlestickData: CandlestickData[];
  tickers: Record<string, MarketTicker>;
  orderBook: OrderBook | null;
  isLoading: boolean;
  lastUpdate: number;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

const initialState: MarketDataState = {
  currentSymbol: 'SOL/USDT',
  timeframe: '1m',
  candlestickData: [],
  tickers: {},
  orderBook: null,
  isLoading: false,
  lastUpdate: 0,
  connectionStatus: 'disconnected',
};

const marketDataSlice = createSlice({
  name: 'marketData',
  initialState,
  reducers: {
    setCurrentSymbol: (state, action: PayloadAction<string>) => {
      state.currentSymbol = action.payload;
      state.candlestickData = [];
      state.orderBook = null;
    },
    setTimeframe: (state, action: PayloadAction<string>) => {
      state.timeframe = action.payload;
      state.candlestickData = [];
    },
    setCandlestickData: (state, action: PayloadAction<CandlestickData[]>) => {
      state.candlestickData = action.payload;
      state.lastUpdate = Date.now();
    },
    updateCandlestickData: (state, action: PayloadAction<CandlestickData>) => {
      const newCandle = action.payload;
      const existingIndex = state.candlestickData.findIndex(
        candle => candle.time === newCandle.time
      );
      
      if (existingIndex !== -1) {
        // Update existing candle
        state.candlestickData[existingIndex] = newCandle;
      } else {
        // Add new candle
        state.candlestickData.push(newCandle);
        // Keep only last 1000 candles for performance
        if (state.candlestickData.length > 1000) {
          state.candlestickData = state.candlestickData.slice(-1000);
        }
      }
      state.lastUpdate = Date.now();
    },
    updateTicker: (state, action: PayloadAction<MarketTicker>) => {
      const ticker = action.payload;
      state.tickers[ticker.symbol] = ticker;
      state.lastUpdate = Date.now();
    },
    updateOrderBook: (state, action: PayloadAction<OrderBook>) => {
      state.orderBook = action.payload;
      state.lastUpdate = Date.now();
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setConnectionStatus: (state, action: PayloadAction<'connected' | 'disconnected' | 'connecting'>) => {
      state.connectionStatus = action.payload;
    },
    clearMarketData: (state) => {
      state.candlestickData = [];
      state.orderBook = null;
      state.tickers = {};
      state.lastUpdate = 0;
    },
  },
});

export const {
  setCurrentSymbol,
  setTimeframe,
  setCandlestickData,
  updateCandlestickData,
  updateTicker,
  updateOrderBook,
  setLoading,
  setConnectionStatus,
  clearMarketData,
} = marketDataSlice.actions;

export default marketDataSlice.reducer;
