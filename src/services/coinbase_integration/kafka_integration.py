"""
Kafka Integration for Coinbase Integration.

Responsibilities:
- Market data publishing to market-data topic
- Order events to trade-events topic
- Portfolio updates to portfolio-events topic
- Error events to error-events topic
- Message serialization and compression
"""

from typing import Any, Dict

import json
import logging
try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None

logger = logging.getLogger(__name__)

class KafkaIntegration:
    """
    Handles publishing events to Kafka topics for market data, orders, portfolio, and errors.
    """
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize Kafka producer and set up topic names.
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.topics = {
            "market_data": "market-data",
            "order": "trade-events",
            "portfolio": "portfolio-events",
            "error": "error-events"
        }

    async def start(self):
        """
        Start Kafka producer.
        """
        if AIOKafkaProducer is None:
            logger.warning("aiokafka library not installed. Kafka integration disabled.")
            return
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully.")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self):
        """
        Stop Kafka producer if initialized.
        """
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped.")

    async def publish_market_data(self, data: Dict[str, Any]):
        """
        Publish market data event to Kafka.
        """
        await self._publish_event("market_data", data)

    async def publish_order_event(self, event: Dict[str, Any]):
        """
        Publish order event to Kafka.
        """
        await self._publish_event("order", event)

    async def publish_portfolio_update(self, update: Dict[str, Any]):
        """
        Publish portfolio update event to Kafka.
        """
        await self._publish_event("portfolio", update)

    async def publish_error_event(self, error: Dict[str, Any]):
        """
        Publish error event to Kafka.
        """
        await self._publish_event("error", error)

    async def _publish_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Internal helper to publish an event to the appropriate Kafka topic.
        """
        if event_type not in self.topics:
            logger.error(f"Unknown event type: {event_type}")
            raise ValueError(f"Unknown event type: {event_type}")
        topic = self.topics[event_type]
        if self.producer is None:
            logger.error("Kafka producer not initialized")
            raise RuntimeError("Kafka producer not initialized")
        try:
            await self.producer.send_and_wait(topic, event_data)
            logger.info(f"Published {event_type} event to {topic}")
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
            raise