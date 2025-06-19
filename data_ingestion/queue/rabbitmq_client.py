import os
import json
import uuid
import aio_pika
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

logger = logging.getLogger(__name__)


# Custom JSON encoder for UUID objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class RabbitMQClient:
    def __init__(
        self,
        host: str = os.getenv("RABBITMQ_HOST", "localhost"),
        port: int = int(os.getenv("RABBITMQ_PORT", "5672")),
        username: str = os.getenv("RABBITMQ_USER", "guest"),
        password: str = os.getenv("RABBITMQ_PASSWORD", "guest"),
        vhost: str = os.getenv("RABBITMQ_VHOST", "/"),
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        self.connection = None
        self.channel = None
        self.exchange = None
        self.default_exchange_name = "temperature_data"
        self.default_queue_name = "temperature_readings"





    async def connect(self) -> None:
        """Connect to RabbitMQ server"""
        try:
            # Build connection string
            connection_str = f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.vhost}"
            
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(connection_str)
            self.channel = await self.connection.channel()
            
            # Declare the exchange
            self.exchange = await self.channel.declare_exchange(
                self.default_exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def close(self) -> None:
        """Close the connection"""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")

    async def publish(
        self, 
        message: Dict[str, Any], 
        routing_key: str = "temperature.reading",
        exchange_name: Optional[str] = None
    ) -> None:
        """Publish a message to the exchange"""
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
            
        # Convert message to JSON using the custom encoder
        message_body = json.dumps(message, cls=CustomJSONEncoder).encode()
        
        # Get the exchange
        if exchange_name and exchange_name != self.default_exchange_name:
            exchange = await self.channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
        else:
            exchange = self.exchange
            
        # Publish the message
        await exchange.publish(
            aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )
        
        logger.debug(f"Published message with routing key '{routing_key}'")

    async def consume(
        self,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
        queue_name: str = None,
        routing_key: str = "temperature.#",
        exchange_name: Optional[str] = None
    ) -> None:
        """Set up a consumer for a queue"""
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        # Use default queue name if not provided
        if queue_name is None:
            queue_name = self.default_queue_name
            
        # Get the exchange
        if exchange_name and exchange_name != self.default_exchange_name:
            exchange = await self.channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
        else:
            exchange = self.exchange
            
        # Declare the queue
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            auto_delete=False
        )
        
        # Bind the queue to the exchange
        await queue.bind(exchange, routing_key)
        
        # Set up the consumer
        async def process_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Reject the message and requeue it
                    await message.reject(requeue=True)
        
        # Start consuming
        await queue.consume(process_message)
        logger.info(f"Started consuming from queue '{queue_name}' with routing key '{routing_key}'")




async def check_connection(
    host: str = os.getenv("RABBITMQ_HOST", "localhost"),
    port: int = int(os.getenv("RABBITMQ_PORT", "5672")),
    username: str = os.getenv("RABBITMQ_USER", "guest"),
    password: str = os.getenv("RABBITMQ_PASSWORD", "guest"),
    vhost: str = os.getenv("RABBITMQ_VHOST", "/"),
) -> bool:
    """Check if RabbitMQ connection is available"""
    try:
        # Build connection string
        connection_str = f"amqp://{username}:{password}@{host}:{port}/{vhost}"
        
        # Try to connect
        connection = await aio_pika.connect_robust(connection_str)
        await connection.close()
        logger.info(f"RabbitMQ connection check successful at {host}:{port}")
        return True
    except Exception as e:
        logger.error(f"RabbitMQ connection check failed: {e}")
        return False


# RabbitMQ singleton instance
rabbitmq = RabbitMQClient()
