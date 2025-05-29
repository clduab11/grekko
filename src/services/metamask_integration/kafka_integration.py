"""Kafka Integration

Handles event streaming and messaging, including:
- Wallet events to wallet-events topic
- Transaction events to transaction-events topic
- Balance updates to portfolio-events topic
- Error events to error-events topic
- Network events to network-events topic

Enables real-time event distribution across the trading system.
"""

import json
import asyncio
from typing import Dict, Any, Optional
try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
except ImportError:
    AIOKafkaProducer = None
    AIOKafkaConsumer = None
import logging

logger = logging.getLogger(__name__)

class KafkaIntegration:
    """
    Manages Kafka interactions for the Metamask Integration Service.
    Publishes events to specific topics and subscribes to relevant topics for cross-service communication.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize Kafka producer and consumer.
        
        Args:
            bootstrap_servers (str): Kafka bootstrap servers address.
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumer = None
        self.topics = {
            "wallet": "wallet-events",
            "transaction": "transaction-events",
            "portfolio": "portfolio-events",
            "error": "error-events",
            "network": "network-events"
        }
    
    async def start(self):
        """
        Start Kafka producer.
        Note: Ensure 'aiokafka' library is installed (`pip install aiokafka`).
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
        Stop Kafka producer and consumer if initialized.
        """
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped.")
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped.")
    
    async def publish_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Publish an event to the appropriate Kafka topic.
        
        Args:
            event_type (str): Type of event (wallet, transaction, portfolio, error, network).
            event_data (Dict[str, Any]): Event data to be published.
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
    
    async def subscribe_to_topics(self, topics: list, callback):
        """
        Subscribe to specified Kafka topics and process messages with the provided callback.
        
        Args:
            topics (list): List of topics to subscribe to.
            callback: Function to process incoming messages.
        """
        if AIOKafkaConsumer is None:
            logger.warning("aiokafka library not installed. Kafka subscription disabled.")
            return
            
        try:
            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            await self.consumer.start()
            logger.info(f"Subscribed to topics: {topics}")
            
            async for msg in self.consumer:
                try:
                    await callback(msg.value)
                except Exception as e:
                    logger.error(f"Error processing message from {msg.topic}: {e}")
        except Exception as e:
            logger.error(f"Failed to subscribe to topics {topics}: {e}")
            raise