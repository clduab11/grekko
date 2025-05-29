"""
Unit tests for WalletProvider and its implementations.
"""

import pytest
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.execution.decentralized_execution.wallet_provider import WalletProvider, MetaMaskProvider, CoinbaseWalletProvider

class TestWalletProvider:
    """
    Tests for the WalletProvider abstract base class.
    """

    def test_wallet_provider_is_abstract(self):
        """
        Test that WalletProvider cannot be instantiated directly
        and that subclasses must implement abstract methods.
        """
        # Attempting to instantiate WalletProvider directly should fail
        # However, Python's ABC doesn't prevent instantiation if all methods have default `pass`
        # The real test is if a subclass fails without implementing methods.

        class IncompleteProvider(WalletProvider):
            # Missing connect, is_connected, get_address, sign_transaction, send_transaction
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteProvider with abstract methods connect, get_address, is_connected, send_transaction, sign_transaction"):
            # The error message might vary slightly based on Python version and specific missing methods
            # We are checking for TypeError due to unimplmented abstract methods.
            # Let's refine the match to be more general for abstract methods.
            # A more robust check for Python 3.7+ for the specific methods:
            # "Can't instantiate abstract class IncompleteProvider with abstract methods connect, get_address, is_connected, send_transaction, sign_transaction"
            # For older versions, it might just say "abstract methods" without listing them.
            # Let's try to catch the general idea.
            IncompleteProvider()

    def test_connect_is_abstract(self):
        """Test that the 'connect' method is abstract."""
        class MinimalProvider(WalletProvider):
            def is_connected(self) -> bool: return False
            def get_address(self) -> Optional[str]: return None
            def sign_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            def send_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            # connect is missing

        with pytest.raises(TypeError, match="Can't instantiate abstract class MinimalProvider with abstract method connect"):
            MinimalProvider()

    def test_is_connected_is_abstract(self):
        """Test that the 'is_connected' method is abstract."""
        class MinimalProvider(WalletProvider):
            def connect(self, connection_params: Dict[str, Any]) -> bool: return False
            def get_address(self) -> Optional[str]: return None
            def sign_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            def send_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            # is_connected is missing

        with pytest.raises(TypeError, match="Can't instantiate abstract class MinimalProvider with abstract method is_connected"):
            MinimalProvider()

    def test_get_address_is_abstract(self):
        """Test that the 'get_address' method is abstract."""
        class MinimalProvider(WalletProvider):
            def connect(self, connection_params: Dict[str, Any]) -> bool: return False
            def is_connected(self) -> bool: return False
            def sign_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            def send_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            # get_address is missing

        with pytest.raises(TypeError, match="Can't instantiate abstract class MinimalProvider with abstract method get_address"):
            MinimalProvider()

    def test_sign_transaction_is_abstract(self):
        """Test that the 'sign_transaction' method is abstract."""
        class MinimalProvider(WalletProvider):
            def connect(self, connection_params: Dict[str, Any]) -> bool: return False
            def is_connected(self) -> bool: return False
            def get_address(self) -> Optional[str]: return None
            def send_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            # sign_transaction is missing

        with pytest.raises(TypeError, match="Can't instantiate abstract class MinimalProvider with abstract method sign_transaction"):
            MinimalProvider()

    def test_send_transaction_is_abstract(self):
        """Test that the 'send_transaction' method is abstract."""
        class MinimalProvider(WalletProvider):
            def connect(self, connection_params: Dict[str, Any]) -> bool: return False
            def is_connected(self) -> bool: return False
            def get_address(self) -> Optional[str]: return None
            def sign_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]: return None
            # send_transaction is missing

        with pytest.raises(TypeError, match="Can't instantiate abstract class MinimalProvider with abstract method send_transaction"):
            MinimalProvider()


