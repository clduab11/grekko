"""
Token Monitor - Real-time monitoring of new Solana token launches.

This module connects to Helius RPC via WebSocket to monitor new Raydium/Orca pools
in real-time, detecting new token launches the moment they hit the blockchain.
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
import websockets
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature

from ..utils.logger import get_logger
from ..utils.database import get_db, MarketData

logger = get_logger('solana_token_monitor')


@dataclass
class NewTokenEvent:
    """Data class for new token launch events."""
    timestamp: datetime
    token_address: str
    pool_address: str
    dex: str  # 'raydium' or 'orca'
    base_mint: str  # Usually SOL
    quote_mint: str  # The new token
    initial_liquidity: float
    initial_price: float
    tx_signature: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'token_address': self.token_address,
            'pool_address': self.pool_address,
            'dex': self.dex,
            'base_mint': self.base_mint,
            'quote_mint': self.quote_mint,
            'initial_liquidity': self.initial_liquidity,
            'initial_price': self.initial_price,
            'tx_signature': self.tx_signature
        }


class TokenMonitor:
    """
    High-performance token monitor for Solana DEXs.
    
    Monitors Raydium and Orca pool creation events in real-time using
    WebSocket connections to detect new token launches instantly.
    """
    
    # Raydium V2 AMM Program
    RAYDIUM_AMM_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
    # Orca Whirlpool Program
    ORCA_WHIRLPOOL_PROGRAM = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
    
    # Known stable coins and base tokens (not new launches)
    KNOWN_TOKENS = {
        "So11111111111111111111111111111111111111112",  # SOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
        "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",  # ETH
        "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",   # mSOL
    }
    
    def __init__(self, 
                 helius_api_key: str,
                 helius_ws_url: Optional[str] = None,
                 callback: Optional[Callable[[NewTokenEvent], None]] = None):
        """
        Initialize the token monitor.
        
        Args:
            helius_api_key: Helius API key for authentication
            helius_ws_url: Optional WebSocket URL (defaults to Helius)
            callback: Optional callback function for new token events
        """
        self.api_key = helius_api_key
        self.ws_url = helius_ws_url or f"wss://atlas-mainnet.helius-rpc.com/?api-key={helius_api_key}"
        self.callback = callback
        self.is_running = False
        self._ws_connection = None
        self._monitored_pools = set()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {
            'events_received': 0,
            'new_tokens_found': 0,
            'avg_detection_time_ms': 0,
            'last_event_time': None
        }
        
        logger.info("Token monitor initialized for Raydium and Orca DEXs")
    
    async def start(self):
        """Start monitoring for new tokens."""
        self.is_running = True
        logger.info("Starting Solana token monitor...")
        
        # Start WebSocket listener and event processor in parallel
        await asyncio.gather(
            self._websocket_listener(),
            self._event_processor(),
            return_exceptions=True
        )
    
    async def stop(self):
        """Stop monitoring."""
        logger.info("Stopping token monitor...")
        self.is_running = False
        
        if self._ws_connection:
            await self._ws_connection.close()
    
    async def _websocket_listener(self):
        """
        WebSocket listener that subscribes to program logs.
        
        Monitors Raydium and Orca program accounts for pool creation events.
        """
        while self.is_running:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self._ws_connection = websocket
                    logger.info("WebSocket connected to Helius RPC")
                    
                    # Subscribe to Raydium AMM logs
                    await self._subscribe_to_program(websocket, self.RAYDIUM_AMM_PROGRAM)
                    
                    # Subscribe to Orca Whirlpool logs
                    await self._subscribe_to_program(websocket, self.ORCA_WHIRLPOOL_PROGRAM)
                    
                    # Listen for events
                    async for message in websocket:
                        if not self.is_running:
                            break
                            
                        await self._handle_websocket_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}, reconnecting in 10s...")
                await asyncio.sleep(10)
    
    async def _subscribe_to_program(self, websocket, program_id: str):
        """Subscribe to program logs for a specific program."""
        subscription = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {
                    "mentions": [program_id]
                },
                {
                    "commitment": "confirmed"
                }
            ]
        }
        
        await websocket.send(json.dumps(subscription))
        logger.info(f"Subscribed to program logs: {program_id}")
    
    async def _handle_websocket_message(self, message: str):
        """
        Handle incoming WebSocket messages.
        
        Parses log messages to detect new pool creation events.
        """
        try:
            data = json.loads(message)
            
            # Check if this is a notification (not a subscription response)
            if 'method' in data and data['method'] == 'logsNotification':
                result = data['params']['result']
                signature = result['value']['signature']
                logs = result['value']['logs']
                
                # Quick check if this might be a pool creation
                pool_creation_keywords = [
                    'InitializePool',
                    'CreatePool', 
                    'initialize',
                    'create_pool'
                ]
                
                if any(keyword in log for log in logs for keyword in pool_creation_keywords):
                    # Queue for detailed processing
                    await self._event_queue.put({
                        'signature': signature,
                        'logs': logs,
                        'timestamp': time.time()
                    })
                    
                self.metrics['events_received'] += 1
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
    
    async def _event_processor(self):
        """
        Process events from the queue to identify new token launches.
        
        This runs separately from the WebSocket listener to avoid blocking.
        """
        rpc_client = AsyncClient("https://api.mainnet-beta.solana.com")
        
        while self.is_running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                # Process the event
                signature = event['signature']
                logs = event['logs']
                
                # Fetch full transaction details
                tx_details = await self._get_transaction_details(rpc_client, signature)
                
                if tx_details:
                    # Check if this is a new token launch
                    new_token = await self._identify_new_token(tx_details, logs)
                    
                    if new_token:
                        # Calculate detection time
                        detection_time_ms = (time.time() - event['timestamp']) * 1000
                        self._update_metrics(detection_time_ms)
                        
                        logger.info(f"🚀 NEW TOKEN DETECTED: {new_token.token_address}")
                        logger.info(f"  DEX: {new_token.dex}")
                        logger.info(f"  Pool: {new_token.pool_address}")
                        logger.info(f"  Initial Liquidity: ${new_token.initial_liquidity:,.2f}")
                        logger.info(f"  Detection Time: {detection_time_ms:.1f}ms")
                        
                        # Call callback if provided
                        if self.callback:
                            await self._safe_callback(new_token)
                            
            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
    
    async def _get_transaction_details(self, client: AsyncClient, signature: str) -> Optional[Dict]:
        """Fetch full transaction details from RPC."""
        try:
            sig = Signature.from_string(signature)
            response = await client.get_transaction(
                sig,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            
            if response.value:
                return response.value.to_json()
            
        except Exception as e:
            logger.error(f"Error fetching transaction {signature}: {str(e)}")
        
        return None
    
    async def _identify_new_token(self, tx_details: Dict, logs: List[str]) -> Optional[NewTokenEvent]:
        """
        Analyze transaction to identify if it's a new token launch.
        
        Returns NewTokenEvent if this is a legitimate new token launch.
        """
        try:
            # Extract relevant data from transaction
            meta = tx_details.get('meta', {})
            transaction = tx_details.get('transaction', {})
            
            # Check if transaction was successful
            if meta.get('err') is not None:
                return None
            
            # Parse instructions to find pool creation
            instructions = transaction.get('message', {}).get('instructions', [])
            
            for instruction in instructions:
                program_id = instruction.get('programId', '')
                
                # Check if this is a Raydium pool initialization
                if program_id == self.RAYDIUM_AMM_PROGRAM:
                    pool_info = self._parse_raydium_pool_creation(instruction, meta)
                    if pool_info:
                        return pool_info
                
                # Check if this is an Orca pool initialization
                elif program_id == self.ORCA_WHIRLPOOL_PROGRAM:
                    pool_info = self._parse_orca_pool_creation(instruction, meta)
                    if pool_info:
                        return pool_info
            
        except Exception as e:
            logger.error(f"Error identifying new token: {str(e)}")
        
        return None
    
    def _parse_raydium_pool_creation(self, instruction: Dict, meta: Dict) -> Optional[NewTokenEvent]:
        """Parse Raydium pool creation instruction."""
        # This is a simplified parser - in production, you'd decode the full instruction
        # For MVP, we'll do basic parsing
        
        try:
            # Check if this looks like a pool creation
            if 'parsed' not in instruction:
                return None
                
            parsed = instruction.get('parsed', {})
            if parsed.get('type') != 'initializePool':
                return None
            
            info = parsed.get('info', {})
            
            # Extract token mints
            token_a = info.get('tokenMintA', '')
            token_b = info.get('tokenMintB', '')
            
            # Identify which is the new token (not SOL/USDC/etc)
            new_token = None
            base_token = None
            
            if token_a not in self.KNOWN_TOKENS:
                new_token = token_a
                base_token = token_b
            elif token_b not in self.KNOWN_TOKENS:
                new_token = token_b
                base_token = token_a
            else:
                # Both tokens are known, not a new launch
                return None
            
            # Extract liquidity info from token balances
            post_balances = meta.get('postTokenBalances', [])
            initial_liquidity = self._calculate_initial_liquidity(post_balances, base_token)
            
            return NewTokenEvent(
                timestamp=datetime.utcnow(),
                token_address=new_token,
                pool_address=info.get('poolAccount', ''),
                dex='raydium',
                base_mint=base_token,
                quote_mint=new_token,
                initial_liquidity=initial_liquidity,
                initial_price=0.0,  # Calculate from pool ratios
                tx_signature=instruction.get('signature', '')
            )
            
        except Exception as e:
            logger.debug(f"Error parsing Raydium instruction: {str(e)}")
        
        return None
    
    def _parse_orca_pool_creation(self, instruction: Dict, meta: Dict) -> Optional[NewTokenEvent]:
        """Parse Orca pool creation instruction."""
        # Similar structure to Raydium parser
        # Implementation would decode Orca-specific instruction format
        return None
    
    def _calculate_initial_liquidity(self, token_balances: List[Dict], base_token: str) -> float:
        """Calculate initial liquidity in USD from token balances."""
        # Simplified calculation - in production, fetch real-time prices
        sol_price = 150.0  # Hardcoded for MVP
        
        for balance in token_balances:
            if balance.get('mint') == base_token:
                amount = float(balance.get('uiTokenAmount', {}).get('uiAmount', 0))
                return amount * sol_price
        
        return 0.0
    
    def _update_metrics(self, detection_time_ms: float):
        """Update performance metrics."""
        self.metrics['new_tokens_found'] += 1
        self.metrics['last_event_time'] = datetime.utcnow()
        
        # Update average detection time
        avg = self.metrics['avg_detection_time_ms']
        count = self.metrics['new_tokens_found']
        self.metrics['avg_detection_time_ms'] = (avg * (count - 1) + detection_time_ms) / count
    
    async def _safe_callback(self, event: NewTokenEvent):
        """Safely execute callback function."""
        try:
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(event)
            else:
                self.callback(event)
        except Exception as e:
            logger.error(f"Error in callback: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return dict(self.metrics)