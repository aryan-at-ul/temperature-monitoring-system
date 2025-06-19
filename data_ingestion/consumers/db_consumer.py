import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from database.repositories.repositories import TemperatureReadingRepository
from data_ingestion.processors.data_processor import DataProcessor
from data_ingestion.queue.rabbitmq_client import rabbitmq

logger = logging.getLogger(__name__)


class DatabaseConsumer:
    """Consumer that processes queue messages and writes to the database"""

    def __init__(self, batch_size: int = 100, batch_timeout: int = 10):
        self.processor = DataProcessor()
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_batch = []
        self.last_flush_time = datetime.now()
        self.is_running = False
        self.flush_task = None

    async def start(self):
        """Start the consumer"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Connect to RabbitMQ
        await rabbitmq.connect()
        
        # Start the message consumer
        await rabbitmq.consume(
            callback=self.handle_message,
            queue_name="temperature_readings",
            routing_key="temperature.#"
        )
        
        # Start the batch flushing task
        self.flush_task = asyncio.create_task(self.periodic_flush())
        logger.info("Database consumer started")

    async def stop(self):
        """Stop the consumer"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Cancel the flush task
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
            
        # Flush any remaining items
        await self.flush_batch()
        
        # Close RabbitMQ connection
        await rabbitmq.close()
        
        logger.info("Database consumer stopped")

    async def handle_message(self, message: Dict[str, Any]):
        """Handle a message from the queue"""
        try:
            # Map the event to a temperature reading
            reading = self.processor.map_temperature_reading(message)
            
            # Add to the pending batch
            self.pending_batch.append(reading)
            
            # Flush if batch size reached
            if len(self.pending_batch) >= self.batch_size:
                await self.flush_batch()
                
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    async def flush_batch(self):
        """Flush the current batch to the database"""
        if not self.pending_batch:
            return
            
        batch_to_flush = self.pending_batch
        self.pending_batch = []
        self.last_flush_time = datetime.now()
        
        try:
            # Insert batch into database
            count = await TemperatureReadingRepository.create_batch(batch_to_flush)
            logger.info(f"Inserted {count} temperature readings into database")
            
        except Exception as e:
            logger.error(f"Error flushing batch to database: {e}", exc_info=True)
            
            # Put items back in the batch for retry
            self.pending_batch.extend(batch_to_flush)

    async def periodic_flush(self):
        """Periodically flush the batch if timeout is reached"""
        while self.is_running:
            try:
                # Sleep for a bit
                await asyncio.sleep(1)
                
                # Check if timeout reached
                now = datetime.now()
                seconds_since_flush = (now - self.last_flush_time).total_seconds()
                
                if seconds_since_flush >= self.batch_timeout and self.pending_batch:
                    await self.flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}", exc_info=True)