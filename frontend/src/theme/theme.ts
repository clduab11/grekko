import { createTheme } from '@mui/material/styles';

// TradingView-inspired dark theme
export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#0088cc',
      light: '#42a5f5',
      dark: '#005f99',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#26a69a',
      light: '#4db6ac',
      dark: '#00695c',
      contrastText: '#ffffff',
    },
    error: {
      main: '#ef5350',
      light: '#ff6b6b',
      dark: '#c62828',
    },
    warning: {
      main: '#ff9800',
      light: '#ffb74d',
      dark: '#f57400',
    },
    info: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    success: {
      main: '#4caf50',
      light: '#81c784',
      dark: '#388e3c',
    },
    background: {
      default: '#0b0e11',
      paper: '#1e222d',
    },
    text: {
      primary: '#d1d4dc',
      secondary: '#868b98',
    },
    divider: '#2a2e39',
    action: {
      hover: 'rgba(255, 255, 255, 0.05)',
      selected: 'rgba(255, 255, 255, 0.08)',
      disabled: 'rgba(255, 255, 255, 0.3)',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
      color: '#868b98',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 4,
  },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: '#2a2e39 #1e222d',
          '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
            width: 8,
            height: 8,
          },
          '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
            borderRadius: 4,
            backgroundColor: '#2a2e39',
            '&:hover': {
              backgroundColor: '#363a45',
            },
          },
          '&::-webkit-scrollbar-track, & *::-webkit-scrollbar-track': {
            backgroundColor: '#1e222d',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 4,
          fontWeight: 500,
          '&.MuiButton-contained': {
            boxShadow: 'none',
            '&:hover': {
              boxShadow: 'none',
            },
          },
        },
        containedPrimary: {
          background: 'linear-gradient(45deg, #0088cc 30%, #42a5f5 90%)',
          '&:hover': {
            background: 'linear-gradient(45deg, #005f99 30%, #1976d2 90%)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#1e222d',
          border: '1px solid #2a2e39',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e222d',
          borderBottom: '1px solid #2a2e39',
          boxShadow: 'none',
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e222d',
          borderBottom: '1px solid #2a2e39',
        },
        indicator: {
          backgroundColor: '#0088cc',
          height: 2,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          minWidth: 'auto',
          padding: '12px 16px',
          color: '#868b98',
          '&.Mui-selected': {
            color: '#d1d4dc',
          },
          '&:hover': {
            color: '#d1d4dc',
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          color: '#868b98',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            color: '#d1d4dc',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: '#2a2e39',
          color: '#d1d4dc',
          '&.MuiChip-colorPrimary': {
            backgroundColor: '#0088cc',
            color: '#ffffff',
          },
          '&.MuiChip-colorSecondary': {
            backgroundColor: '#26a69a',
            color: '#ffffff',
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#2a2e39',
          color: '#d1d4dc',
          fontSize: '0.75rem',
          border: '1px solid #363a45',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: '#1e222d',
            '& fieldset': {
              borderColor: '#2a2e39',
            },
            '&:hover fieldset': {
              borderColor: '#363a45',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#0088cc',
            },
          },
          '& .MuiInputLabel-root': {
            color: '#868b98',
            '&.Mui-focused': {
              color: '#0088cc',
            },
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e222d',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: '#2a2e39',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#363a45',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#0088cc',
          },
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1e222d',
          border: '1px solid #2a2e39',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          color: '#d1d4dc',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
          },
          '&.Mui-selected': {
            backgroundColor: 'rgba(0, 136, 204, 0.12)',
            '&:hover': {
              backgroundColor: 'rgba(0, 136, 204, 0.2)',
            },
          },
        },
      },
    },
  },
});

// Trading-specific color palette
export const tradingColors = {
  bullish: '#26a69a',
  bearish: '#ef5350',
  neutral: '#d1d4dc',
  volume: '#363a45',
  grid: '#2a2e39',
  crosshair: '#868b98',
  watermark: 'rgba(209, 212, 220, 0.1)',
};

// Chart color scheme for TradingView-like appearance
export const chartColors = {
  background: '#131722',
  gridLines: '#2a2e39',
  textColor: '#d1d4dc',
  candlestick: {
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderUpColor: '#26a69a',
    borderDownColor: '#ef5350',
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  },
  volume: {
    upColor: 'rgba(38, 166, 154, 0.5)',
    downColor: 'rgba(239, 83, 80, 0.5)',
  },
  ma: {
    ma7: '#f7931a',
    ma25: '#627eea',
    ma99: '#e91e63',
  },
  oscillators: {
    rsi: '#9c27b0',
    macd: '#ff5722',
    signal: '#2196f3',
  },
};
