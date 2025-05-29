import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface UIState {
  sidebarOpen: boolean;
  selectedTab: string;
  chartSettings: {
    candlestickType: 'candlestick' | 'hollow_candlestick' | 'line' | 'area';
    indicators: string[];
    timeframe: string;
    overlays: string[];
  };
  notifications: {
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message: string;
    timestamp: number;
    read: boolean;
  }[];
  theme: 'dark' | 'light';
  isFullscreen: boolean;
  windowSizes: {
    sidebar: number;
    chartArea: number;
  };
}

const initialState: UIState = {
  sidebarOpen: true,
  selectedTab: 'spot',
  chartSettings: {
    candlestickType: 'candlestick',
    indicators: ['volume'],
    timeframe: '1m',
    overlays: [],
  },
  notifications: [],
  theme: 'dark',
  isFullscreen: false,
  windowSizes: {
    sidebar: 320,
    chartArea: 0,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    setSelectedTab: (state, action: PayloadAction<string>) => {
      state.selectedTab = action.payload;
    },
    updateChartSettings: (state, action: PayloadAction<Partial<UIState['chartSettings']>>) => {
      state.chartSettings = {
        ...state.chartSettings,
        ...action.payload,
      };
    },
    addIndicator: (state, action: PayloadAction<string>) => {
      if (!state.chartSettings.indicators.includes(action.payload)) {
        state.chartSettings.indicators.push(action.payload);
      }
    },
    removeIndicator: (state, action: PayloadAction<string>) => {
      state.chartSettings.indicators = state.chartSettings.indicators.filter(
        indicator => indicator !== action.payload
      );
    },
    addOverlay: (state, action: PayloadAction<string>) => {
      if (!state.chartSettings.overlays.includes(action.payload)) {
        state.chartSettings.overlays.push(action.payload);
      }
    },
    removeOverlay: (state, action: PayloadAction<string>) => {
      state.chartSettings.overlays = state.chartSettings.overlays.filter(
        overlay => overlay !== action.payload
      );
    },
    addNotification: (state, action: PayloadAction<Omit<UIState['notifications'][0], 'id' | 'timestamp' | 'read'>>) => {
      const notification = {
        ...action.payload,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        read: false,
      };
      state.notifications.unshift(notification);
      
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    markNotificationRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        notification.read = true;
      }
    },
    markAllNotificationsRead: (state) => {
      state.notifications.forEach(n => n.read = true);
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setTheme: (state, action: PayloadAction<'dark' | 'light'>) => {
      state.theme = action.payload;
    },
    toggleFullscreen: (state) => {
      state.isFullscreen = !state.isFullscreen;
    },
    setFullscreen: (state, action: PayloadAction<boolean>) => {
      state.isFullscreen = action.payload;
    },
    updateWindowSizes: (state, action: PayloadAction<Partial<UIState['windowSizes']>>) => {
      state.windowSizes = {
        ...state.windowSizes,
        ...action.payload,
      };
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setSelectedTab,
  updateChartSettings,
  addIndicator,
  removeIndicator,
  addOverlay,
  removeOverlay,
  addNotification,
  markNotificationRead,
  markAllNotificationsRead,
  removeNotification,
  clearNotifications,
  setTheme,
  toggleFullscreen,
  setFullscreen,
  updateWindowSizes,
} = uiSlice.actions;

export default uiSlice.reducer;
