import React, { useEffect, useRef, useState } from 'react';
import { Box, IconButton, Tooltip, Chip } from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  ShowChart,
  BarChart,
  Timeline,
} from '@mui/icons-material';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { useAppSelector, useAppDispatch } from '../../store/store';
import { updateChartSettings } from '../../store/slices/uiSlice';

const TradingChart: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  const dispatch = useAppDispatch();
  const { candlestickData, currentSymbol, tickers } = useAppSelector((state: any) => state.marketData);
  const { chartSettings, theme } = useAppSelector((state: any) => state.ui);

  const [lastPrice, setLastPrice] = useState<number | null>(null);
  const [priceDirection, setPriceDirection] = useState<'up' | 'down' | 'neutral'>('neutral');

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#363c4e' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#485c7b',
      },
      timeScale: {
        borderColor: '#485c7b',
        timeVisible: true,
        secondsVisible: false,
      },
      watermark: {
        visible: true,
        fontSize: 24,
        horzAlign: 'center',
        vertAlign: 'center',
        color: 'rgba(171, 71, 188, 0.3)',
        text: 'GREKKO',
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Add volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });

    chart.priceScale('').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    volumeSeriesRef.current = volumeSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, []);

  // Update chart data
  useEffect(() => {
    if (candlestickSeriesRef.current && candlestickData.length > 0) {
      const chartData = candlestickData.map((candle: any) => ({
        time: candle.time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      }));

      const volumeData = candlestickData.map((candle: any) => ({
        time: candle.time,
        value: candle.volume,
        color: candle.close >= candle.open ? '#26a69a' : '#ef5350',
      }));

      candlestickSeriesRef.current.setData(chartData);
      volumeSeriesRef.current?.setData(volumeData);

      // Update price direction
      if (chartData.length > 1) {
        const currentPrice = chartData[chartData.length - 1].close;
        const previousPrice = chartData[chartData.length - 2].close;
        
        if (lastPrice !== null) {
          if (currentPrice > lastPrice) {
            setPriceDirection('up');
          } else if (currentPrice < lastPrice) {
            setPriceDirection('down');
          }
        }
        
        setLastPrice(currentPrice);
      }
    }
  }, [candlestickData, lastPrice]);

  // Current ticker for the selected symbol
  const currentTicker = tickers[currentSymbol];

  const handleChartTypeChange = (type: 'candlestick' | 'hollow_candlestick' | 'line' | 'area') => {
    dispatch(updateChartSettings({ candlestickType: type }));
  };

  return (
    <Box sx={{ height: '100%', position: 'relative' }}>
      {/* Chart Controls */}
      <Box
        sx={{
          position: 'absolute',
          top: 10,
          left: 10,
          zIndex: 10,
          display: 'flex',
          gap: 1,
          alignItems: 'center',
        }}
      >
        {/* Chart Type Selector */}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="Candlesticks">
            <IconButton
              size="small"
              onClick={() => handleChartTypeChange('candlestick')}
              sx={{
                color: chartSettings.candlestickType === 'candlestick' ? '#0088cc' : '#666',
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
              }}
            >
              <BarChart fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Line Chart">
            <IconButton
              size="small"
              onClick={() => handleChartTypeChange('line')}
              sx={{
                color: chartSettings.candlestickType === 'line' ? '#0088cc' : '#666',
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
              }}
            >
              <ShowChart fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Area Chart">
            <IconButton
              size="small"
              onClick={() => handleChartTypeChange('area')}
              sx={{
                color: chartSettings.candlestickType === 'area' ? '#0088cc' : '#666',
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
              }}
            >
              <Timeline fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Price Info */}
      {currentTicker && (
        <Box
          sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            zIndex: 10,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            padding: 1,
            borderRadius: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: 0.5,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {priceDirection === 'up' && <TrendingUp color="success" fontSize="small" />}
            {priceDirection === 'down' && <TrendingDown color="error" fontSize="small" />}
            
            <Box sx={{ color: 'white', fontSize: '1.2rem', fontWeight: 'bold' }}>
              ${currentTicker.price.toFixed(4)}
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip
              label={`${currentTicker.changePercent24h >= 0 ? '+' : ''}${currentTicker.changePercent24h.toFixed(2)}%`}
              color={currentTicker.changePercent24h >= 0 ? 'success' : 'error'}
              size="small"
            />
            <Chip
              label={`Vol: ${(currentTicker.volume24h / 1000000).toFixed(1)}M`}
              size="small"
              variant="outlined"
              sx={{ color: '#999' }}
            />
          </Box>
        </Box>
      )}

      {/* Chart Container */}
      <Box
        ref={chartContainerRef}
        sx={{
          width: '100%',
          height: '100%',
          '& > div': {
            borderRadius: 0,
          },
        }}
      />

      {/* Loading State */}
      {candlestickData.length === 0 && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            color: '#666',
            fontSize: '1.1rem',
          }}
        >
          Loading chart data...
        </Box>
      )}
    </Box>
  );
};

export default TradingChart;
