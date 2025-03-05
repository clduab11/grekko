import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.contract import Contract

class UniswapExecutor:
    def __init__(self, provider_url):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.logger = logging.getLogger(__name__)

    def get_contract(self, address, abi) -> Contract:
        return self.web3.eth.contract(address=address, abi=abi)

    def estimate_gas(self, transaction):
        try:
            gas_estimate = self.web3.eth.estimate_gas(transaction)
            gas_buffer = int(gas_estimate * 1.2)  # Adding a 20% buffer
            return gas_buffer
        except Exception as e:
            self.logger.error(f"Error estimating gas: {e}")
            return None

    def execute_transaction(self, transaction):
        try:
            gas_limit = self.estimate_gas(transaction)
            if gas_limit:
                transaction.update({'gas': gas_limit})
                tx_hash = self.web3.eth.send_transaction(transaction)
                self.logger.info(f"Transaction sent: {tx_hash.hex()}")
                return tx_hash
            else:
                self.logger.error("Gas estimation failed. Transaction not sent.")
                return None
        except Exception as e:
            self.logger.error(f"Error executing transaction: {e}")
            return None
