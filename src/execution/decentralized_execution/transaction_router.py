"""
Transaction router module for decentralized execution.

This module provides routing capabilities for transactions across
multiple decentralized exchanges to find the optimal execution path.
"""
import logging
import json
import asyncio
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from ...utils.logger import get_logger
from ...utils.metrics import track_latency, track_api_call
from .wallet_manager import BlockchainNetwork, WalletManager

class DEX(Enum):
    """Supported decentralized exchanges."""
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    SUSHISWAP = "sushiswap"
    PANCAKESWAP = "pancakeswap"
    QUICKSWAP = "quickswap"
    CURVE = "curve"
    BALANCER = "balancer"
    RAYDIUM = "raydium"
    
class RouteType(Enum):
    """Types of routing strategies."""
    BEST_PRICE = "best_price"  # Optimize for best execution price
    LOWEST_GAS = "lowest_gas"  # Optimize for lowest gas cost
    FASTEST = "fastest"  # Optimize for fastest execution
    SPLIT = "split"  # Split order across multiple venues
    PRIVACY = "privacy"  # Optimize for privacy

class TransactionRouter:
    """
    Router for transactions across multiple DEXes and blockchains.
    
    This class analyzes available trading venues and routes transactions
    optimally based on price, gas cost, and other factors.
    
    Attributes:
        dex_adapters (Dict[str, Any]): Adapters for different DEXes
        wallet_manager (WalletManager): Wallet manager instance
        config (Dict[str, Any]): Router configuration
        logger (logging.Logger): Logger for routing events
    """
    
    def __init__(self, 
                wallet_manager: WalletManager,
                config: Dict[str, Any] = None):
        """
        Initialize the transaction router.
        
        Args:
            wallet_manager (WalletManager): Wallet manager instance
            config (Dict[str, Any], optional): Router configuration
        """
        self.wallet_manager = wallet_manager
        self.config = config or {}
        
        # Initialize DEX adapters
        self.dex_adapters = {}
        self._init_dex_adapters()
        
        self.logger = get_logger('transaction_router')
        self.logger.info("Transaction router initialized")
        
        # Stats for routing
        self.stats = {
            "routes_analyzed": 0,
            "routes_executed": 0,
            "splits_performed": 0,
            "average_price_improvement": 0.0
        }
    
    def _init_dex_adapters(self):
        """Initialize adapters for supported DEXes."""
        # This is a simplified implementation
        # In production, would dynamically load adapters
        
        for dex in DEX:
            self.dex_adapters[dex.value] = {
                "name": dex.value,
                "enabled": True,
                "chains": self._get_supported_chains(dex)
            }
            
        self.logger.info(f"Initialized {len(self.dex_adapters)} DEX adapters")
    
    def _get_supported_chains(self, dex: DEX) -> List[str]:
        """Get supported chains for a DEX."""
        # Mapping of DEXes to supported chains
        dex_chain_map = {
            DEX.UNISWAP_V2: [BlockchainNetwork.ETHEREUM.value],
            DEX.UNISWAP_V3: [
                BlockchainNetwork.ETHEREUM.value, 
                BlockchainNetwork.POLYGON.value,
                BlockchainNetwork.ARBITRUM.value,
                BlockchainNetwork.OPTIMISM.value
            ],
            DEX.SUSHISWAP: [
                BlockchainNetwork.ETHEREUM.value,
                BlockchainNetwork.POLYGON.value,
                BlockchainNetwork.ARBITRUM.value,
                BlockchainNetwork.AVALANCHE.value,
                BlockchainNetwork.BSC.value
            ],
            DEX.PANCAKESWAP: [BlockchainNetwork.BSC.value],
            DEX.QUICKSWAP: [BlockchainNetwork.POLYGON.value],
            DEX.CURVE: [
                BlockchainNetwork.ETHEREUM.value,
                BlockchainNetwork.POLYGON.value,
                BlockchainNetwork.ARBITRUM.value,
                BlockchainNetwork.OPTIMISM.value,
                BlockchainNetwork.AVALANCHE.value
            ],
            DEX.BALANCER: [
                BlockchainNetwork.ETHEREUM.value,
                BlockchainNetwork.POLYGON.value,
                BlockchainNetwork.ARBITRUM.value
            ],
            DEX.RAYDIUM: [BlockchainNetwork.SOLANA.value]
        }
        
        return dex_chain_map.get(dex, [])
    
    @track_latency("find_best_route")
    async def find_best_route(self,
                            from_token: str,
                            to_token: str,
                            amount: float,
                            chain: Union[str, BlockchainNetwork] = BlockchainNetwork.ETHEREUM,
                            route_type: Union[str, RouteType] = RouteType.BEST_PRICE,
                            options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Find the best route for a trade.
        
        Args:
            from_token (str): Source token address or symbol
            to_token (str): Destination token address or symbol
            amount (float): Amount to trade
            chain (Union[str, BlockchainNetwork]): Blockchain network
            route_type (Union[str, RouteType]): Routing strategy
            options (Optional[Dict[str, Any]]): Additional options
            
        Returns:
            Dict[str, Any]: Best route information
        """
        # Normalize parameters
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        if isinstance(route_type, RouteType):
            route_type = route_type.value
            
        options = options or {}
        
        # Track routing request
        self.stats["routes_analyzed"] += 1
        
        try:
            # Get all possible routes
            routes = await self._get_possible_routes(from_token, to_token, amount, chain)
            
            # If no routes found, return empty result
            if not routes:
                self.logger.warning(f"No routes found for {from_token} -> {to_token} on {chain}")
                return {"success": False, "error": "No routes found"}
                
            # Select best route based on strategy
            best_route = await self._select_best_route(routes, route_type, options)
            
            # Check if splitting is better
            if route_type == RouteType.SPLIT.value or options.get("consider_split", False):
                split_route = await self._check_split_advantage(routes, best_route, amount)
                if split_route and split_route["price_improvement"] > 0.001:  # 0.1% improvement threshold
                    self.logger.info(f"Split route provides {split_route['price_improvement']:.2%} better price")
                    best_route = split_route
                    self.stats["splits_performed"] += 1
            
            return best_route
            
        except Exception as e:
            self.logger.error(f"Error finding best route: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_possible_routes(self,
                                 from_token: str,
                                 to_token: str,
                                 amount: float,
                                 chain: str) -> List[Dict[str, Any]]:
        """
        Get all possible routes for a trade.
        
        Args:
            from_token (str): Source token address or symbol
            to_token (str): Destination token address or symbol
            amount (float): Amount to trade
            chain (str): Blockchain network
            
        Returns:
            List[Dict[str, Any]]: List of possible routes
        """
        routes = []
        
        # Get all DEXes supporting this chain
        dexes = [
            dex for dex, info in self.dex_adapters.items() 
            if info["enabled"] and chain in info["chains"]
        ]
        
        # Query each DEX for quotes
        quote_tasks = []
        for dex in dexes:
            quote_tasks.append(self._get_dex_quote(dex, from_token, to_token, amount, chain))
            
        # Wait for all quotes
        quotes = await asyncio.gather(*quote_tasks)
        
        # Add valid quotes to routes
        for quote in quotes:
            if quote and quote.get("success", False):
                routes.append(quote)
                
        return routes
    
    async def _get_dex_quote(self,
                           dex: str,
                           from_token: str,
                           to_token: str,
                           amount: float,
                           chain: str) -> Optional[Dict[str, Any]]:
        """
        Get a quote from a specific DEX.
        
        Args:
            dex (str): DEX name
            from_token (str): Source token address or symbol
            to_token (str): Destination token address or symbol
            amount (float): Amount to trade
            chain (str): Blockchain network
            
        Returns:
            Optional[Dict[str, Any]]: Quote information
        """
        # This is a simplified implementation
        # In production, would call actual DEX APIs
        
        # Track API call
        track_api_call(f"{dex}_quote", True)
        
        # Simulate different quotes from different DEXes
        if dex == DEX.UNISWAP_V3.value:
            return {
                "success": True,
                "dex": dex,
                "chain": chain,
                "from_token": from_token,
                "to_token": to_token,
                "amount_in": amount,
                "amount_out": amount * 0.997,  # 0.3% fee
                "price": 0.997,
                "gas_estimate": 150000,
                "gas_price_gwei": 50,
                "estimated_gas_cost_usd": 15.0,
                "estimated_execution_time_ms": 15000
            }
        elif dex == DEX.SUSHISWAP.value:
            return {
                "success": True,
                "dex": dex,
                "chain": chain,
                "from_token": from_token,
                "to_token": to_token,
                "amount_in": amount,
                "amount_out": amount * 0.996,  # 0.4% fee
                "price": 0.996,
                "gas_estimate": 140000,
                "gas_price_gwei": 50,
                "estimated_gas_cost_usd": 14.0,
                "estimated_execution_time_ms": 16000
            }
        elif dex == DEX.CURVE.value:
            return {
                "success": True,
                "dex": dex,
                "chain": chain,
                "from_token": from_token,
                "to_token": to_token,
                "amount_in": amount,
                "amount_out": amount * 0.998,  # 0.2% fee
                "price": 0.998,
                "gas_estimate": 250000,
                "gas_price_gwei": 50,
                "estimated_gas_cost_usd": 25.0,
                "estimated_execution_time_ms": 18000
            }
        else:
            # Other DEXes with random quotes
            import random
            return {
                "success": True,
                "dex": dex,
                "chain": chain,
                "from_token": from_token,
                "to_token": to_token,
                "amount_in": amount,
                "amount_out": amount * (0.995 + random.random() * 0.004),  # 0.1-0.5% fee
                "price": 0.995 + random.random() * 0.004,
                "gas_estimate": 100000 + random.randint(0, 100000),
                "gas_price_gwei": 50,
                "estimated_gas_cost_usd": 10.0 + random.random() * 10.0,
                "estimated_execution_time_ms": 15000 + random.randint(0, 5000)
            }
    
    async def _select_best_route(self,
                               routes: List[Dict[str, Any]],
                               route_type: str,
                               options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the best route from available options.
        
        Args:
            routes (List[Dict[str, Any]]): Available routes
            route_type (str): Routing strategy
            options (Dict[str, Any]): Additional options
            
        Returns:
            Dict[str, Any]: Best route
        """
        if not routes:
            return {"success": False, "error": "No routes available"}
            
        # Select based on strategy
        if route_type == RouteType.BEST_PRICE.value:
            # Sort by amount_out (descending)
            sorted_routes = sorted(routes, key=lambda r: r["amount_out"], reverse=True)
            return sorted_routes[0]
            
        elif route_type == RouteType.LOWEST_GAS.value:
            # Sort by estimated_gas_cost_usd (ascending)
            sorted_routes = sorted(routes, key=lambda r: r["estimated_gas_cost_usd"])
            return sorted_routes[0]
            
        elif route_type == RouteType.FASTEST.value:
            # Sort by estimated_execution_time_ms (ascending)
            sorted_routes = sorted(routes, key=lambda r: r["estimated_execution_time_ms"])
            return sorted_routes[0]
            
        elif route_type == RouteType.PRIVACY.value:
            # This would involve a more complex privacy scoring
            # For simplified demo, use a random route
            import random
            return random.choice(routes)
            
        else:
            # Default to best price
            sorted_routes = sorted(routes, key=lambda r: r["amount_out"], reverse=True)
            return sorted_routes[0]
    
    async def _check_split_advantage(self,
                                   routes: List[Dict[str, Any]],
                                   best_route: Dict[str, Any],
                                   total_amount: float) -> Optional[Dict[str, Any]]:
        """
        Check if splitting the order across multiple venues is advantageous.
        
        Args:
            routes (List[Dict[str, Any]]): Available routes
            best_route (Dict[str, Any]): Best single route
            total_amount (float): Total amount to trade
            
        Returns:
            Optional[Dict[str, Any]]: Split route if better, None otherwise
        """
        # Need at least 2 routes for splitting
        if len(routes) < 2:
            return None
            
        # Sort routes by price (descending)
        sorted_routes = sorted(routes, key=lambda r: r["price"], reverse=True)
        
        # Try different split ratios
        best_split = None
        best_amount_out = best_route["amount_out"]
        
        # Check a few simple split ratios
        for ratio in [0.25, 0.33, 0.5, 0.66, 0.75]:
            # Split amounts
            amount1 = total_amount * ratio
            amount2 = total_amount * (1 - ratio)
            
            # Get quotes for the split amounts
            quote1 = await self._get_dex_quote(
                sorted_routes[0]["dex"],
                sorted_routes[0]["from_token"],
                sorted_routes[0]["to_token"],
                amount1,
                sorted_routes[0]["chain"]
            )
            
            quote2 = await self._get_dex_quote(
                sorted_routes[1]["dex"],
                sorted_routes[1]["from_token"],
                sorted_routes[1]["to_token"],
                amount2,
                sorted_routes[1]["chain"]
            )
            
            # Calculate total output
            if quote1 and quote2:
                total_out = quote1["amount_out"] + quote2["amount_out"]
                
                # If better than current best, update
                if total_out > best_amount_out:
                    price_improvement = (total_out - best_amount_out) / best_amount_out
                    
                    best_split = {
                        "success": True,
                        "type": "split",
                        "routes": [quote1, quote2],
                        "ratios": [ratio, 1 - ratio],
                        "amount_in": total_amount,
                        "amount_out": total_out,
                        "price_improvement": price_improvement,
                        "total_gas_cost_usd": quote1["estimated_gas_cost_usd"] + quote2["estimated_gas_cost_usd"],
                        "estimated_execution_time_ms": max(
                            quote1["estimated_execution_time_ms"],
                            quote2["estimated_execution_time_ms"]
                        )
                    }
                    best_amount_out = total_out
        
        return best_split
    
    @track_latency("estimate_price_impact")
    async def estimate_price_impact(self,
                                  route: Dict[str, Any],
                                  amount: float) -> float:
        """
        Estimate the price impact of a trade.
        
        Args:
            route (Dict[str, Any]): Route information
            amount (float): Amount to trade
            
        Returns:
            float: Estimated price impact (0.0-1.0)
        """
        # This is a simplified implementation
        # In production, would use liquidity data from DEXes
        
        dex = route.get("dex")
        chain = route.get("chain")
        from_token = route.get("from_token")
        to_token = route.get("to_token")
        
        # Get quotes for different sizes to estimate impact
        small_amount = amount * 0.01  # 1% of amount
        full_amount = amount
        
        small_quote = await self._get_dex_quote(dex, from_token, to_token, small_amount, chain)
        full_quote = await self._get_dex_quote(dex, from_token, to_token, full_amount, chain)
        
        if not small_quote or not full_quote:
            return 0.0
            
        # Calculate price impact
        small_price = small_quote["amount_out"] / small_quote["amount_in"]
        full_price = full_quote["amount_out"] / full_quote["amount_in"]
        
        price_impact = 1.0 - (full_price / small_price)
        
        return max(0.0, price_impact)
    
    async def split_order(self,
                        from_token: str,
                        to_token: str,
                        amount: float,
                        chain: Union[str, BlockchainNetwork],
                        max_splits: int = 3) -> Dict[str, Any]:
        """
        Split an order across multiple venues for optimal execution.
        
        Args:
            from_token (str): Source token address or symbol
            to_token (str): Destination token address or symbol
            amount (float): Amount to trade
            chain (Union[str, BlockchainNetwork]): Blockchain network
            max_splits (int): Maximum number of splits
            
        Returns:
            Dict[str, Any]: Split order information
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        # For now, delegate to find_best_route with SPLIT type
        return await self.find_best_route(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            chain=chain,
            route_type=RouteType.SPLIT,
            options={"max_splits": max_splits}
        )
    
    def get_supported_dexes(self, chain: Union[str, BlockchainNetwork]) -> List[str]:
        """
        Get supported DEXes for a specific chain.
        
        Args:
            chain (Union[str, BlockchainNetwork]): Blockchain network
            
        Returns:
            List[str]: List of supported DEXes
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        return [
            dex for dex, info in self.dex_adapters.items() 
            if info["enabled"] and chain in info["chains"]
        ]