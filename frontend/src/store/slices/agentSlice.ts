import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface AgentMessage {
  id: string;
  timestamp: number;
  type: 'info' | 'warning' | 'error' | 'success';
  content: string;
  data?: any;
}

export interface AgentMetrics {
  successRate: number;
  totalSignals: number;
  activeAlerts: number;
  profitLoss: number;
  uptime: number;
}

export interface Agent {
  id: string;
  name: string;
  type: 'spot' | 'gordo' | 'gekko';
  status: 'active' | 'inactive' | 'error';
  description: string;
  lastActivity: number;
  messages: AgentMessage[];
  metrics: AgentMetrics;
  config: Record<string, any>;
}

export interface AgentState {
  agents: Record<string, Agent>;
  selectedAgent: string | null;
  isLoading: boolean;
}

const initialState: AgentState = {
  agents: {
    spot: {
      id: 'spot',
      name: 'Spot',
      type: 'spot',
      status: 'inactive',
      description: 'Real-time volatility alerts across multiple exchanges',
      lastActivity: 0,
      messages: [],
      metrics: {
        successRate: 0,
        totalSignals: 0,
        activeAlerts: 0,
        profitLoss: 0,
        uptime: 0,
      },
      config: {
        volatilityThreshold: 5.0,
        exchanges: ['binance', 'coinbase', 'uniswap'],
        alertCooldown: 300,
      },
    },
    gordo: {
      id: 'gordo',
      name: 'Gordo',
      type: 'gordo',
      status: 'inactive',
      description: 'Analytical companion using LLM ensemble',
      lastActivity: 0,
      messages: [],
      metrics: {
        successRate: 0,
        totalSignals: 0,
        activeAlerts: 0,
        profitLoss: 0,
        uptime: 0,
      },
      config: {
        analysisDepth: 'comprehensive',
        models: ['gpt-4', 'claude'],
        confidenceThreshold: 0.7,
      },
    },
    gekko: {
      id: 'gekko',
      name: 'Gekko',
      type: 'gekko',
      status: 'inactive',
      description: 'Autonomous trader leveraging ExecutionManager',
      lastActivity: 0,
      messages: [],
      metrics: {
        successRate: 0,
        totalSignals: 0,
        activeAlerts: 0,
        profitLoss: 0,
        uptime: 0,
      },
      config: {
        maxPositionSize: 0.1,
        riskLevel: 'medium',
        tradingPairs: ['SOL/USDT', 'BTC/USDT', 'ETH/USDT'],
        stopLoss: 5.0,
        takeProfit: 10.0,
      },
    },
  },
  selectedAgent: 'spot',
  isLoading: false,
};

const agentSlice = createSlice({
  name: 'agents',
  initialState,
  reducers: {
    setSelectedAgent: (state, action: PayloadAction<string>) => {
      state.selectedAgent = action.payload;
    },
    updateAgentStatus: (state, action: PayloadAction<{ agentId: string; status: Agent['status'] }>) => {
      const { agentId, status } = action.payload;
      if (state.agents[agentId]) {
        state.agents[agentId].status = status;
        state.agents[agentId].lastActivity = Date.now();
      }
    },
    addAgentMessage: (state, action: PayloadAction<{ agentId: string; message: Omit<AgentMessage, 'id'> }>) => {
      const { agentId, message } = action.payload;
      if (state.agents[agentId]) {
        const fullMessage: AgentMessage = {
          ...message,
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        };
        state.agents[agentId].messages.unshift(fullMessage);
        state.agents[agentId].lastActivity = Date.now();
        
        // Keep only last 100 messages
        if (state.agents[agentId].messages.length > 100) {
          state.agents[agentId].messages = state.agents[agentId].messages.slice(0, 100);
        }
      }
    },
    updateAgentMetrics: (state, action: PayloadAction<{ agentId: string; metrics: Partial<AgentMetrics> }>) => {
      const { agentId, metrics } = action.payload;
      if (state.agents[agentId]) {
        state.agents[agentId].metrics = {
          ...state.agents[agentId].metrics,
          ...metrics,
        };
        state.agents[agentId].lastActivity = Date.now();
      }
    },
    updateAgentConfig: (state, action: PayloadAction<{ agentId: string; config: Record<string, any> }>) => {
      const { agentId, config } = action.payload;
      if (state.agents[agentId]) {
        state.agents[agentId].config = {
          ...state.agents[agentId].config,
          ...config,
        };
      }
    },
    clearAgentMessages: (state, action: PayloadAction<string>) => {
      const agentId = action.payload;
      if (state.agents[agentId]) {
        state.agents[agentId].messages = [];
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
  },
});

export const {
  setSelectedAgent,
  updateAgentStatus,
  addAgentMessage,
  updateAgentMetrics,
  updateAgentConfig,
  clearAgentMessages,
  setLoading,
} = agentSlice.actions;

export default agentSlice.reducer;
