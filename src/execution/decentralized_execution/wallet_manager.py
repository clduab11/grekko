"""
Wallet manager module for decentralized execution.

This module provides a secure, non-custodial wallet management system
for the Grekko platform's decentralized execution architecture.
"""
import logging
import json
import os
import random
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

from ...utils.logger import get_logger
from ...utils.credentials_manager import CredentialsManager
from ...utils.metrics import track_latency, track_api_call
from ...risk_management.circuit_breaker import CircuitBreaker

class BlockchainNetwork(Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BSC = "binance-smart-chain"
    AVALANCHE = "avalanche"
    SOLANA = "solana"
    
class WalletType(Enum):
    """Types of wallets supported by the platform."""
    HOT = "hot"  # Software wallet with stored private key
    HARDWARE = "hardware"  # Hardware wallet like Ledger or Trezor
    MULTISIG = "multisig"  # Multi-signature wallet
    EXTERNAL = "external"  # Externally managed (e.g., MetaMask)
    
class RotationPolicy(Enum):
    """Wallet rotation policies for privacy."""
    NONE = "none"  # No rotation
    TRADE_BASED = "trade_based"  # Rotate after specific number of trades
    TIME_BASED = "time_based"  # Rotate after specific time period
    VOLUME_BASED = "volume_based"  # Rotate after specific volume threshold
    RANDOM = "random"  # Random rotation with probability
    
class WalletManager:
    """
    Secure manager for blockchain wallets across multiple networks.

    This class handles all aspects of wallet management for decentralized
    execution, including key storage, address rotation, balance monitoring,
    transaction signing, and integration with external wallet providers.

    Attributes:
        credentials_manager (CredentialsManager): Secure storage for private keys
        wallets (Dict[str, List[Dict]]): Map of all wallets by blockchain
        active_wallets (Dict[str, Dict]): Currently active wallets by blockchain
        rotation_policies (Dict[str, Dict]): Rotation policy settings by blockchain
        logger (logging.Logger): Logger for wallet events
        external_providers (Dict[str, Any]): Registered external wallet providers (e.g., MetaMask, Coinbase)
    """

    def __init__(self,
                credentials_manager: CredentialsManager,
                config: Dict[str, Any] = None,
                circuit_breaker: Optional[CircuitBreaker] = None):
        """
        Initialize the wallet manager.

        Args:
            credentials_manager (CredentialsManager): Secure storage for keys
            config (Dict[str, Any], optional): Configuration parameters
            circuit_breaker (Optional[CircuitBreaker]): Circuit breaker for safety
        """
        self.credentials_manager = credentials_manager
        self.config = config or {}
        self.circuit_breaker = circuit_breaker

        # Initialize wallet storage
        self.wallets = {}  # chain -> [wallet_info]
        self.active_wallets = {}  # chain -> wallet_info

        # External wallet providers (MetaMask, Coinbase, etc.)
        self.external_providers = {}  # provider_name -> WalletProvider instance

        # Default rotation policies
        self.rotation_policies = {
            BlockchainNetwork.ETHEREUM.value: {
                "policy": RotationPolicy.TRADE_BASED.value,
                "trades_threshold": 10,
                "time_threshold": 86400,  # 1 day in seconds
                "volume_threshold": 10000,  # in USD
                "random_probability": 0.2,
                "last_rotation": time.time()
            }
        }

        # Update with config if provided
        if config and "rotation_policies" in config:
            for chain, policy in config["rotation_policies"].items():
                if chain in self.rotation_policies:
                    self.rotation_policies[chain].update(policy)
                else:
                    self.rotation_policies[chain] = policy

        self.logger = get_logger('wallet_manager')
        self.logger.info("Wallet manager initialized")

        # Stats for wallet usage
        self.stats = {
            "transactions_count": 0,
            "rotations_performed": 0,
            "rebalances_performed": 0
        }

        # Initialize wallets from credentials
        self._init_wallets()

    def register_external_provider(self, provider_name: str, provider_instance: Any) -> None:
        """
        Register an external wallet provider (e.g., MetaMask, Coinbase).

        Args:
            provider_name (str): Name of the provider (e.g., 'metamask', 'coinbase')
            provider_instance (WalletProvider): Instance of the provider
        """
        self.external_providers[provider_name.lower()] = provider_instance
        self.logger.info(f"Registered external wallet provider: {provider_name}")

    def get_external_provider(self, provider_name: str) -> Optional[Any]:
        """
        Retrieve a registered external wallet provider.

        Args:
            provider_name (str): Name of the provider

        Returns:
            WalletProvider instance or None
        """
        return self.external_providers.get(provider_name.lower())
    
    def _init_wallets(self):
        """Initialize wallets from stored credentials."""
        try:
            # Get wallet credentials from credentials manager
            wallet_data = self.credentials_manager.get_credential("wallet_data")
            
            if wallet_data:
                # Parse wallet data if it's a string
                if isinstance(wallet_data, str):
                    wallet_data = json.loads(wallet_data)
                
                # Initialize wallets from stored data
                for chain, wallets in wallet_data.items():
                    self.wallets[chain] = wallets
                    
                    # Set active wallet for each chain
                    if wallets:
                        self.active_wallets[chain] = wallets[0]
                        
                self.logger.info(f"Initialized wallets for {len(self.wallets)} blockchain networks")
                
            else:
                self.logger.warning("No wallet data found in credentials manager")
        
        except Exception as e:
            self.logger.error(f"Error initializing wallets: {str(e)}")
    
    async def add_wallet(self, 
                        chain: Union[str, BlockchainNetwork],
                        wallet_info: Dict[str, Any],
                        private_key: Optional[str] = None) -> bool:
        """
        Add a new wallet to the manager.
        
        Args:
            chain (Union[str, BlockchainNetwork]): Blockchain network
            wallet_info (Dict[str, Any]): Wallet information
            private_key (Optional[str]): Private key if it's a hot wallet
            
        Returns:
            bool: Success or failure
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        try:
            # Ensure required fields in wallet_info
            required_fields = ["address", "type", "name"]
            for field in required_fields:
                if field not in wallet_info:
                    self.logger.error(f"Missing required field in wallet_info: {field}")
                    return False
            
            # Initialize chain if not exists
            if chain not in self.wallets:
                self.wallets[chain] = []
                
            # Check if wallet already exists
            if any(w["address"] == wallet_info["address"] for w in self.wallets[chain]):
                self.logger.warning(f"Wallet {wallet_info['address']} already exists for {chain}")
                return False
                
            # Store private key if provided
            if private_key and wallet_info["type"] == WalletType.HOT.value:
                credential_key = f"wallet_{chain}_{wallet_info['address']}"
                await self.credentials_manager.add_credential(credential_key, private_key)
                
            # Add wallet to the list
            self.wallets[chain].append(wallet_info)
            
            # If this is the first wallet for this chain, make it active
            if len(self.wallets[chain]) == 1:
                self.active_wallets[chain] = wallet_info
                
            # Persist wallet data
            self._save_wallet_data()
            
            self.logger.info(f"Added wallet {wallet_info['address']} to {chain}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding wallet: {str(e)}")
            return False
    
    async def get_wallet(self, 
                       chain: Union[str, BlockchainNetwork],
                       rotation_policy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the active wallet for a blockchain network.
        
        Args:
            chain (Union[str, BlockchainNetwork]): Blockchain network
            rotation_policy (Optional[str]): Override default rotation policy
            
        Returns:
            Optional[Dict[str, Any]]: Wallet information or None if not available
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        # Check if we have wallets for this chain
        if chain not in self.wallets or not self.wallets[chain]:
            self.logger.warning(f"No wallets available for {chain}")
            return None
            
        # Check if active wallet exists for this chain
        if chain not in self.active_wallets:
            self.active_wallets[chain] = self.wallets[chain][0]
            
        # Check if we should rotate wallet
        policy = rotation_policy or self.rotation_policies.get(chain, {}).get("policy")
        if policy and policy != RotationPolicy.NONE.value:
            should_rotate = await self._should_rotate_wallet(chain, self.active_wallets[chain])
            if should_rotate:
                await self.rotate_wallets(chain)
                
        return self.active_wallets[chain]
    
    async def rotate_wallets(self, chain: Union[str, BlockchainNetwork]) -> bool:
        """
        Rotate to a different wallet for a blockchain network.
        
        Args:
            chain (Union[str, BlockchainNetwork]): Blockchain network
            
        Returns:
            bool: Success or failure
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        # Check if we have wallets for this chain
        if chain not in self.wallets or len(self.wallets[chain]) < 2:
            self.logger.warning(f"Not enough wallets for rotation on {chain}")
            return False
            
        try:
            # Get current active wallet
            current_wallet = self.active_wallets.get(chain)
            
            # Select a different wallet
            available_wallets = [w for w in self.wallets[chain] if w != current_wallet]
            
            # Select the wallet with the highest balance
            # This could be enhanced with more sophisticated selection
            new_wallet = random.choice(available_wallets)
            
            # Set as active wallet
            self.active_wallets[chain] = new_wallet
            
            # Update rotation timestamp
            if chain in self.rotation_policies:
                self.rotation_policies[chain]["last_rotation"] = time.time()
                
            self.stats["rotations_performed"] += 1
            
            self.logger.info(f"Rotated wallet for {chain} from {current_wallet['address']} to {new_wallet['address']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rotating wallets: {str(e)}")
            return False
    
    async def _should_rotate_wallet(self, chain: str, wallet: Dict[str, Any]) -> bool:
        """
        Check if a wallet should be rotated based on policy.
        
        Args:
            chain (str): Blockchain network
            wallet (Dict[str, Any]): Wallet information
            
        Returns:
            bool: True if wallet should be rotated
        """
        if chain not in self.rotation_policies:
            return False
            
        policy = self.rotation_policies[chain]
        
        # Check based on policy type
        policy_type = policy.get("policy")
        
        if policy_type == RotationPolicy.NONE.value:
            return False
            
        elif policy_type == RotationPolicy.TRADE_BASED.value:
            # Rotate after specific number of trades
            trades_threshold = policy.get("trades_threshold", 10)
            trades_count = wallet.get("trades_count", 0)
            return trades_count >= trades_threshold
            
        elif policy_type == RotationPolicy.TIME_BASED.value:
            # Rotate after specific time period
            time_threshold = policy.get("time_threshold", 86400)  # Default 1 day
            last_rotation = policy.get("last_rotation", 0)
            return (time.time() - last_rotation) >= time_threshold
            
        elif policy_type == RotationPolicy.VOLUME_BASED.value:
            # Rotate after specific volume threshold
            volume_threshold = policy.get("volume_threshold", 10000)  # Default 10k USD
            volume = wallet.get("volume_traded", 0)
            return volume >= volume_threshold
            
        elif policy_type == RotationPolicy.RANDOM.value:
            # Random rotation with probability
            probability = policy.get("random_probability", 0.2)  # Default 20% chance
            return random.random() < probability
            
        return False
    
    @track_latency("check_balances")
    async def check_balances(self, 
                           chain: Optional[Union[str, BlockchainNetwork]] = None,
                           wallets: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Check balances for wallets.
        
        Args:
            chain (Optional[Union[str, BlockchainNetwork]]): Specific blockchain or all
            wallets (Optional[List[Dict[str, Any]]]): Specific wallets or all
            
        Returns:
            Dict[str, Dict[str, Any]]: Wallet balances by address
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        balances = {}
        
        try:
            # Determine which chains to check
            chains_to_check = [chain] if chain else list(self.wallets.keys())
            
            for current_chain in chains_to_check:
                # Determine which wallets to check
                wallets_to_check = wallets if wallets else self.wallets.get(current_chain, [])
                
                for wallet in wallets_to_check:
                    address = wallet["address"]
                    
                    # Get balance from blockchain
                    # This is a placeholder - actual implementation would depend on the blockchain
                    balance = await self._get_chain_balance(current_chain, address)
                    
                    # Store balance
                    if current_chain not in balances:
                        balances[current_chain] = {}
                        
                    balances[current_chain][address] = balance
                    
                    # Update wallet info
                    wallet["balance"] = balance
                    wallet["last_balance_check"] = time.time()
            
            return balances
            
        except Exception as e:
            self.logger.error(f"Error checking balances: {str(e)}")
            return {}
    
    async def _get_chain_balance(self, chain: str, address: str) -> Dict[str, Any]:
        """
        Get balance from blockchain for a specific address.
        
        Args:
            chain (str): Blockchain network
            address (str): Wallet address
            
        Returns:
            Dict[str, Any]: Balance information
        """
        # This is a placeholder implementation
        # In production, this would connect to blockchain nodes or APIs
        
        # Different implementation based on chain
        if chain == BlockchainNetwork.ETHEREUM.value:
            return await self._get_ethereum_balance(address)
        elif chain == BlockchainNetwork.POLYGON.value:
            return await self._get_polygon_balance(address)
        elif chain == BlockchainNetwork.SOLANA.value:
            return await self._get_solana_balance(address)
        else:
            # Default implementation for other chains
            return {"native": 0.0, "tokens": {}}
    
    async def _get_ethereum_balance(self, address: str) -> Dict[str, Any]:
        """Get balance for Ethereum address."""
        # Placeholder - would use Web3.py or similar
        track_api_call("ethereum_rpc", True)
        
        return {
            "native": 1.5,  # ETH
            "tokens": {
                "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": 1000.0,  # USDC
                "0xdAC17F958D2ee523a2206206994597C13D831ec7": 1000.0   # USDT
            }
        }
    
    async def _get_polygon_balance(self, address: str) -> Dict[str, Any]:
        """Get balance for Polygon address."""
        # Placeholder - would use Polygon RPC or API
        track_api_call("polygon_rpc", True)
        
        return {
            "native": 1000.0,  # MATIC
            "tokens": {
                "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174": 1000.0,  # USDC
                "0xc2132D05D31c914a87C6611C10748AEb04B58e8F": 1000.0   # USDT
            }
        }
    
    async def _get_solana_balance(self, address: str) -> Dict[str, Any]:
        """Get balance for Solana address."""
        # Placeholder - would use Solana API
        track_api_call("solana_rpc", True)
        
        return {
            "native": 100.0,  # SOL
            "tokens": {
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 1000.0,  # USDC
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 1000.0   # USDT
            }
        }
    
    async def rebalance_if_needed(self, 
                                threshold: float = 0.1,
                                chain: Optional[Union[str, BlockchainNetwork]] = None) -> bool:
        """
        Rebalance funds between wallets if needed.
        
        Args:
            threshold (float): Threshold for imbalance (0.0-1.0)
            chain (Optional[Union[str, BlockchainNetwork]]): Specific blockchain or all
            
        Returns:
            bool: Success or failure
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        # Determine which chains to rebalance
        chains_to_check = [chain] if chain else list(self.wallets.keys())
        
        for current_chain in chains_to_check:
            # Skip if less than 2 wallets (nothing to rebalance)
            if current_chain not in self.wallets or len(self.wallets[current_chain]) < 2:
                continue
                
            # Check balances
            await self.check_balances(current_chain)
            
            # Calculate total balance and average
            total_balance = 0.0
            for wallet in self.wallets[current_chain]:
                balance = wallet.get("balance", {}).get("native", 0.0)
                total_balance += balance
                
            # Skip if no balance
            if total_balance == 0:
                continue
                
            average_balance = total_balance / len(self.wallets[current_chain])
            threshold_amount = average_balance * threshold
            
            # Find wallets that need rebalancing
            transfers_needed = []
            for wallet in self.wallets[current_chain]:
                balance = wallet.get("balance", {}).get("native", 0.0)
                diff = balance - average_balance
                
                if abs(diff) > threshold_amount:
                    transfers_needed.append({
                        "wallet": wallet,
                        "diff": diff
                    })
            
            # Skip if no transfers needed
            if not transfers_needed:
                continue
                
            # Sort by diff (descending)
            transfers_needed.sort(key=lambda x: x["diff"], reverse=True)
            
            # Perform transfers from highest to lowest
            while len(transfers_needed) >= 2:
                from_wallet = transfers_needed[0]
                to_wallet = transfers_needed[-1]
                
                # Calculate transfer amount
                transfer_amount = min(from_wallet["diff"], -to_wallet["diff"])
                
                # Perform transfer
                success = await self._transfer_funds(
                    current_chain,
                    from_wallet["wallet"]["address"],
                    to_wallet["wallet"]["address"],
                    transfer_amount
                )
                
                if success:
                    # Update balances
                    from_wallet["wallet"]["balance"]["native"] -= transfer_amount
                    to_wallet["wallet"]["balance"]["native"] += transfer_amount
                    
                    # Update diffs
                    from_wallet["diff"] -= transfer_amount
                    to_wallet["diff"] += transfer_amount
                    
                    # Remove wallets that are now balanced
                    if abs(from_wallet["diff"]) <= threshold_amount:
                        transfers_needed.remove(from_wallet)
                    if abs(to_wallet["diff"]) <= threshold_amount:
                        transfers_needed.remove(to_wallet)
                    
                    # Sort again
                    transfers_needed.sort(key=lambda x: x["diff"], reverse=True)
                    
                    self.stats["rebalances_performed"] += 1
                else:
                    # Transfer failed, skip these wallets
                    transfers_needed.remove(from_wallet)
                    transfers_needed.remove(to_wallet)
        
        return True
    
    async def _transfer_funds(self, chain: str, from_address: str, to_address: str, amount: float) -> bool:
        """
        Transfer funds between wallets.
        
        Args:
            chain (str): Blockchain network
            from_address (str): Source address
            to_address (str): Destination address
            amount (float): Amount to transfer
            
        Returns:
            bool: Success or failure
        """
        # This is a placeholder implementation
        # In production, this would sign and submit a transaction
        
        # Check circuit breaker
        if self.circuit_breaker:
            can_trade, reason = self.circuit_breaker.can_trade()
            if not can_trade:
                self.logger.warning(f"Circuit breaker active: {reason}")
                return False
        
        self.logger.info(f"Transferring {amount} on {chain} from {from_address} to {to_address}")
        
        # Increment transaction count
        self.stats["transactions_count"] += 1
        
        # Pretend it worked
        return True
    
    async def sign_transaction(self, 
                             chain: Union[str, BlockchainNetwork],
                             address: str, 
                             transaction_data: Dict[str, Any]) -> Optional[str]:
        """
        Sign a transaction with a wallet's private key.
        
        Args:
            chain (Union[str, BlockchainNetwork]): Blockchain network
            address (str): Wallet address
            transaction_data (Dict[str, Any]): Transaction data to sign
            
        Returns:
            Optional[str]: Signed transaction or None if failed
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        try:
            # Get wallet private key
            credential_key = f"wallet_{chain}_{address}"
            private_key = self.credentials_manager.get_credential(credential_key)
            
            if not private_key:
                self.logger.error(f"No private key found for wallet {address} on {chain}")
                return None
                
            # Different signing logic based on chain
            if chain == BlockchainNetwork.ETHEREUM.value:
                return await self._sign_ethereum_transaction(private_key, transaction_data)
            elif chain == BlockchainNetwork.POLYGON.value:
                return await self._sign_polygon_transaction(private_key, transaction_data)
            elif chain == BlockchainNetwork.SOLANA.value:
                return await self._sign_solana_transaction(private_key, transaction_data)
            else:
                self.logger.error(f"Unsupported chain for signing: {chain}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error signing transaction: {str(e)}")
            return None
    
    async def _sign_ethereum_transaction(self, private_key: str, transaction_data: Dict[str, Any]) -> str:
        """Sign an Ethereum transaction."""
        # This is a placeholder implementation
        # In production, this would use Web3.py or similar
        
        # Pretend we signed it
        return f"0x{private_key[:8]}...{transaction_data.get('nonce', 0)}"
    
    async def _sign_polygon_transaction(self, private_key: str, transaction_data: Dict[str, Any]) -> str:
        """Sign a Polygon transaction."""
        # This is a placeholder implementation
        # In production, this would use Web3.py or similar
        
        # Pretend we signed it
        return f"0x{private_key[:8]}...{transaction_data.get('nonce', 0)}"
    
    async def _sign_solana_transaction(self, private_key: str, transaction_data: Dict[str, Any]) -> str:
        """Sign a Solana transaction."""
        # This is a placeholder implementation
        # In production, this would use Solana SDK
        
        # Pretend we signed it
        return f"0x{private_key[:8]}...{transaction_data.get('nonce', 0)}"
    
    def _save_wallet_data(self) -> bool:
        """Save wallet data to credentials manager."""
        try:
            # Create wallet data without private keys
            wallet_data = {}
            
            for chain, wallets in self.wallets.items():
                # Exclude private keys from storage
                wallet_data[chain] = []
                for wallet in wallets:
                    wallet_copy = wallet.copy()
                    if "private_key" in wallet_copy:
                        del wallet_copy["private_key"]
                    wallet_data[chain].append(wallet_copy)
            
            # Save to credentials manager
            self.credentials_manager.add_credential("wallet_data", json.dumps(wallet_data))
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving wallet data: {str(e)}")
            return False
    
    def get_wallets_for_chain(self, chain: Union[str, BlockchainNetwork]) -> List[Dict[str, Any]]:
        """
        Get all wallets for a blockchain.
        
        Args:
            chain (Union[str, BlockchainNetwork]): Blockchain network
            
        Returns:
            List[Dict[str, Any]]: List of wallets
        """
        # Normalize chain parameter
        if isinstance(chain, BlockchainNetwork):
            chain = chain.value
            
        return self.wallets.get(chain, [])