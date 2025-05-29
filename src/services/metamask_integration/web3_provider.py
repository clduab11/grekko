"""Web3 Provider for Metamask Integration Service

Handles secure Web3 provider initialization, RPC connection security, provider failover,
transaction security validation, and gas estimation.

Integrates with SecurityManager and NetworkManager for comprehensive security.
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, List
from web3 import Web3, HTTPProvider

from .network_manager import NetworkManager, NetworkManagerError
from .security_manager import SecurityManager, SecurityViolationError
from .metrics import record_rpc_connection_error

logger = logging.getLogger(__name__)


class Web3ProviderError(Exception):
    """Base exception for Web3 provider errors."""


class Web3Provider:
    """
    Secure Web3 provider manager with:
    - Secure initialization and connection validation
    - RPC endpoint security and TLS checks
    - Provider failover and redundancy
    - Transaction security validation
    - Gas estimation and security checks
    """

    def __init__(
        self,
        network_manager: NetworkManager,
        security_manager: SecurityManager,
        failover_rpc_urls: Optional[List[str]] = None,
        connection_timeout: int = 5,
        max_retries: int = 3,
        retry_backoff: float = 1.5,
    ):
        """
        :param network_manager: NetworkManager instance for network/RPC validation.
        :param security_manager: SecurityManager instance for transaction validation.
        :param failover_rpc_urls: List of backup RPC endpoints for failover.
        :param connection_timeout: Timeout for RPC connections (seconds).
        :param max_retries: Max retries for failover.
        :param retry_backoff: Backoff multiplier for retries.
        """
        self.network_manager = network_manager
        self.security_manager = security_manager
        self.failover_rpc_urls = failover_rpc_urls or []
        self.connection_timeout = connection_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self.web3: Optional[Web3] = None
        self.active_rpc_url: Optional[str] = None
        self.lock = threading.Lock()

    def initialize_provider(self, rpc_url: Optional[str] = None):
        """
        Initialize the Web3 provider securely.
        :param rpc_url: Optional RPC endpoint to use; defaults to active network.
        """
        with self.lock:
            if not rpc_url:
                active_network = self.network_manager.get_active_network()
                if not active_network or "rpc_url" not in active_network:
                    raise Web3ProviderError("No active network or RPC URL available")
                rpc_url = active_network["rpc_url"]

            # Validate endpoint security
            if not isinstance(rpc_url, str) or not rpc_url:
                raise Web3ProviderError("Invalid RPC URL for provider initialization")
            self.network_manager.validate_rpc_endpoint(rpc_url)

            # Initialize Web3 provider with secure settings
            provider = HTTPProvider(rpc_url, request_kwargs={"timeout": self.connection_timeout})
            web3 = Web3(provider)

            # Test connection
            if not web3.is_connected():
                record_rpc_connection_error()
                raise Web3ProviderError(f"Failed to connect to RPC endpoint: {rpc_url}")

            self.web3 = web3
            self.active_rpc_url = rpc_url
            logger.info(f"Web3 provider initialized for {rpc_url}")

    def get_web3(self) -> Web3:
        """Return the current Web3 instance, initializing if needed."""
        if self.web3 is None or not self.web3.is_connected():
            self._failover_and_reconnect()
        return self.web3

    def _failover_and_reconnect(self):
        """
        Attempt to reconnect to the primary or failover RPC endpoints.
        """
        rpc_urls = [self.active_rpc_url] if self.active_rpc_url else []
        active_network = self.network_manager.get_active_network()
        if active_network and "rpc_url" in active_network:
            rpc_urls.append(active_network["rpc_url"])
        rpc_urls.extend(self.failover_rpc_urls)
        tried = set()
        for attempt, rpc_url in enumerate(rpc_urls):
            if not rpc_url or rpc_url in tried:
                continue
            tried.add(rpc_url)
            try:
                self.initialize_provider(rpc_url)
                if self.web3 and self.web3.is_connected():
                    logger.info(f"Web3 failover succeeded on {rpc_url}")
                    return
            except Exception as e:
                record_rpc_connection_error() # Record error during failover attempt
                logger.warning(f"Web3 failover attempt {attempt+1} failed: {e}")
                time.sleep(self.retry_backoff * (attempt + 1))
        record_rpc_connection_error() # All failover attempts failed
        raise Web3ProviderError("All Web3 provider failover attempts failed")

    def validate_transaction(self, tx: Dict[str, Any]) -> bool:
        """
        Validate a transaction using SecurityManager.
        :param tx: Transaction dict.
        """
        try:
            return self.security_manager.verify_transaction(tx)
        except SecurityViolationError as e:
            logger.error(f"Transaction security validation failed: {e}")
            raise Web3ProviderError(f"Transaction validation failed: {e}")

    def send_transaction(self, tx: Dict[str, Any]) -> str:
        """
        Securely send a transaction after validation.
        :param tx: Transaction dict.
        :return: Transaction hash.
        """
        self.validate_transaction(tx)
        web3 = self.get_web3()
        try:
            tx_hash = web3.eth.send_transaction(tx)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Transaction send failed: {e}")
            raise Web3ProviderError(f"Transaction send failed: {e}")

    def estimate_gas(self, tx: Dict[str, Any]) -> int:
        """
        Securely estimate gas for a transaction, with security checks.
        :param tx: Transaction dict.
        :return: Estimated gas.
        """
        self.validate_transaction(tx)
        web3 = self.get_web3()
        try:
            gas = web3.eth.estimate_gas(tx)
            # Security check: ensure gas is within reasonable bounds
            if gas > 10_000_000:
                raise Web3ProviderError("Estimated gas exceeds safe threshold")
            logger.info(f"Gas estimated: {gas}")
            return gas
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            raise Web3ProviderError(f"Gas estimation failed: {e}")

    def monitor_connection(self, interval: int = 30):
        """
        Start a background thread to monitor the Web3 connection and auto-failover.
        :param interval: Monitoring interval in seconds.
        """
        def monitor():
            while True:
                try:
                    web3 = self.get_web3()
                    if not web3.is_connected():
                        logger.warning("Web3 connection lost, attempting failover")
                        record_rpc_connection_error() # Connection lost
                        self._failover_and_reconnect()
                except Exception as e:
                    record_rpc_connection_error() # Error in monitor
                    logger.error(f"Web3 connection monitor error: {e}")
                time.sleep(interval)

        t = threading.Thread(target=monitor, daemon=True)
        t.start()
        logger.info("Started Web3 connection monitor thread")

    def get_active_rpc_url(self) -> Optional[str]:
        """Return the currently active RPC URL."""
        return self.active_rpc_url

    def get_chain_id(self) -> Optional[int]:
        """Return the current chain ID, if available."""
        web3 = self.get_web3()
        try:
            return web3.eth.chain_id
        except Exception as e:
            logger.error(f"Failed to get chain ID: {e}")
            return None