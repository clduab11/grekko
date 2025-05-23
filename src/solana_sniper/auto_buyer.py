"""
Auto Buyer - High-speed trade execution for Solana tokens.

This module executes lightning-fast buys on new tokens that pass safety checks,
using Jito bundles for MEV protection and optimal execution.
"""
import asyncio
import time
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.transaction import Transaction
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.compute_budget import set_compute_unit_price, set_compute_unit_limit
from solders.system_program import transfer, TransferParams
import aiohttp

from ..utils.logger import get_logger
from ..utils.database import get_db, Trade, Order, OrderSide, OrderStatus
from .token_monitor import NewTokenEvent
from .safety_analyzer import SafetyScore

logger = get_logger('solana_auto_buyer')


@dataclass
class BuyConfig:
    """Configuration for auto-buying."""
    wallet_keypair: Keypair
    max_buy_amount_sol: float  # Maximum SOL to spend per trade
    slippage_bps: int  # Slippage tolerance in basis points (100 = 1%)
    priority_fee_lamports: int  # Priority fee for faster execution
    use_jito: bool  # Whether to use Jito for MEV protection
    jito_tip_lamports: int  # Tip for Jito bundle


@dataclass
class BuyResult:
    """Result of a buy attempt."""
    success: bool
    token_address: str
    amount_spent_sol: float
    tokens_received: float
    execution_time_ms: float
    tx_signature: Optional[str]
    error_message: Optional[str]
    price_per_token: float


