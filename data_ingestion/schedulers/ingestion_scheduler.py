import logging
import asyncio
import schedule
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from database.connection import db
from database.repositories.repositories import (
    CustomerRepository, IngestionLogRepository
)
from data_ingestion.collectors.api_collector import APICollector
from data_ingestion.collectors.csv_collector import CSVCollector
from data_ingestion.processors.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """Schedules data ingestion jobs based on customer configurations"""

    def __init__(self):
        self.api_collector = APICollector()
        self.csv_collector = CSVCollector()
        self.processor = DataProcessor()
        self.running_tasks = {}
        self.is_running = False

    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("Starting ingestion scheduler")
        
        # Initialize collectors
        await self.api_collector.initialize()
        await self.csv_collector.initialize()
        
        # Schedule the initial runs
        await self.schedule_all_customers()
        
        # Start the scheduler loop
        asyncio.create_task(self._run_scheduler())

    async def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
            
        self.is_running = False
        logger.info("Stopping ingestion scheduler")
        
        # Cancel all running tasks
        for task in self.running_tasks.values():
            task.cancel()
            
        # Clear the schedule
        schedule.clear()
        
        # Close collectors
        await self.api_collector.close()
        await self.csv_collector.close()

    async def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            # Run pending scheduled jobs
            schedule.run_pending()
            
            # Sleep for a short time
            await asyncio.sleep(1)
            
    async def schedule_all_customers(self):
        """Schedule ingestion for all active customers"""
        # Get all active customers
        customers = await CustomerRepository.get_all_active()
        
        for customer in customers:
            await self.schedule_customer(customer)
            
        logger.info(f"Scheduled ingestion for {len(customers)} active customers")

    async def schedule_customer(self, customer: Dict[str, Any]):
        """Schedule ingestion for a single customer"""
        customer_id = customer['id']
        customer_code = customer['customer_code']
        method = customer['data_sharing_method']
        frequency = customer['data_frequency_seconds']
        
        if customer_id in self.running_tasks:
            logger.info(f"Rescheduling customer {customer_code}")
            self.running_tasks[customer_id].cancel()
            
        # Define the job function
        async def job():
            try:
                await self.ingest_customer_data(customer)
            except Exception as e:
                logger.error(f"Error ingesting data for customer {customer_code}: {e}", exc_info=True)
                
        # Schedule the job
        if method == 'api':
            # For API ingestion, use schedule library
            schedule.every(frequency).seconds.do(
                lambda: asyncio.create_task(job())
            )
        elif method == 'csv':
            # For CSV ingestion, use schedule library
            schedule.every(frequency).seconds.do(
                lambda: asyncio.create_task(job())
            )
        else:
            logger.warning(f"Unknown data sharing method for customer {customer_code}: {method}")
            return
            
        # Run immediately for the first time
        self.running_tasks[customer_id] = asyncio.create_task(job())
        
        logger.info(f"Scheduled {method} ingestion for customer {customer_code} every {frequency} seconds")

    async def ingest_customer_data(self, customer: Dict[str, Any]):
        """Ingest data for a single customer"""
        customer_id = customer['id']
        customer_code = customer['customer_code']
        method = customer['data_sharing_method']
        
        logger.info(f"Starting ingestion for customer {customer_code} via {method}")
        
        # Collect data based on method
        if method == 'api':
            readings, log_data = await self.api_collector.collect(customer)
            
            # Create ingestion log
            await IngestionLogRepository.create_log(log_data)
            
            # Process readings into events
            if readings:
                count = await self.processor.process_api_readings(customer_id, readings)
                logger.info(f"Processed {count} readings into events for customer {customer_code}")
                
        elif method == 'csv':
            readings, log_data = await self.csv_collector.collect(customer)
            
            # Create ingestion log
            await IngestionLogRepository.create_log(log_data)
            
            # Process readings into events
            if readings:
                count = await self.processor.process_csv_readings(customer_id, readings)
                logger.info(f"Processed {count} readings into events for customer {customer_code}")
                
        else:
            logger.warning(f"Unknown data sharing method for customer {customer_code}: {method}")