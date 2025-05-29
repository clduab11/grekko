import React from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Visibility,
  Psychology,
  SmartToy,
  Circle,
  Clear,
  Settings,
  PlayArrow,
  Stop,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../../store/store';
import { setSelectedAgent, clearAgentMessages } from '../../store/slices/agentSlice';

const AgentSidebar: React.FC = () => {
  const dispatch = useAppDispatch();
  const { agents, selectedAgent } = useAppSelector((state: any) => state.agents);
  const currentAgent = selectedAgent ? agents[selectedAgent] : null;

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    dispatch(setSelectedAgent(newValue));
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'spot': return <Visibility />;
      case 'gordo': return <Psychology />;
      case 'gekko': return <SmartToy />;
      default: return <Circle />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (!currentAgent) return null;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Agent Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={selectedAgent}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              minHeight: '48px',
              fontSize: '0.75rem',
              color: '#999',
            },
            '& .Mui-selected': {
              color: '#0088cc !important',
            },
          }}
        >
          {Object.values(agents).map((agent: any) => (
            <Tab
              key={agent.id}
              label={agent.name}
              value={agent.id}
              icon={getAgentIcon(agent.type)}
              iconPosition="top"
            />
          ))}
        </Tabs>
      </Box>

      {/* Agent Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          {getAgentIcon(currentAgent.type)}
          <Typography variant="h6" sx={{ color: 'white', flexGrow: 1 }}>
            {currentAgent.name}
          </Typography>
          <Chip
            label={currentAgent.status}
            color={getStatusColor(currentAgent.status) as any}
            size="small"
            icon={<Circle sx={{ fontSize: '8px !important' }} />}
          />
        </Box>

        <Typography variant="body2" sx={{ color: '#999', mb: 2 }}>
          {currentAgent.description}
        </Typography>

        {/* Agent Metrics */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 2 }}>
          <Paper sx={{ p: 1, backgroundColor: '#1e1e1e' }}>
            <Typography variant="caption" color="#999">Success Rate</Typography>
            <Typography variant="h6" color="white">
              {currentAgent.metrics.successRate.toFixed(1)}%
            </Typography>
          </Paper>
          <Paper sx={{ p: 1, backgroundColor: '#1e1e1e' }}>
            <Typography variant="caption" color="#999">Signals</Typography>
            <Typography variant="h6" color="white">
              {currentAgent.metrics.totalSignals}
            </Typography>
          </Paper>
          <Paper sx={{ p: 1, backgroundColor: '#1e1e1e' }}>
            <Typography variant="caption" color="#999">P&L</Typography>
            <Typography 
              variant="h6" 
              color={currentAgent.metrics.profitLoss >= 0 ? '#26a69a' : '#ef5350'}
            >
              {currentAgent.metrics.profitLoss >= 0 ? '+' : ''}
              {currentAgent.metrics.profitLoss.toFixed(2)}
            </Typography>
          </Paper>
          <Paper sx={{ p: 1, backgroundColor: '#1e1e1e' }}>
            <Typography variant="caption" color="#999">Alerts</Typography>
            <Typography variant="h6" color="white">
              {currentAgent.metrics.activeAlerts}
            </Typography>
          </Paper>
        </Box>

        {/* Agent Controls */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            size="small"
            sx={{
              backgroundColor: currentAgent.status === 'active' ? '#ef5350' : '#26a69a',
              color: 'white',
              '&:hover': {
                backgroundColor: currentAgent.status === 'active' ? '#d32f2f' : '#1b5e20',
              },
            }}
          >
            {currentAgent.status === 'active' ? <Stop /> : <PlayArrow />}
          </IconButton>
          <IconButton size="small" sx={{ color: '#999' }}>
            <Settings />
          </IconButton>
          <IconButton 
            size="small" 
            sx={{ color: '#999' }}
            onClick={() => dispatch(clearAgentMessages(currentAgent.id))}
          >
            <Clear />
          </IconButton>
        </Box>
      </Box>

      {/* Messages/Activity Feed */}
      <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="subtitle2" sx={{ color: 'white' }}>
            Activity Feed
          </Typography>
        </Box>

        <List sx={{ flexGrow: 1, overflow: 'auto', py: 0 }}>
          {currentAgent.messages.length === 0 ? (
            <ListItem>
              <ListItemText
                primary="No activity yet"
                primaryTypographyProps={{ color: '#666', textAlign: 'center' }}
              />
            </ListItem>
          ) : (
            currentAgent.messages.map((message: any) => (
              <React.Fragment key={message.id}>
                <ListItem sx={{ alignItems: 'flex-start', py: 1 }}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Circle 
                          sx={{ 
                            fontSize: 8,
                            color: message.type === 'success' ? '#26a69a' :
                                   message.type === 'error' ? '#ef5350' :
                                   message.type === 'warning' ? '#ff9800' : '#2196f3'
                          }} 
                        />
                        <Typography variant="caption" sx={{ color: '#999' }}>
                          {formatTimestamp(message.timestamp)}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          color: 'white',
                          wordBreak: 'break-word',
                          fontSize: '0.875rem',
                        }}
                      >
                        {message.content}
                      </Typography>
                    }
                  />
                </ListItem>
                <Divider sx={{ backgroundColor: '#363a45' }} />
              </React.Fragment>
            ))
          )}
        </List>
      </Box>

      {/* Real-time Activity Indicator */}
      {currentAgent.status === 'active' && (
        <Box sx={{ p: 1, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Circle sx={{ fontSize: 8, color: '#26a69a' }} />
            <Typography variant="caption" sx={{ color: '#26a69a' }}>
              Agent Active
            </Typography>
          </Box>
          <LinearProgress 
            sx={{
              height: 2,
              backgroundColor: '#363a45',
              '& .MuiLinearProgress-bar': {
                backgroundColor: '#26a69a',
              },
            }}
          />
        </Box>
      )}
    </Box>
  );
};

export default AgentSidebar;
