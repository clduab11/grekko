import ccxt.pro as ccxt
import logging

class CoinbaseConnector:
    def __init__(self, api_key, api_secret, passphrase):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.exchange = ccxt.coinbasepro({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.passphrase,
            'enableRateLimit': True,
        })
        self.logger = logging.getLogger(__name__)

    async def fetch_ticker(self, symbol):
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")

    async def create_order(self, symbol, order_type, side, amount, price=None):
        try:
            order = await self.exchange.create_order(symbol, order_type, side, amount, price)
            return order
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
