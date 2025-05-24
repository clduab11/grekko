"""
Grekko API - FastAPI application for bot control and monitoring.

This module provides REST endpoints and WebSocket connections for:
- Bot control (start/stop/configure)
- Real-time monitoring
- Position tracking
- Performance metrics
"""
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn
from solana.keypair import Keypair

from ..utils.logger import get_logger
from ..utils.database import get_db, Trade, Position, PerformanceMetric, get_recent_trades, get_open_positions
from ..solana_sniper import TokenMonitor, SafetyAnalyzer, AutoBuyer
from ..solana_sniper.token_monitor import NewTokenEvent
from ..solana_sniper.auto_buyer import BuyConfig

logger = get_logger('grekko_api')

# Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token verification - in production use proper JWT."""
    token = credentials.credentials
    expected_token = os.getenv('API_TOKEN', 'grekko-secret-token')
    
    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token


# Pydantic models for API
class BotConfig(BaseModel):
    """Configuration for the sniper bot."""
    max_buy_amount_sol: float = Field(0.1, gt=0, le=10, description="Max SOL per trade")
    min_safety_score: float = Field(70.0, ge=0, le=100, description="Minimum safety score")
    slippage_bps: int = Field(300, ge=100, le=1000, description="Slippage in basis points")
    use_jito: bool = Field(True, description="Use Jito for MEV protection")
    priority_fee_lamports: int = Field(10000, ge=0, description="Priority fee")
    jito_tip_lamports: int = Field(100000, ge=0, description="Jito tip")


class BotStatus(BaseModel):
    """Current bot status."""
    is_running: bool
    start_time: Optional[datetime]
    config: BotConfig
    metrics: Dict[str, Any]
    active_positions: int


