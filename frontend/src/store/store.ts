import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

import marketDataReducer from './slices/marketDataSlice';
import agentReducer from './slices/agentSlice';
import tradingReducer from './slices/tradingSlice';
import uiReducer from './slices/uiSlice';
import walletReducer from './slices/walletSlice';

export const store = configureStore({
  reducer: {
    marketData: marketDataReducer,
    agents: agentReducer,
    trading: tradingReducer,
    ui: uiReducer,
    wallet: walletReducer,
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

// Typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
