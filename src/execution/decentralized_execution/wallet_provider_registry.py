"""
WalletProviderRegistry

Central registry for all WalletProvider implementations.
- Supports plugin registration, discovery, and lifecycle management.
- Enforces interface compliance and uniqueness of provider_id.
- Provides event-driven hooks for provider addition/removal.
- Used by WalletConnectionManager for provider lookup and orchestration.

TDD Anchors:
- Should register and unregister providers by provider_id
- Should prevent duplicate provider_id registration
- Should allow lookup by provider_id and list all providers
- Should emit events on provider registration/removal
- Should validate interface compliance on registration
"""

from typing import Dict, Type, Optional, List
from src.execution.decentralized_execution.wallet_provider import WalletProvider, WalletEvent, EventHandler

class WalletProviderRegistry:
    _providers: Dict[str, WalletProvider] = {}
    _event_handlers: Dict[WalletEvent, List[EventHandler]] = {}

    @classmethod
    def register_provider(cls, provider: WalletProvider) -> None:
        provider_id = provider.provider_id
        if provider_id in cls._providers:
            raise ValueError(f"Provider with id '{provider_id}' already registered")
        if not isinstance(provider, WalletProvider):
            raise TypeError("Provider must implement WalletProvider interface")
        cls._providers[provider_id] = provider
        cls._emit(WalletEvent.CONNECT, provider)
    
    @classmethod
    def unregister_provider(cls, provider_id: str) -> None:
        if provider_id in cls._providers:
            provider = cls._providers.pop(provider_id)
            cls._emit(WalletEvent.DISCONNECT, provider)
    
    @classmethod
    def get_provider(cls, provider_id: str) -> Optional[WalletProvider]:
        return cls._providers.get(provider_id)
    
    @classmethod
    def list_providers(cls) -> List[WalletProvider]:
        return list(cls._providers.values())
    
    @classmethod
    def add_event_listener(cls, event: WalletEvent, handler: EventHandler) -> None:
        if event not in cls._event_handlers:
            cls._event_handlers[event] = []
        if handler not in cls._event_handlers[event]:
            cls._event_handlers[event].append(handler)
    
    @classmethod
    def remove_event_listener(cls, event: WalletEvent, handler: Optional[EventHandler] = None) -> None:
        if event in cls._event_handlers:
            if handler:
                if handler in cls._event_handlers[event]:
                    cls._event_handlers[event].remove(handler)
            else:
                cls._event_handlers[event] = []
    
    @classmethod
    def _emit(cls, event: WalletEvent, data):
        handlers = cls._event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                # Replace with project logger as needed
                print(f"Error in WalletProviderRegistry event handler: {e}")