class TokenAlert(BaseModel):
    """New token alert."""
    timestamp: datetime
    token_address: str
    dex: str
    initial_liquidity: float
    safety_score: float
    action_taken: str


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._broadcaster_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Queue a message for broadcasting."""
        await self._message_queue.put(message)
    
    async def start_broadcaster(self):
        """Start the background broadcaster task."""
        self._broadcaster_task = asyncio.create_task(self._broadcast_worker())
    
    async def stop_broadcaster(self):
        """Stop the broadcaster task."""
        if self._broadcaster_task:
            self._broadcaster_task.cancel()
            try:
                await self._broadcaster_task
            except asyncio.CancelledError:
                pass
    
    async def _broadcast_worker(self):
        """Background worker that broadcasts messages to all connections."""
        while True:
            try:
                # Get message from queue
                message = await self._message_queue.get()
                
                # Send to all active connections
                disconnected = []
                for connection in self.active_connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.debug(f"Failed to send to WebSocket: {str(e)}")
                        disconnected.append(connection)
                
                # Clean up disconnected clients
                for conn in disconnected:
                    self.disconnect(conn)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Broadcaster error: {str(e)}")


# Global instances
websocket_manager = WebSocketManager()
bot_instance: Optional['SniperBot'] = None


class SniperBot:
    """Main sniper bot controller."""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Initialize components
        helius_api_key = os.getenv('HELIUS_API_KEY', '')
        if not helius_api_key:
            raise ValueError("HELIUS_API_KEY environment variable not set")
        
        # Load wallet from environment
        wallet_private_key = os.getenv('SOLANA_WALLET_PRIVATE_KEY', '')
        if not wallet_private_key:
            raise ValueError("SOLANA_WALLET_PRIVATE_KEY environment variable not set")
        
        self.wallet = Keypair.from_secret_key(bytes.fromhex(wallet_private_key))
        
        # Create buy config
        buy_config = BuyConfig(
            wallet_keypair=self.wallet,
            max_buy_amount_sol=config.max_buy_amount_sol,
            slippage_bps=config.slippage_bps,
            priority_fee_lamports=config.priority_fee_lamports,
            use_jito=config.use_jito,
            jito_tip_lamports=config.jito_tip_lamports
        )
        
        # Initialize components
        self.token_monitor = TokenMonitor(
            helius_api_key=helius_api_key,
            callback=self._on_new_token
        )
        self.safety_analyzer = SafetyAnalyzer()
        self.auto_buyer = AutoBuyer(buy_config)
        
        logger.info("Sniper bot initialized")
    
    async def start(self):
        """Start the sniper bot."""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        logger.info("Starting sniper bot...")
        
        # Start components
        await self.auto_buyer.__aenter__()
        await self.safety_analyzer.__aenter__()
        
        # Start token monitor
        asyncio.create_task(self.token_monitor.start())
        
        # Broadcast status
        await websocket_manager.broadcast({
            'type': 'bot_status',
            'data': {
                'is_running': True,
                'message': 'Sniper bot started'
            }
        })
    
    async def stop(self):
        """Stop the sniper bot."""
        if not self.is_running:
            return
        
        logger.info("Stopping sniper bot...")
        
        self.is_running = False
        
        # Stop components
        await self.token_monitor.stop()
        await self.auto_buyer.__aexit__(None, None, None)
        await self.safety_analyzer.__aexit__(None, None, None)
        
        # Broadcast status
        await websocket_manager.broadcast({
            'type': 'bot_status',
            'data': {
                'is_running': False,
                'message': 'Sniper bot stopped'
            }
        })
    
    async def _on_new_token(self, event: NewTokenEvent):
        """Handle new token detection."""
        logger.info(f"New token detected: {event.token_address}")
        
        # Broadcast alert immediately
        await websocket_manager.broadcast({
            'type': 'new_token',
            'data': event.to_dict()
        })
        
        try:
            # Analyze token safety
            safety_score = await self.safety_analyzer.analyze_token(
                event.token_address,
                event.pool_address,
                event.initial_liquidity
            )
            
            # Broadcast safety analysis
            await websocket_manager.broadcast({
                'type': 'safety_analysis',
                'data': {
                    'token_address': event.token_address,
                    'safety_score': safety_score.total_score,
                    'red_flags': safety_score.red_flags,
                    'verdict': self.safety_analyzer.get_quick_verdict(safety_score)
                }
            })
            
            # Check if we should buy
            if safety_score.is_safe(self.config.min_safety_score):
                # Execute buy
                result = await self.auto_buyer.execute_buy(event, safety_score)
                
                # Broadcast result
                await websocket_manager.broadcast({
                    'type': 'trade_result',
                    'data': {
                        'success': result.success,
                        'token_address': result.token_address,
                        'amount_spent': result.amount_spent_sol,
                        'tokens_received': result.tokens_received,
                        'execution_time_ms': result.execution_time_ms,
                        'error': result.error_message
                    }
                })
            else:
                logger.info(f"Skipping {event.token_address} - safety score too low: {safety_score.total_score}")
                
        except Exception as e:
            logger.error(f"Error processing token {event.token_address}: {str(e)}")
            
            await websocket_manager.broadcast({
                'type': 'error',
                'data': {
                    'token_address': event.token_address,
                    'error': str(e)
                }
            })
    
    def get_status(self) -> BotStatus:
        """Get current bot status."""
        return BotStatus(
            is_running=self.is_running,
            start_time=self.start_time,
            config=self.config,
            metrics=self.auto_buyer.get_metrics() if self.auto_buyer else {},
            active_positions=len(self.auto_buyer.get_positions()) if self.auto_buyer else 0
        )


# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting Grekko API...")
    await websocket_manager.start_broadcaster()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Grekko API...")
    if bot_instance and bot_instance.is_running:
        await bot_instance.stop()
    await websocket_manager.stop_broadcaster()


# Create FastAPI app
app = FastAPI(
    title="Grekko Trading Bot API",
    description="High-frequency Solana token sniper bot",
    version="0.3.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Grekko Trading Bot",
        "version": "0.3.0"
    }


@app.post("/bot/start", dependencies=[Depends(verify_token)])
async def start_bot(config: BotConfig):
    """Start the sniper bot with given configuration."""
    global bot_instance
    
    try:
        if bot_instance and bot_instance.is_running:
            raise HTTPException(400, "Bot is already running")
        
        # Create new bot instance
        bot_instance = SniperBot(config)
        await bot_instance.start()
        
        return {
            "status": "success",
            "message": "Bot started successfully",
            "config": config.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise HTTPException(500, f"Failed to start bot: {str(e)}")


@app.post("/bot/stop", dependencies=[Depends(verify_token)])
async def stop_bot():
    """Stop the sniper bot."""
    global bot_instance
    
    if not bot_instance or not bot_instance.is_running:
        raise HTTPException(400, "Bot is not running")
    
    await bot_instance.stop()
    
    return {
        "status": "success",
        "message": "Bot stopped successfully"
    }


@app.get("/bot/status")
async def get_bot_status():
    """Get current bot status."""
    if not bot_instance:
        return BotStatus(
            is_running=False,
            start_time=None,
            config=BotConfig(),
            metrics={},
            active_positions=0
        )
    
    return bot_instance.get_status()


@app.get("/bot/positions")
async def get_positions():
    """Get current token positions."""
    if not bot_instance:
        return {"positions": {}}
    
    return {"positions": bot_instance.auto_buyer.get_positions()}


@app.get("/trades/recent")
async def get_recent_trades_endpoint(limit: int = 100):
    """Get recent trades from database."""
    trades = get_recent_trades(limit=limit)
    
    return {
        "trades": [
            {
                "id": str(trade.id),
                "timestamp": trade.created_at.isoformat(),
                "symbol": trade.symbol,
                "side": trade.side.value,
                "entry_price": trade.entry_price,
                "quantity": trade.quantity,
                "pnl": trade.pnl_percentage,
                "result": trade.result.value if trade.result else "open"
            }
            for trade in trades
        ]
    }


@app.get("/metrics/performance")
async def get_performance_metrics():
    """Get bot performance metrics."""
    with get_db() as db:
        # Get last 24h metrics
        recent_metrics = db.query(PerformanceMetric)\
            .filter(PerformanceMetric.metric_type == 'sniper_bot')\
            .order_by(PerformanceMetric.timestamp.desc())\
            .first()
        
        if recent_metrics:
            return {
                "win_rate": recent_metrics.win_rate,
                "total_pnl": recent_metrics.total_pnl,
                "total_trades": recent_metrics.total_trades,
                "sharpe_ratio": recent_metrics.sharpe_ratio,
                "max_drawdown": recent_metrics.max_drawdown
            }
        else:
            return {
                "win_rate": 0,
                "total_pnl": 0,
                "total_trades": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0
            }


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket_manager.connect(websocket)
    
    try:
        # Send initial status
        if bot_instance:
            await websocket.send_json({
                'type': 'bot_status',
                'data': bot_instance.get_status().dict()
            })
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)


if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )