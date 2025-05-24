"""
Database models and connection management for Grekko.

This module provides SQLAlchemy models for trades, positions, metrics,
and manages database connections with proper pooling for high-performance trading.
"""
import os
from datetime import datetime
from decimal import Decimal
from enum import Enum
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Boolean, JSON, Enum as SQLEnum, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.pool import QueuePool
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..utils.logger import get_logger

logger = get_logger('database')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://grekko:grekkopassword@localhost:5432/grekko')

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of persistent connections
    max_overflow=40,  # Maximum overflow connections
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base class for models
Base = declarative_base()


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TradeResult(Enum):
    """Trade result enumeration."""
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    OPEN = "open"


class Trade(Base):
    """
    Trade model for storing executed trades.
    
    This model tracks all trades executed by the system including entry/exit prices,
    P&L, and associated metadata for analysis.
    """
    __tablename__ = 'trades'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Trade identification
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)
    strategy = Column(String(100), nullable=False, index=True)
    
    # Trade details
    side = Column(SQLEnum(OrderSide), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    
    # Timing
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    duration_minutes = Column(Float)
    
    # P&L
    pnl_amount = Column(Float)
    pnl_percentage = Column(Float)
    fees_paid = Column(Float, default=0.0)
    result = Column(SQLEnum(TradeResult), default=TradeResult.OPEN)
    
    # Risk management
    stop_loss = Column(Float)
    take_profit = Column(Float)
    risk_amount = Column(Float)
    
    # Metadata
    signal_strength = Column(Float)
    market_conditions = Column(JSON)  # Store market data at time of trade
    notes = Column(String(500))
    
    # Relationships
    orders = relationship("Order", back_populates="trade")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trades_symbol_time', 'symbol', 'entry_time'),
        Index('idx_trades_strategy_result', 'strategy', 'result'),
    )


class Position(Base):
    """
    Position model for tracking open positions.
    
    Represents current holdings and their real-time P&L status.
    """
    __tablename__ = 'positions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Position identification
    symbol = Column(String(50), nullable=False, unique=True, index=True)
    exchange = Column(String(50), nullable=False)
    
    # Position details
    quantity = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    
    # P&L tracking
    unrealized_pnl = Column(Float)
    unrealized_pnl_pct = Column(Float)
    realized_pnl = Column(Float, default=0.0)
    
    # Risk parameters
    position_value = Column(Float)
    risk_percentage = Column(Float)
    max_position_size = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_check = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    """
    Order model for tracking all order attempts.
    
    Stores both successful and failed orders for audit trail and analysis.
    """
    __tablename__ = 'orders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Order identification
    exchange_order_id = Column(String(100), index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(50), nullable=False)
    
    # Order details
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(String(20), nullable=False)  # market, limit, stop
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    
    # Status tracking
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    filled_quantity = Column(Float, default=0.0)
    avg_fill_price = Column(Float)
    
    # Execution details
    submitted_at = Column(DateTime)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Error handling
    error_message = Column(String(500))
    retry_count = Column(Integer, default=0)
    
    # Foreign keys
    trade_id = Column(UUID(as_uuid=True), ForeignKey('trades.id'))
    trade = relationship("Trade", back_populates="orders")


class PerformanceMetric(Base):
    """
    Performance metrics model for tracking system and strategy performance.
    
    Aggregates performance data for analysis and optimization.
    """
    __tablename__ = 'performance_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metric identification
    metric_type = Column(String(50), nullable=False, index=True)  # strategy, system, exchange
    metric_name = Column(String(100), nullable=False, index=True)
    period = Column(String(20), nullable=False)  # 1h, 1d, 1w, 1m
    
    # Performance data
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # Returns
    total_pnl = Column(Float, default=0.0)
    avg_win_amount = Column(Float)
    avg_loss_amount = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    
    # Risk metrics
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    var_95 = Column(Float)  # Value at Risk 95%
    
    # System metrics
    api_calls = Column(Integer, default=0)
    avg_latency_ms = Column(Float)
    error_count = Column(Integer, default=0)
    uptime_percentage = Column(Float)
    
    # Additional data
    metadata = Column(JSON)


class MarketData(Base):
    """
    Market data model for storing historical price and volume data.
    
    Used for backtesting and analysis.
    """
    __tablename__ = 'market_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(50), nullable=False)
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Additional metrics
    trades_count = Column(Integer)
    vwap = Column(Float)  # Volume Weighted Average Price
    
    __table_args__ = (
        Index('idx_market_data_symbol_time', 'symbol', 'timestamp'),
    )


# Database helper functions
@contextmanager
def get_db():
    """
    Provide a transactional scope for database operations.
    
    Usage:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()


def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def get_recent_trades(symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
    """
    Get recent trades, optionally filtered by symbol.
    
    Args:
        symbol: Optional symbol to filter by
        limit: Maximum number of trades to return
        
    Returns:
        List of Trade objects
    """
    with get_db() as db:
        query = db.query(Trade).order_by(Trade.created_at.desc())
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.limit(limit).all()


def get_open_positions() -> List[Position]:
    """Get all open positions."""
    with get_db() as db:
        return db.query(Position).filter(Position.is_active == True).all()


def update_position_price(symbol: str, current_price: float) -> Optional[Position]:
    """
    Update the current price for a position and recalculate P&L.
    
    Args:
        symbol: The symbol to update
        current_price: The current market price
        
    Returns:
        Updated Position object or None
    """
    with get_db() as db:
        position = db.query(Position).filter(Position.symbol == symbol).first()
        if position:
            position.current_price = current_price
            position.unrealized_pnl = (current_price - position.avg_entry_price) * position.quantity
            position.unrealized_pnl_pct = (current_price / position.avg_entry_price - 1) * 100
            position.position_value = current_price * position.quantity
            position.last_check = datetime.utcnow()
            db.commit()
        return position


if __name__ == "__main__":
    # Initialize database if running directly
    init_db()
    logger.info("Database setup complete")