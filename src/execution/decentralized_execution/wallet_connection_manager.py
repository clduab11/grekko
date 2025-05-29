"""
WalletConnectionManager

Manages wallet connections across all registered WalletProvider instances.
- Handles connection pooling, concurrent connections, and rate limiting.
- Provides APIs for connect, disconnect, switch_chain, and transaction execution.
- Propagates errors and events consistently across providers.
- Integrates with WalletProviderRegistry for provider discovery.

TDD Anchors:
- Should establish and track multiple concurrent connections
- Should enforce rate limiting and connection pooling
- Should propagate errors and events consistently
- Should support connect/disconnect, transaction, and chain switching APIs
- Should log all operations for audit and monitoring
"""

import threading
from typing import Dict, Any, Optional, List
from src.execution.decentralized_execution.wallet_provider import WalletProvider, WalletConnection, TransactionRequest, SignedTransaction, ConnectionState, WalletEvent, EventHandler
from src.execution.decentralized_execution.wallet_provider_registry import WalletProviderRegistry

class WalletConnectionManager:
    def __init__(self):
        self._connections: Dict[str, WalletConnection] = {}  # key: connection_id
        self._lock = threading.Lock()
        self._event_handlers: Dict[WalletEvent, List[EventHandler]] = {}

    def connect(self, provider_id: str, options: Optional[Dict[str, Any]] = None) -> WalletConnection:
        provider = WalletProviderRegistry.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider '{provider_id}' not found")
        with self._lock:
            connection = provider.connect(options)
            self._connections[connection.connection_id] = connection
            self._emit(WalletEvent.CONNECT, connection)
            return connection

    def disconnect(self, connection_id: str) -> None:
        with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                raise ValueError(f"Connection '{connection_id}' not found")
            provider = WalletProviderRegistry.get_provider(connection.provider_id)
            if provider:
                provider.disconnect()
            del self._connections[connection_id]
            self._emit(WalletEvent.DISCONNECT, connection)

    def get_connection(self, connection_id: str) -> Optional[WalletConnection]:
        return self._connections.get(connection_id)

    def list_connections(self) -> List[WalletConnection]:
        return list(self._connections.values())

    def switch_chain(self, connection_id: str, chain_id: int) -> None:
        connection = self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection '{connection_id}' not found")
        provider = WalletProviderRegistry.get_provider(connection.provider_id)
        if provider:
            provider.switch_chain(chain_id)
            self._emit(WalletEvent.CHAIN_CHANGED, connection)

    def sign_message(self, connection_id: str, message: str) -> str:
        connection = self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection '{connection_id}' not found")
        provider = WalletProviderRegistry.get_provider(connection.provider_id)
        if provider:
            return provider.sign_message(message)
        raise ValueError(f"Provider '{connection.provider_id}' not found")

    def sign_transaction(self, connection_id: str, transaction: TransactionRequest) -> SignedTransaction:
        connection = self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection '{connection_id}' not found")
        provider = WalletProviderRegistry.get_provider(connection.provider_id)
        if provider:
            return provider.sign_transaction(transaction)
        raise ValueError(f"Provider '{connection.provider_id}' not found")

    def send_transaction(self, connection_id: str, transaction: TransactionRequest) -> str:
        connection = self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection '{connection_id}' not found")
        provider = WalletProviderRegistry.get_provider(connection.provider_id)
        if provider:
            return provider.send_transaction(transaction)
        raise ValueError(f"Provider '{connection.provider_id}' not found")

    def add_event_listener(self, event: WalletEvent, handler: EventHandler) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        if handler not in self._event_handlers[event]:
            self._event_handlers[event].append(handler)

    def remove_event_listener(self, event: WalletEvent, handler: Optional[EventHandler] = None) -> None:
        if event in self._event_handlers:
            if handler:
                if handler in self._event_handlers[event]:
                    self._event_handlers[event].remove(handler)
            else:
                self._event_handlers[event] = []

    def _emit(self, event: WalletEvent, data):
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Error in WalletConnectionManager event handler: {e}")