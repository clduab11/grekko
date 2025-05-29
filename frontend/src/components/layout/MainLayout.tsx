import React from 'react';
import { Box, Drawer } from '@mui/material';
import { useAppSelector } from '../../store/store';

import TradingChart from '../chart/TradingChart';
import AgentSidebar from '../agents/AgentSidebar';

const MainLayout: React.FC = () => {
  const { sidebarOpen, windowSizes } = useAppSelector((state: any) => state.ui);

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 56px)' }}>
      {/* Main Chart Area */}
      <Box
        sx={{
          flexGrow: 1,
          position: 'relative',
          backgroundColor: '#1a1a1a',
          transition: 'margin-right 0.3s ease',
          marginRight: sidebarOpen ? `${windowSizes.sidebar}px` : 0,
        }}
      >
        <TradingChart />
      </Box>

      {/* Right Sidebar with Agents */}
      <Drawer
        anchor="right"
        variant="persistent"
        open={sidebarOpen}
        sx={{
          width: windowSizes.sidebar,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: windowSizes.sidebar,
            position: 'relative',
            height: '100%',
            backgroundColor: '#131722',
            borderLeft: '1px solid #363a45',
          },
        }}
      >
        <AgentSidebar />
      </Drawer>
    </Box>
  );
};

export default MainLayout;
