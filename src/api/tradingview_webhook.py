"""
TradingView Webhook Microservice for Grekko

- Exposes a secure POST endpoint for TradingView alerts.
- Validates incoming JSON and secret.
- Executes trades in sandbox/testnet via Grekko ExecutionManager.
- Logs all actions and returns result.
"""

import os
import asyncio
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from starlette.middleware.cors import CORSMiddleware

from ..utils.logger import get_logger
from ..execution.execution_manager import ExecutionManager, OrderType
from ..risk_management.risk_manager import RiskManager

# --- Configuration ---
WEBHOOK_SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "changeme")
ALLOWED_IPS = os.getenv("TRADINGVIEW_ALLOWED_IPS", "")  # Comma-separated, optional

logger = get_logger("tradingview_webhook")

# --- FastAPI app ---
app = FastAPI(
    title="TradingView Webhook for Grekko",
    description="Receives TradingView alerts and triggers sandboxed trades.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic model for TradingView alert ---
class TradingViewAlert(BaseModel):
    symbol: str = Field(..., description="Trading pair symbol, e.g. BTCUSDT")
    price: float = Field(..., gt=0, description="Current price from TradingView")
    side: str = Field(..., regex="^(buy|sell)$", description="Trade direction")
    strategy_id: Optional[str] = Field(None, description="Strategy identifier")
    size: float = Field(..., gt=0, description="Order size (base units)")
    secret: str = Field(..., description="Webhook secret for validation")
    leverage: Optional[float] = Field(1, ge=1, le=5, description="Leverage (sandbox only)")
    exchange: Optional[str] = Field(None, description="Exchange to use (optional)")

# --- Security dependencies ---
def verify_ip(request: Request):
    if not ALLOWED_IPS:
        return
    client_ip = request.client.host
    allowed = [ip.strip() for ip in ALLOWED_IPS.split(",") if ip.strip()]
    if allowed and client_ip not in allowed:
        logger.warning(f"Rejected webhook from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="IP not allowed")

def verify_secret(alert: TradingViewAlert):
    if alert.secret != WEBHOOK_SECRET:
        logger.warning("Rejected webhook: invalid secret")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

# --- Initialize Grekko ExecutionManager in sandbox mode ---
# In production, load config from file/env and ensure testnet/sandbox is used.
# Set a default sandbox capital for test trading (e.g., $10,000)
risk_manager = RiskManager(
    capital=10000,
    max_trade_size_pct=0.15,  # 15% per trade
    max_drawdown_pct=0.10     # 10% max drawdown
)
execution_manager = ExecutionManager(
    config={
        "sandbox": True,
        "exchanges": {
            "binance": {"testnet": True},
            "coinbase": {"testnet": True}
        }
    },
    risk_manager=risk_manager
)

# --- Webhook endpoint ---
@app.post("/api/v1/tradingview/hook")
async def tradingview_hook(
    request: Request,
    alert: TradingViewAlert = Depends()
):
    # IP allowlist check
    verify_ip(request)
    # Secret check
    verify_secret(alert)

    # Log received data
    logger.info(f"Received TradingView alert: {alert.dict(exclude={'secret'})}")

    # Parameter restrictions (sandbox only)
    leverage = min(alert.leverage or 1, 5)
    size = min(alert.size, 1000)

    # Execute trade in sandbox
    try:
        result = await execution_manager.execute_order(
            symbol=alert.symbol,
            side=alert.side,
            amount=size,
            order_type=OrderType.MARKET,
            price=alert.price,
            exchange=alert.exchange,
            leverage=leverage,
            strategy_id=alert.strategy_id,
            sandbox=True
        )
        logger.info(f"Trade executed: {result}")
        # Optionally, send result to TradingView (if feedback URL is set in alert)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "order_result": result
            }
        )
    except Exception as e:
        logger.error(f"Trade execution failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )