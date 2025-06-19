import asyncio
import logging
import signal
import sys
import os

from database.connection import db
from data_ingestion.queue.rabbitmq_client import rabbitmq
from data_ingestion.schedulers.ingestion_scheduler import IngestionScheduler
from data_ingestion.consumer.db_consumer import DatabaseConsumer

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/data_ingestion.log"),
    ]
)

logger = logging.getLogger(__name__)


class IngestionService:
    """Main ingestion service that manages the scheduler and consumer"""

    def __init__(self):
        self.scheduler = IngestionScheduler()
        self.consumer = DatabaseConsumer()
        self.running = False
        self.stop_event = asyncio.Event()

    async def start(self):
        """Start the ingestion service"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting ingestion service")
        
        # Connect to the database
        await db.connect()
        
        # Connect to RabbitMQ
        await rabbitmq.connect()
        
        # Start the scheduler and consumer
        await self.scheduler.start()
        await self.consumer.start()
        
        logger.info("Ingestion service started")

    async def stop(self):
        """Stop the ingestion service"""
        if not self.running:
            return
            
        self.running = False
        logger.info("Stopping ingestion service")
        
        # Stop the scheduler and consumer
        await self.scheduler.stop()
        await self.consumer.stop()
        
        # Close connections
        await rabbitmq.close()
        await db.close()
        
        # Set the stop event
        self.stop_event.set()
        
        logger.info("Ingestion service stopped")

    async def run(self):
        """Run the service until stopped"""
        # Register signal handlers
        loop = asyncio.get_running_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
        
        # Start the service
        await self.start()
        
        # Wait for stop event
        await self.stop_event.wait()


async def main():
    """Main entry point"""
    try:
        # Create and run the service
        service = IngestionService()
        await service.run()
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Ensure database connection is closed
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