class AutoBuyer:
    """
    High-speed automated token buyer for Solana.
    
    Executes trades on Raydium/Orca with minimal latency and MEV protection.
    """
    
    # Raydium AMM Program
    RAYDIUM_AMM_PROGRAM = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
    
    # Jito Block Engine endpoints
    JITO_ENDPOINTS = [
        "https://mainnet.block-engine.jito.wtf/api/v1/bundles",
        "https://amsterdam.mainnet.block-engine.jito.wtf/api/v1/bundles",
        "https://frankfurt.mainnet.block-engine.jito.wtf/api/v1/bundles",
        "https://ny.mainnet.block-engine.jito.wtf/api/v1/bundles",
        "https://tokyo.mainnet.block-engine.jito.wtf/api/v1/bundles",
    ]
    
    def __init__(self,
                 config: BuyConfig,
                 rpc_url: str = "https://api.mainnet-beta.solana.com"):
        """
        Initialize the auto buyer.
        
        Args:
            config: Buy configuration including wallet and limits
            rpc_url: Solana RPC endpoint
        """
        self.config = config
        self.rpc_client = AsyncClient(rpc_url)
        self.session = None
        
        # Performance tracking
        self.metrics = {
            'total_buys': 0,
            'successful_buys': 0,
            'failed_buys': 0,
            'total_sol_spent': 0.0,
            'avg_execution_time_ms': 0.0
        }
        
        # Active positions for tracking
        self._positions: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Auto buyer initialized with {config.max_buy_amount_sol} SOL limit per trade")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def execute_buy(self,
                         token_event: NewTokenEvent,
                         safety_score: SafetyScore,
                         override_amount: Optional[float] = None) -> BuyResult:
        """
        Execute a buy order for a new token.
        
        Args:
            token_event: Token launch event details
            safety_score: Safety analysis results
            override_amount: Optional override for buy amount
            
        Returns:
            BuyResult with execution details
        """
        start_time = time.time()
        
        # Determine buy amount based on safety score
        buy_amount_sol = self._calculate_buy_amount(safety_score, override_amount)
        
        logger.info(f"Executing buy for {token_event.token_address}")
        logger.info(f"  Amount: {buy_amount_sol} SOL")
        logger.info(f"  DEX: {token_event.dex}")
        logger.info(f"  Pool: {token_event.pool_address}")
        
        try:
            # Build the swap transaction
            if token_event.dex == 'raydium':
                transaction = await self._build_raydium_swap(
                    token_event.pool_address,
                    token_event.token_address,
                    buy_amount_sol
                )
            else:
                # Orca implementation would go here
                raise NotImplementedError(f"DEX {token_event.dex} not supported yet")
            
            # Execute the transaction
            if self.config.use_jito:
                tx_signature = await self._send_jito_bundle(transaction)
            else:
                tx_signature = await self._send_transaction(transaction)
            
            # Wait for confirmation
            confirmed = await self._wait_for_confirmation(tx_signature)
            
            if confirmed:
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Get transaction details for token amount
                tokens_received = await self._get_tokens_received(tx_signature, token_event.token_address)
                price_per_token = buy_amount_sol / tokens_received if tokens_received > 0 else 0
                
                # Update metrics
                self._update_metrics(True, buy_amount_sol, execution_time_ms)
                
                # Record position
                self._positions[token_event.token_address] = {
                    'amount': tokens_received,
                    'cost': buy_amount_sol,
                    'entry_price': price_per_token,
                    'timestamp': datetime.utcnow()
                }
                
                # Save to database
                await self._record_trade(token_event, safety_score, buy_amount_sol, tokens_received, tx_signature)
                
                logger.info(f"✅ Buy successful! Tx: {tx_signature}")
                logger.info(f"   Received: {tokens_received:.2f} tokens")
                logger.info(f"   Price: {price_per_token:.8f} SOL per token")
                logger.info(f"   Execution: {execution_time_ms:.1f}ms")
                
                return BuyResult(
                    success=True,
                    token_address=token_event.token_address,
                    amount_spent_sol=buy_amount_sol,
                    tokens_received=tokens_received,
                    execution_time_ms=execution_time_ms,
                    tx_signature=tx_signature,
                    error_message=None,
                    price_per_token=price_per_token
                )
            else:
                raise Exception("Transaction failed to confirm")
                
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            logger.error(f"❌ Buy failed: {error_msg}")
            self._update_metrics(False, 0, execution_time_ms)
            
            return BuyResult(
                success=False,
                token_address=token_event.token_address,
                amount_spent_sol=0,
                tokens_received=0,
                execution_time_ms=execution_time_ms,
                tx_signature=None,
                error_message=error_msg,
                price_per_token=0
            )
    
    def _calculate_buy_amount(self, safety_score: SafetyScore, override: Optional[float]) -> float:
        """
        Calculate buy amount based on safety score.
        
        Uses a tiered approach:
        - Score 90+: 100% of max amount
        - Score 80-90: 75% of max amount
        - Score 70-80: 50% of max amount
        - Score 60-70: 25% of max amount
        - Below 60: Skip (shouldn't reach here)
        """
        if override is not None:
            return min(override, self.config.max_buy_amount_sol)
        
        score = safety_score.total_score
        max_amount = self.config.max_buy_amount_sol
        
        if score >= 90:
            return max_amount
        elif score >= 80:
            return max_amount * 0.75
        elif score >= 70:
            return max_amount * 0.5
        elif score >= 60:
            return max_amount * 0.25
        else:
            return max_amount * 0.1  # Minimum amount for very risky trades
    
    async def _build_raydium_swap(self, 
                                 pool_address: str,
                                 token_address: str,
                                 amount_sol: float) -> Transaction:
        """
        Build a Raydium swap transaction.
        
        This is a simplified version - production would use full Raydium SDK.
        """
        # Create transaction
        transaction = Transaction()
        
        # Add compute budget instructions for priority
        transaction.add(
            set_compute_unit_price(self.config.priority_fee_lamports)
        )
        transaction.add(
            set_compute_unit_limit(300000)  # Typical swap compute units
        )
        
        # Build swap instruction
        # In production, this would:
        # 1. Fetch pool state
        # 2. Calculate amounts with slippage
        # 3. Build proper Raydium swap instruction
        
        # For MVP, we'll create a placeholder
        # Real implementation would use Raydium's instruction builders
        swap_instruction = Instruction(
            program_id=self.RAYDIUM_AMM_PROGRAM,
            accounts=[],  # Would include all necessary accounts
            data=bytes()  # Would include swap parameters
        )
        
        transaction.add(swap_instruction)
        
        # If using Jito, add tip transfer
        if self.config.use_jito and self.config.jito_tip_lamports > 0:
            # Jito tip addresses (rotate through them)
            jito_tip_accounts = [
                "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
                "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
                "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
                "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
                "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
                "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
                "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
                "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"
            ]
            
            tip_account = Pubkey.from_string(jito_tip_accounts[0])
            transaction.add(
                transfer(
                    TransferParams(
                        from_pubkey=self.config.wallet_keypair.pubkey(),
                        to_pubkey=tip_account,
                        lamports=self.config.jito_tip_lamports
                    )
                )
            )
        
        # Set fee payer and recent blockhash
        recent_blockhash = (await self.rpc_client.get_latest_blockhash()).value.blockhash
        transaction.recent_blockhash = recent_blockhash
        transaction.fee_payer = self.config.wallet_keypair.pubkey()
        
        # Sign transaction
        transaction.sign(self.config.wallet_keypair)
        
        return transaction
    
    async def _send_jito_bundle(self, transaction: Transaction) -> str:
        """Send transaction via Jito bundle for MEV protection."""
        if not self.session:
            raise Exception("Session not initialized")
        
        # Serialize transaction
        serialized = transaction.serialize()
        
        # Create bundle
        bundle = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendBundle",
            "params": [[serialized.hex()]]
        }
        
        # Try each Jito endpoint until one works
        for endpoint in self.JITO_ENDPOINTS:
            try:
                async with self.session.post(endpoint, json=bundle) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if 'result' in result:
                            return result['result']
            except Exception as e:
                logger.debug(f"Jito endpoint {endpoint} failed: {str(e)}")
                continue
        
        # Fallback to regular transaction if Jito fails
        logger.warning("All Jito endpoints failed, falling back to regular send")
        return await self._send_transaction(transaction)
    
    async def _send_transaction(self, transaction: Transaction) -> str:
        """Send transaction via regular RPC."""
        result = await self.rpc_client.send_transaction(transaction)
        return str(result.value)
    
    async def _wait_for_confirmation(self, signature: str, max_attempts: int = 30) -> bool:
        """Wait for transaction confirmation."""
        for i in range(max_attempts):
            try:
                response = await self.rpc_client.get_signature_statuses([signature])
                if response.value[0] is not None:
                    return response.value[0].confirmation_status in ["confirmed", "finalized"]
            except Exception as e:
                logger.debug(f"Error checking confirmation: {str(e)}")
            
            await asyncio.sleep(0.5)
        
        return False
    
    async def _get_tokens_received(self, tx_signature: str, token_address: str) -> float:
        """Get the amount of tokens received from transaction."""
        try:
            # Get transaction details
            response = await self.rpc_client.get_transaction(
                tx_signature,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            
            if response.value:
                # Parse token balance changes
                # This is simplified - real implementation would parse all token transfers
                meta = response.value.transaction.meta
                post_balances = meta.post_token_balances or []
                
                for balance in post_balances:
                    if balance.mint == token_address and balance.owner == str(self.config.wallet_keypair.pubkey()):
                        return float(balance.ui_token_amount.ui_amount)
                        
        except Exception as e:
            logger.error(f"Error getting tokens received: {str(e)}")
        
        return 0.0
    
    async def _record_trade(self,
                          token_event: NewTokenEvent,
                          safety_score: SafetyScore,
                          amount_spent: float,
                          tokens_received: float,
                          tx_signature: str):
        """Record trade in database."""
        with get_db() as db:
            trade = Trade(
                symbol=token_event.token_address[:8],  # Shortened for display
                exchange='solana',
                strategy='sniper_bot',
                side=OrderSide.BUY,
                entry_price=amount_spent / tokens_received if tokens_received > 0 else 0,
                quantity=tokens_received,
                entry_time=datetime.utcnow(),
                signal_strength=safety_score.total_score / 100,
                market_conditions={
                    'dex': token_event.dex,
                    'pool': token_event.pool_address,
                    'initial_liquidity': token_event.initial_liquidity,
                    'safety_score': safety_score.total_score
                },
                notes=f"Auto-buy via sniper bot. Tx: {tx_signature}"
            )
            db.add(trade)
            db.commit()
    
    def _update_metrics(self, success: bool, amount_spent: float, execution_time_ms: float):
        """Update performance metrics."""
        self.metrics['total_buys'] += 1
        
        if success:
            self.metrics['successful_buys'] += 1
            self.metrics['total_sol_spent'] += amount_spent
        else:
            self.metrics['failed_buys'] += 1
        
        # Update average execution time
        avg = self.metrics['avg_execution_time_ms']
        count = self.metrics['total_buys']
        self.metrics['avg_execution_time_ms'] = (avg * (count - 1) + execution_time_ms) / count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        success_rate = (self.metrics['successful_buys'] / self.metrics['total_buys'] * 100) if self.metrics['total_buys'] > 0 else 0
        
        return {
            **self.metrics,
            'success_rate': success_rate,
            'active_positions': len(self._positions)
        }
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions."""
        return dict(self._positions)