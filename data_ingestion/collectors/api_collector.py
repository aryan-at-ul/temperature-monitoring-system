import logging
import aiohttp
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from database.models.models import Customer, IngestionLog
from database.repositories.repositories import IngestionLogRepository

logger = logging.getLogger(__name__)


class APICollector:
    """Collector for API data sources"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = None

    async def initialize(self):
        """Initialize HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def collect(self, customer: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Collect data from customer API
        
        Args:
            customer: Customer data including API URL
            
        Returns:
            Tuple containing (list of readings, ingestion log data)
        """
        await self.initialize()
        
        customer_id = customer['id']
        customer_code = customer['customer_code']
        api_url = customer.get('api_url')
        
        if not api_url:
            logger.error(f"No API URL configured for customer {customer_code}")
            log_data = {
                'customer_id': customer_id,
                'ingestion_type': 'api',
                'status': 'failure',
                'records_processed': 0,
                'records_succeeded': 0,
                'records_failed': 0,
                'start_time': datetime.now(),
                'end_time': datetime.now(),
                'error_message': f"No API URL configured for customer {customer_code}",
                'source_url': api_url
            }
            return [], log_data
        
        # Initialize ingestion log
        log_data = {
            'customer_id': customer_id,
            'ingestion_type': 'api',
            'status': 'pending',
            'records_processed': 0,
            'records_succeeded': 0,
            'records_failed': 0,
            'start_time': datetime.now(),
            'source_url': api_url
        }
        
        try:
            logger.info(f"Collecting data from API for customer {customer_code}: {api_url}")
            
            async with self.session.get(api_url) as response:
                if response.status != 200:
                    error_message = f"API request failed with status {response.status}: {await response.text()}"
                    logger.error(error_message)
                    
                    log_data.update({
                        'status': 'failure',
                        'end_time': datetime.now(),
                        'error_message': error_message
                    })
                    return [], log_data
                
                data = await response.json()
                
                # Extract readings
                readings = data.get('readings', [])
                
                # Update log data
                log_data.update({
                    'status': 'success' if readings else 'warning',
                    'records_processed': len(readings),
                    'records_succeeded': len(readings),
                    'end_time': datetime.now(),
                    'error_message': None if readings else "API returned no readings"
                })
                
                logger.info(f"Successfully collected {len(readings)} readings from {customer_code}")
                return readings, log_data
                
        except asyncio.TimeoutError:
            error_message = f"API request timed out after {self.timeout} seconds: {api_url}"
            logger.error(error_message)
            
            log_data.update({
                'status': 'failure',
                'end_time': datetime.now(),
                'error_message': error_message
            })
            return [], log_data
            
        except Exception as e:
            error_message = f"Error collecting data from API: {str(e)}"
            logger.error(error_message)
            
            log_data.update({
                'status': 'failure',
                'end_time': datetime.now(),
                'error_message': error_message
            })
            return [], log_data