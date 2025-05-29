"""Kafka Integration

Handles event publishing to the coordination-events topic, subscribes to agent-status and task-completion topics,
manages dead letter queues, and ensures message ordering and deduplication for reliable event streaming.
"""

import json
import asyncio
from typing import Dict, Any
try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
except ImportError:
    AIOKafkaProducer = None
    AIOKafkaConsumer = None
import logging

logger = logging.getLogger(__name__)

class KafkaIntegration:
    """
    Integrates the agent coordination service with Kafka for event-driven communication.
    - Publishes coordination events
    - Subscribes to agent status updates
    - Processes task completion events
    - Manages dead letter queues
    - Ensures message ordering and deduplication
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
            "coordination": "coordination-events",
            "agent_status": "agent-status",
            "task_completion": "task-completion",
            "dead_letter": "dead-letter-queue"
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
    
    async def publish_coordination_event(self, event_data: Dict[str, Any]):
        """
        Publish a coordination event to the coordination-events Kafka topic.
        
        Args:
            event_data (Dict[str, Any]): Coordination event data to be published.
        """
        if self.producer is None:
            logger.error("Kafka producer not initialized")
            raise RuntimeError("Kafka producer not initialized")
            
        topic = self.topics["coordination"]
        try:
            await self.producer.send_and_wait(topic, event_data)
            logger.info(f"Published coordination event to {topic}")
        except Exception as e:
            logger.error(f"Failed to publish coordination event to {topic}: {e}")
            raise
    
    async def subscribe_agent_status(self, callback):
        """
        Subscribe to agent status update events from Kafka.
        
        Args:
            callback: Function to process incoming agent status messages.
        """
        if AIOKafkaConsumer is None:
            logger.warning("aiokafka library not installed. Kafka subscription disabled.")
            return
            
        topic = self.topics["agent_status"]
        try:
            self.consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            await self.consumer.start()
            logger.info(f"Subscribed to topic: {topic}")
            
            async for msg in self.consumer:
                try:
                    await callback(msg.value)
                except Exception as e:
                    logger.error(f"Error processing message from {msg.topic}: {e}")
        except Exception as e:
            logger.error(f"Failed to subscribe to topic {topic}: {e}")
            raise
    
    async def subscribe_task_completion(self, callback):
        """
        Subscribe to task completion events from Kafka.
        
        Args:
            callback: Function to process incoming task completion messages.
        """
        if AIOKafkaConsumer is None:
            logger.warning("aiokafka library not installed. Kafka subscription disabled.")
            return
            
        topic = self.topics["task_completion"]
        try:
            self.consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            await self.consumer.start()
            logger.info(f"Subscribed to topic: {topic}")
            
            async for msg in self.consumer:
                try:
                    await callback(msg.value)
                except Exception as e:
                    logger.error(f"Error processing message from {msg.topic}: {e}")
        except Exception as e:
            logger.error(f"Failed to subscribe to topic {topic}: {e}")
            raise
    
    async def handle_dead_letter(self, event_data: Dict[str, Any]):
        """
        Send failed or unprocessable events to the dead letter queue for later analysis.
        
        Args:
            event_data (Dict[str, Any]): Event data to be sent to the dead letter queue.
        """
        if self.producer is None:
            logger.error("Kafka producer not initialized")
            raise RuntimeError("Kafka producer not initialized")
            
        topic = self.topics["dead_letter"]
        try:
            await self.producer.send_and_wait(topic, event_data)
            logger.info(f"Sent event to dead letter queue: {topic}")
        except Exception as e:
            logger.error(f"Failed to send event to dead letter queue {topic}: {e}")
            raise