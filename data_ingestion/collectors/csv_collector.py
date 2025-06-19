import logging
import aiohttp
import asyncio
import csv
import os
import io
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from database.models.models import Customer, IngestionLog
from database.repositories.repositories import IngestionLogRepository

logger = logging.getLogger(__name__)


class CSVCollector:
    """Collector for CSV data sources"""

    def __init__(self, timeout: int = 30, download_dir: str = "data/imported"):
        self.timeout = timeout
        self.session = None
        self.download_dir = download_dir
        
        # Ensure download directory exists
        os.makedirs(self.download_dir, exist_ok=True)

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
        Collect data from customer CSV endpoint
        
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
            logger.error(f"No CSV URL configured for customer {customer_code}")
            log_data = {
                'customer_id': customer_id,
                'ingestion_type': 'csv',
                'status': 'failure',
                'records_processed': 0,
                'records_succeeded': 0,
                'records_failed': 0,
                'start_time': datetime.now(),
                'end_time': datetime.now(),
                'error_message': f"No CSV URL configured for customer {customer_code}",
                'source_url': api_url
            }
            return [], log_data
        
        # Initialize ingestion log
        log_data = {
            'customer_id': customer_id,
            'ingestion_type': 'csv',
            'status': 'pending',
            'records_processed': 0,
            'records_succeeded': 0,
            'records_failed': 0,
            'start_time': datetime.now(),
            'source_url': api_url
        }
        
        # Create a unique filename for this download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{customer_code}_{timestamp}.csv"
        filepath = os.path.join(self.download_dir, filename)
        
        try:
            logger.info(f"Downloading CSV for customer {customer_code} from: {api_url}")
            
            async with self.session.get(api_url) as response:
                if response.status != 200:
                    error_message = f"CSV download failed with status {response.status}: {await response.text()}"
                    logger.error(error_message)
                    
                    log_data.update({
                        'status': 'failure',
                        'end_time': datetime.now(),
                        'error_message': error_message
                    })
                    return [], log_data
                
                # Read the response content
                content = await response.read()
                
                # Save the file
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                # Parse the CSV
                readings = []
                failed_rows = 0
                
                # Process the CSV content
                csv_text = content.decode('utf-8-sig').splitlines()
                csv_reader = csv.DictReader(csv_text)
                
                for row in csv_reader:
                    try:
                        # Clean up row data (strip whitespace from keys and handle empty values)
                        cleaned_row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
                        readings.append(cleaned_row)
                    except Exception as e:
                        failed_rows += 1
                        logger.warning(f"Failed to parse CSV row: {e}")
                
                # Update log data
                log_data.update({
                    'status': 'success' if readings else 'warning',
                    'records_processed': len(readings) + failed_rows,
                    'records_succeeded': len(readings),
                    'records_failed': failed_rows,
                    'end_time': datetime.now(),
                    'error_message': None if readings else "CSV contained no valid readings"
                })
                
                logger.info(f"Successfully parsed {len(readings)} readings from CSV for {customer_code}")
                return readings, log_data
                
        except asyncio.TimeoutError:
            error_message = f"CSV download timed out after {self.timeout} seconds: {api_url}"
            logger.error(error_message)
            
            log_data.update({
                'status': 'failure',
                'end_time': datetime.now(),
                'error_message': error_message
            })
            return [], log_data
            
        except Exception as e:
            error_message = f"Error collecting data from CSV: {str(e)}"
            logger.error(error_message)
            
            log_data.update({
                'status': 'failure',
                'end_time': datetime.now(),
                'error_message': error_message
            })
            return [], log_data