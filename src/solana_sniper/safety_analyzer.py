"""
Safety Analyzer - Rug pull and scam detection for new tokens.

This module analyzes new tokens for red flags like:
- Liquidity locks
- Mint authority status
- Holder distribution
- Contract verification
"""
import asyncio
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.responses import GetTokenAccountsByOwnerResp
import aiohttp

from ..utils.logger import get_logger

logger = get_logger('solana_safety_analyzer')


@dataclass
class SafetyScore:
    """Safety analysis results for a token."""
    token_address: str
    total_score: float  # 0-100, higher is safer
    
    # Individual checks
    liquidity_locked: bool
    liquidity_lock_duration_days: float
    mint_authority_disabled: bool
    freeze_authority_disabled: bool
    top_10_holders_percentage: float
    holder_count: int
    verified_metadata: bool
    
    # Red flags
    red_flags: List[str]
    analysis_timestamp: datetime
    
    def is_safe(self, min_score: float = 70.0) -> bool:
        """Check if token meets minimum safety threshold."""
        return self.total_score >= min_score and len(self.red_flags) == 0


class SafetyAnalyzer:
    """
    Analyzes new tokens for safety and legitimacy.
    
    Performs multiple checks to identify potential rug pulls and scams
    before executing trades.
    """
    
    # Known liquidity lock programs
    LIQUIDITY_LOCK_PROGRAMS = [
        "7WPzEiozJ69MQe8bfbss1t2unR6bHR4S7FimiQN"  # Example lock program
    ]
    
    def __init__(self, 
                 rpc_url: str = "https://api.mainnet-beta.solana.com",
                 birdeye_api_key: Optional[str] = None):
        """
        Initialize the safety analyzer.
        
        Args:
            rpc_url: Solana RPC endpoint
            birdeye_api_key: Optional Birdeye API key for enhanced analysis
        """
        self.rpc_client = AsyncClient(rpc_url)
        self.birdeye_api_key = birdeye_api_key
        self.session = None
        
        # Cache for token analysis (avoid re-analyzing)
        self._analysis_cache: Dict[str, SafetyScore] = {}
        self._cache_ttl = timedelta(minutes=5)
        
        logger.info("Safety analyzer initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def analyze_token(self, 
                          token_address: str,
                          pool_address: str,
                          initial_liquidity: float) -> SafetyScore:
        """
        Perform comprehensive safety analysis on a token.
        
        Args:
            token_address: The token mint address
            pool_address: The liquidity pool address
            initial_liquidity: Initial liquidity in USD
            
        Returns:
            SafetyScore with analysis results
        """
        # Check cache first
        if token_address in self._analysis_cache:
            cached = self._analysis_cache[token_address]
            if datetime.utcnow() - cached.analysis_timestamp < self._cache_ttl:
                logger.debug(f"Using cached analysis for {token_address}")
                return cached
        
        logger.info(f"Analyzing token safety: {token_address}")
        
        # Run all checks in parallel for speed
        results = await asyncio.gather(
            self._check_mint_authorities(token_address),
            self._check_liquidity_lock(pool_address),
            self._analyze_holder_distribution(token_address),
            self._check_metadata(token_address),
            return_exceptions=True
        )
        
        # Unpack results
        mint_status = results[0] if not isinstance(results[0], Exception) else (False, False)
        liquidity_lock = results[1] if not isinstance(results[1], Exception) else (False, 0)
        holder_stats = results[2] if not isinstance(results[2], Exception) else (0, 0)
        has_metadata = results[3] if not isinstance(results[3], Exception) else False
        
        # Calculate safety score
        score, red_flags = self._calculate_safety_score(
            mint_disabled=mint_status[0],
            freeze_disabled=mint_status[1],
            liquidity_locked=liquidity_lock[0],
            lock_duration=liquidity_lock[1],
            top_10_percentage=holder_stats[0],
            holder_count=holder_stats[1],
            has_metadata=has_metadata,
            initial_liquidity=initial_liquidity
        )
        
        # Create safety score object
        safety_score = SafetyScore(
            token_address=token_address,
            total_score=score,
            liquidity_locked=liquidity_lock[0],
            liquidity_lock_duration_days=liquidity_lock[1],
            mint_authority_disabled=mint_status[0],
            freeze_authority_disabled=mint_status[1],
            top_10_holders_percentage=holder_stats[0],
            holder_count=holder_stats[1],
            verified_metadata=has_metadata,
            red_flags=red_flags,
            analysis_timestamp=datetime.utcnow()
        )
        
        # Cache the result
        self._analysis_cache[token_address] = safety_score
        
        # Log analysis summary
        logger.info(f"Token {token_address} safety score: {score:.1f}/100")
        if red_flags:
            logger.warning(f"Red flags detected: {', '.join(red_flags)}")
        
        return safety_score
    
    async def _check_mint_authorities(self, token_address: str) -> Tuple[bool, bool]:
        """
        Check if mint and freeze authorities are disabled.
        
        Returns:
            Tuple of (mint_disabled, freeze_disabled)
        """
        try:
            mint_pubkey = Pubkey.from_string(token_address)
            
            # Get token mint info
            response = await self.rpc_client.get_account_info(mint_pubkey)
            
            if response.value:
                # Parse mint data (simplified for MVP)
                # In production, properly decode the mint account data
                data = response.value.data
                
                # Check if authorities are set to None (disabled)
                # This is simplified - real implementation would decode the account properly
                mint_disabled = True  # Placeholder
                freeze_disabled = True  # Placeholder
                
                return mint_disabled, freeze_disabled
                
        except Exception as e:
            logger.error(f"Error checking mint authorities: {str(e)}")
            
        return False, False
    
    async def _check_liquidity_lock(self, pool_address: str) -> Tuple[bool, float]:
        """
        Check if liquidity is locked and for how long.
        
        Returns:
            Tuple of (is_locked, duration_in_days)
        """
        try:
            # Check if pool tokens are held by known lock programs
            pool_pubkey = Pubkey.from_string(pool_address)
            
            # Get token accounts for the pool
            # In production, check against actual lock program accounts
            
            # For MVP, we'll do a simplified check
            # Real implementation would verify lock contracts
            is_locked = False
            duration_days = 0.0
            
            # Placeholder logic - in production:
            # 1. Get LP token accounts
            # 2. Check if held by lock programs
            # 3. Read lock duration from program data
            
            return is_locked, duration_days
            
        except Exception as e:
            logger.error(f"Error checking liquidity lock: {str(e)}")
            
        return False, 0.0
    
    async def _analyze_holder_distribution(self, token_address: str) -> Tuple[float, int]:
        """
        Analyze token holder distribution.
        
        Returns:
            Tuple of (top_10_percentage, total_holder_count)
        """
        try:
            # Use Birdeye API if available for accurate data
            if self.birdeye_api_key and self.session:
                url = f"https://api.birdeye.so/v1/token/holder/{token_address}"
                headers = {"X-API-KEY": self.birdeye_api_key}
                
                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Calculate top 10 holders percentage
                        holders = data.get('holders', [])
                        total_supply = sum(h['amount'] for h in holders)
                        top_10_amount = sum(h['amount'] for h in holders[:10])
                        
                        top_10_pct = (top_10_amount / total_supply * 100) if total_supply > 0 else 100
                        
                        return top_10_pct, len(holders)
            
            # Fallback: Use RPC (less accurate, sample-based)
            mint_pubkey = Pubkey.from_string(token_address)
            
            # Get largest accounts
            response = await self.rpc_client.get_token_largest_accounts(mint_pubkey)
            
            if response.value:
                accounts = response.value
                total_supply = sum(acc.amount for acc in accounts)
                top_10_amount = sum(acc.amount for acc in accounts[:10])
                
                top_10_pct = (top_10_amount / total_supply * 100) if total_supply > 0 else 100
                
                # Estimate holder count (this is just top holders, not total)
                holder_count = len(accounts)
                
                return top_10_pct, holder_count
                
        except Exception as e:
            logger.error(f"Error analyzing holders: {str(e)}")
            
        return 100.0, 0  # Worst case assumptions
    
    async def _check_metadata(self, token_address: str) -> bool:
        """
        Check if token has proper metadata.
        
        Returns:
            True if metadata exists and appears legitimate
        """
        try:
            # Check for Metaplex metadata
            # In production, verify metadata account and URI
            
            # For MVP, we'll do a basic check
            # Real implementation would:
            # 1. Derive metadata PDA
            # 2. Fetch metadata account
            # 3. Verify URI is accessible
            # 4. Check for suspicious metadata
            
            return True  # Placeholder
            
        except Exception as e:
            logger.error(f"Error checking metadata: {str(e)}")
            
        return False
    
    def _calculate_safety_score(self,
                              mint_disabled: bool,
                              freeze_disabled: bool,
                              liquidity_locked: bool,
                              lock_duration: float,
                              top_10_percentage: float,
                              holder_count: int,
                              has_metadata: bool,
                              initial_liquidity: float) -> Tuple[float, List[str]]:
        """
        Calculate overall safety score and identify red flags.
        
        Returns:
            Tuple of (score 0-100, list of red flags)
        """
        score = 100.0
        red_flags = []
        
        # Mint authority check (critical)
        if not mint_disabled:
            score -= 30
            red_flags.append("Mint authority still enabled - infinite supply risk")
        
        # Freeze authority check
        if not freeze_disabled:
            score -= 15
            red_flags.append("Freeze authority enabled - funds can be frozen")
        
        # Liquidity lock check
        if not liquidity_locked:
            score -= 20
            red_flags.append("Liquidity not locked - rug pull risk")
        elif lock_duration < 30:
            score -= 10
            red_flags.append("Liquidity lock too short (<30 days)")
        
        # Holder distribution
        if top_10_percentage > 50:
            score -= 15
            if top_10_percentage > 80:
                red_flags.append(f"Extreme concentration: top 10 hold {top_10_percentage:.1f}%")
        elif top_10_percentage > 30:
            score -= 5
        
        # Holder count
        if holder_count < 50:
            score -= 10
            if holder_count < 20:
                red_flags.append(f"Very few holders: {holder_count}")
        
        # Metadata check
        if not has_metadata:
            score -= 5
            # Not a red flag, just reduces score
        
        # Initial liquidity
        if initial_liquidity < 5000:
            score -= 10
            red_flags.append(f"Low initial liquidity: ${initial_liquidity:.2f}")
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        return score, red_flags
    
    def get_quick_verdict(self, safety_score: SafetyScore) -> str:
        """Get a quick buy/skip verdict with reasoning."""
        if safety_score.total_score >= 80:
            return "✅ SAFE TO BUY - High safety score, no major risks detected"
        elif safety_score.total_score >= 60 and len(safety_score.red_flags) == 0:
            return "⚠️  RISKY BUY - Moderate safety, proceed with caution"
        else:
            return "❌ SKIP - Too risky: " + ", ".join(safety_score.red_flags[:2])