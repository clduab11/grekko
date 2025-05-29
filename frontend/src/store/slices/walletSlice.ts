import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type WalletProviderType = 'metamask' | 'coinbase' | null;

export interface WalletState {
  provider: WalletProviderType;
  address: string | null;
  connected: boolean;
  error: string | null;
  connecting: boolean;
}

const initialState: WalletState = {
  provider: null,
  address: null,
  connected: false,
  error: null,
  connecting: false,
};

const walletSlice = createSlice({
  name: 'wallet',
  initialState,
  reducers: {
    connectWalletStart(state, action: PayloadAction<WalletProviderType>) {
      state.provider = action.payload;
      state.connecting = true;
      state.error = null;
    },
    connectWalletSuccess(
      state,
      action: PayloadAction<{ provider: WalletProviderType; address: string }>
    ) {
      state.provider = action.payload.provider;
      state.address = action.payload.address;
      state.connected = true;
      state.connecting = false;
      state.error = null;
    },
    connectWalletFailure(state, action: PayloadAction<string>) {
      state.error = action.payload;
      state.connected = false;
      state.connecting = false;
      state.address = null;
    },
    disconnectWallet(state) {
      state.provider = null;
      state.address = null;
      state.connected = false;
      state.error = null;
      state.connecting = false;
    },
  },
});

export const {
  connectWalletStart,
  connectWalletSuccess,
  connectWalletFailure,
  disconnectWallet,
} = walletSlice.actions;

export default walletSlice.reducer;