class TestMetaMaskProvider:
    """
    Tests for the MetaMaskProvider implementation.
    """

    def test_metamask_provider_instantiation(self):
        """Test that MetaMaskProvider can be instantiated."""
        provider = MetaMaskProvider()
        assert provider is not None
        assert isinstance(provider, WalletProvider)

    def test_connect_with_valid_params_returns_true(self):
        """Test that connect returns True when connection is successful."""
        provider = MetaMaskProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        
        result = provider.connect(connection_params)
        
        assert result is True

    def test_connect_with_invalid_params_returns_false(self):
        """Test that connect returns False when connection fails."""
        provider = MetaMaskProvider()
        connection_params = {"invalid": "params"}
        
        result = provider.connect(connection_params)
        
        assert result is False

    def test_is_connected_returns_false_when_not_connected(self):
        """Test that is_connected returns False when wallet is not connected."""
        provider = MetaMaskProvider()
        
        result = provider.is_connected()
        
        assert result is False

    def test_is_connected_returns_true_when_connected(self):
        """Test that is_connected returns True after successful connection."""
        provider = MetaMaskProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        
        provider.connect(connection_params)
        result = provider.is_connected()
        
        assert result is True

    def test_get_address_returns_none_when_not_connected(self):
        """Test that get_address returns None when wallet is not connected."""
        provider = MetaMaskProvider()
        
        result = provider.get_address()
        
        assert result is None

    def test_get_address_returns_address_when_connected(self):
        """Test that get_address returns wallet address when connected."""
        provider = MetaMaskProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        
        provider.connect(connection_params)
        result = provider.get_address()
        
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith("0x")

    def test_sign_transaction_returns_none_when_not_connected(self):
        """Test that sign_transaction returns None when wallet is not connected."""
        provider = MetaMaskProvider()
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        result = provider.sign_transaction(transaction_data)
        
        assert result is None

    def test_sign_transaction_returns_signature_when_connected(self):
        """Test that sign_transaction returns signature when wallet is connected."""
        provider = MetaMaskProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        provider.connect(connection_params)
        result = provider.sign_transaction(transaction_data)
        
        assert result is not None
        assert isinstance(result, str)

    def test_send_transaction_returns_none_when_not_connected(self):
        """Test that send_transaction returns None when wallet is not connected."""
        provider = MetaMaskProvider()
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        result = provider.send_transaction(transaction_data)
        
        assert result is None

    def test_send_transaction_returns_hash_when_connected(self):
        """Test that send_transaction returns transaction hash when wallet is connected."""
        provider = MetaMaskProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        provider.connect(connection_params)
        result = provider.send_transaction(transaction_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith("0x")


class TestCoinbaseWalletProvider:
    """
    Tests for the CoinbaseWalletProvider implementation.
    """

    def test_coinbase_provider_instantiation(self):
        """Test that CoinbaseWalletProvider can be instantiated."""
        provider = CoinbaseWalletProvider()
        assert provider is not None
        assert isinstance(provider, WalletProvider)

    def test_connect_with_valid_params_returns_true(self):
        """Test that connect returns True when connection is successful."""
        provider = CoinbaseWalletProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        
        result = provider.connect(connection_params)
        
        assert result is True

    def test_connect_with_invalid_params_returns_false(self):
        """Test that connect returns False when connection fails."""
        provider = CoinbaseWalletProvider()
        connection_params = {"invalid": "params"}
        
        result = provider.connect(connection_params)
        
        assert result is False

    def test_is_connected_returns_false_when_not_connected(self):
        """Test that is_connected returns False when wallet is not connected."""
        provider = CoinbaseWalletProvider()
        
        result = provider.is_connected()
        
        assert result is False

    def test_is_connected_returns_true_when_connected(self):
        """Test that is_connected returns True after successful connection."""
        provider = CoinbaseWalletProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        
        provider.connect(connection_params)
        result = provider.is_connected()
        
        assert result is True

    def test_get_address_returns_none_when_not_connected(self):
        """Test that get_address returns None when wallet is not connected."""
        provider = CoinbaseWalletProvider()
        
        result = provider.get_address()
        
        assert result is None

    def test_get_address_returns_address_when_connected(self):
        """Test that get_address returns wallet address when connected."""
        provider = CoinbaseWalletProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        
        provider.connect(connection_params)
        result = provider.get_address()
        
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith("0x")

    def test_sign_transaction_returns_none_when_not_connected(self):
        """Test that sign_transaction returns None when wallet is not connected."""
        provider = CoinbaseWalletProvider()
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        result = provider.sign_transaction(transaction_data)
        
        assert result is None

    def test_sign_transaction_returns_signature_when_connected(self):
        """Test that sign_transaction returns signature when wallet is connected."""
        provider = CoinbaseWalletProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        provider.connect(connection_params)
        result = provider.sign_transaction(transaction_data)
        
        assert result is not None
        assert isinstance(result, str)

    def test_send_transaction_returns_none_when_not_connected(self):
        """Test that send_transaction returns None when wallet is not connected."""
        provider = CoinbaseWalletProvider()
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        result = provider.send_transaction(transaction_data)
        
        assert result is None

    def test_send_transaction_returns_hash_when_connected(self):
        """Test that send_transaction returns transaction hash when wallet is connected."""
        provider = CoinbaseWalletProvider()
        connection_params = {"network": "ethereum", "chain_id": 1}
        transaction_data = {"to": "0x123", "value": "1000000000000000000"}
        
        provider.connect(connection_params)
        result = provider.send_transaction(transaction_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith("0x")