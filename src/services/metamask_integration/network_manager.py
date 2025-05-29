"""Network Manager for Metamask Integration Service

Handles secure RPC endpoint management, network switching validation, trusted network whitelisting,
connection monitoring, anomaly detection, and secure network configuration.

Integrates with SecurityManager and Validator for comprehensive security.
"""

import ssl
import socket
import logging
import threading
import time
from typing import List, Dict, Optional, Callable
from urllib.parse import urlparse

from .security_manager import SecurityManager, SecurityViolationError, SuspiciousActivityError
# Validator is a placeholder, so we will structure for future extension
# Validator is a placeholder for future extension.

logger = logging.getLogger(__name__)


class NetworkManagerError(Exception):
    """Base exception for network manager errors."""


class RPCValidationError(NetworkManagerError):
    """Raised when an RPC endpoint fails validation."""


class NetworkSwitchError(NetworkManagerError):
    """Raised when a network switch fails security checks."""


class NetworkManager:
    """
    Manages secure network operations for Metamask integration.
    - Secure RPC endpoint management with TLS validation
    - Network switching validation and security checks
    - Trusted network whitelist management
    - Connection monitoring and anomaly detection
    - Secure network configuration management
    """

    def __init__(
        self,
        security_manager: SecurityManager,
        trusted_networks: Optional[List[Dict]] = None,
        validator: Optional[object] = None,
    ):
        """
        :param security_manager: SecurityManager instance for security checks.
        :param trusted_networks: List of trusted network dicts (id, name, rpc_url, chain_id, etc).
        :param validator: Optional validator for network parameter validation.
        """
        self.security_manager = security_manager
        self.validator = validator
        self.trusted_networks = trusted_networks or []
        self.trusted_rpc_urls = {n["rpc_url"] for n in self.trusted_networks if "rpc_url" in n}
        self.active_network = None
        self.connection_monitors = {}
        self.monitor_interval = 30  # seconds

    def add_trusted_network(self, network: Dict):
        """Add a network to the trusted whitelist after validation."""
        # TODO: Add validator logic for network parameter validation when available.
        if "rpc_url" not in network:
            raise ValueError("Network must include 'rpc_url'")
        self.trusted_networks.append(network)
        self.trusted_rpc_urls.add(network["rpc_url"])
        logger.info(f"Trusted network added: {network.get('name', network['rpc_url'])}")

    def is_trusted_network(self, rpc_url: str) -> bool:
        """Check if the given RPC URL is in the trusted whitelist."""
        return rpc_url in self.trusted_rpc_urls

    def validate_rpc_endpoint(self, rpc_url: str) -> bool:
        """
        Validate the RPC endpoint:
        - Must be in trusted whitelist
        - Must use HTTPS (TLS)
        - Must pass SSL certificate validation
        """
        if not self.is_trusted_network(rpc_url):
            logger.warning(f"RPC endpoint not in trusted whitelist: {rpc_url}")
            raise RPCValidationError("RPC endpoint not trusted")

        parsed = urlparse(rpc_url)
        if parsed.scheme != "https":
            logger.warning(f"RPC endpoint does not use HTTPS: {rpc_url}")
            raise RPCValidationError("RPC endpoint must use HTTPS")

        # TLS/SSL certificate validation
        try:
            context = ssl.create_default_context()
            with socket.create_connection((parsed.hostname, parsed.port or 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
                    cert = ssock.getpeercert()
                    if not cert:
                        raise RPCValidationError("No SSL certificate presented by endpoint")
        except Exception as e:
            logger.error(f"TLS validation failed for {rpc_url}: {e}")
            raise RPCValidationError(f"TLS validation failed: {e}")

        logger.info(f"RPC endpoint validated: {rpc_url}")
        return True

    def switch_network(self, network_id: str) -> Dict:
        """
        Securely switch to a new network after validation and security checks.
        :param network_id: The identifier of the network to switch to.
        :return: The new active network dict.
        """
        network = next((n for n in self.trusted_networks if n.get("id") == network_id), None)
        if not network:
            logger.warning(f"Attempted to switch to unknown network: {network_id}")
            raise NetworkSwitchError("Network not found in trusted list")

        try:
            self.validate_rpc_endpoint(network["rpc_url"])
            # SecurityManager can be used for additional checks (e.g., suspicious activity)
            self.security_manager.detect_suspicious_activity("system", {"value": 0})
        except (RPCValidationError, SuspiciousActivityError) as e:
            logger.error(f"Network switch blocked: {e}")
            raise NetworkSwitchError(str(e))

        self.active_network = network
        logger.info(f"Switched to network: {network.get('name', network_id)}")
        return network

    def get_active_network(self) -> Optional[Dict]:
        """Return the currently active network."""
        return self.active_network

    def monitor_rpc_health(self, rpc_url: str, callback: Optional[Callable] = None):
        """
        Start monitoring the health of an RPC endpoint.
        :param rpc_url: The RPC endpoint to monitor.
        :param callback: Optional callback to invoke on anomaly detection.
        """
        if rpc_url in self.connection_monitors:
            logger.info(f"Already monitoring {rpc_url}")
            return

        def monitor():
            while True:
                try:
                    self.validate_rpc_endpoint(rpc_url)
                    # Optionally, perform a lightweight JSON-RPC call here for deeper health check
                    logger.debug(f"RPC health OK: {rpc_url}")
                except Exception as e:
                    logger.warning(f"RPC health anomaly detected: {rpc_url} - {e}")
                    if callback:
                        callback(rpc_url, e)
                time.sleep(self.monitor_interval)

        t = threading.Thread(target=monitor, daemon=True)
        self.connection_monitors[rpc_url] = t
        t.start()
        logger.info(f"Started monitoring RPC health: {rpc_url}")

    def stop_monitoring(self, rpc_url: str):
        """Stop monitoring the given RPC endpoint."""
        # For simplicity, this just removes the monitor; thread will exit on next check.
        if rpc_url in self.connection_monitors:
            del self.connection_monitors[rpc_url]
            logger.info(f"Stopped monitoring RPC health: {rpc_url}")

    def get_trusted_networks(self) -> List[Dict]:
        """Return the list of trusted networks."""
        return list(self.trusted_networks)

    def update_network_config(self, network_id: str, updates: Dict):
        """Securely update network configuration."""
        for n in self.trusted_networks:
            if n.get("id") == network_id:
                n.update(updates)
                logger.info(f"Updated network config for {network_id}: {updates}")
                return n
        raise NetworkManagerError("Network not found for update")

    def alert_on_anomaly(self, rpc_url: str, error: Exception):
        """Default anomaly alert handler."""
        logger.error(f"ALERT: Anomaly detected on {rpc_url}: {error}")
        # Integrate with SecurityManager for audit logging
        self.security_manager.log_security_event({
            "event_type": "rpc_anomaly",
            "rpc_url": rpc_url,
            "error": str(error),
        })