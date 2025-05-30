import ccxt.pro as ccxt
import logging
import time

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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
        max_retries = 5
        for attempt in range(max_retries):
            try:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
                return order
            except ccxt.NetworkError as e:
                self.logger.error(f"Network error: {e}")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Exchange error: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
            self.logger.info(f"Retrying order creation ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        self.logger.error("Order creation failed after multiple attempts")

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

    async def create_order(self, symbol, order_type, side,
        amount, price=None):
        """Create an order on the exchange"""
        try:
            if order_type == "limit" and price is None:
                raise ValueError("Limit orders require a price")
                
            if order_type == "market":
                order = await self.exchange.create_market_order(symbol, side, amount)
            else:
                order = await self.exchange.create_limit_order(symbol, side, amount, price)
                
            return order
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error: {e}")
        except ccxt.ExchangeError as e:
            self.logger.error(f"Exchange error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        return None
