"""
NamespaceManager

Handles multi-chain namespace management for WalletConnect v2.
Supports dynamic namespace construction, chain switching, and cross-chain account management.

TDD Anchors:
- Should build required namespaces correctly for all supported chains
- Should include all required methods and events
- Should support dynamic addition and removal of chains
- Should validate namespace structure and chain support
"""

from typing import List, Dict, Any

class NamespaceManager:
    """
    Manages WalletConnect namespaces for multi-chain support.
    """

    def __init__(self, supported_chains: List[int]):
        """
        Initialize NamespaceManager with supported chain IDs.
        """
        self.supported_chains = supported_chains

    def build_required_namespaces(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build required namespaces for WalletConnect session proposal.
        """
        # TDD: Should build required namespaces correctly
        eip155_chains = [f"eip155:{chain_id}" for chain_id in self.supported_chains]
        return {
            "eip155": {
                "chains": eip155_chains,
                "methods": [
                    "eth_sendTransaction",
                    "eth_signTransaction",
                    "eth_sign",
                    "personal_sign",
                    "eth_signTypedData",
                    "eth_signTypedData_v4"
                ],
                "events": [
                    "chainChanged",
                    "accountsChanged"
                ]
            }
        }

    def build_optional_namespaces(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build optional namespaces for WalletConnect session proposal.
        """
        # TDD: Should build optional namespaces correctly
        eip155_chains = [f"eip155:{chain_id}" for chain_id in self.supported_chains]
        return {
            "eip155": {
                "chains": eip155_chains,
                "methods": [
                    "eth_accounts",
                    "eth_requestAccounts",
                    "eth_getBalance",
                    "eth_chainId",
                    "wallet_switchEthereumChain",
                    "wallet_addEthereumChain",
                    "wallet_watchAsset"
                ],
                "events": [
                    "connect",
                    "disconnect"
                ]
            }
        }