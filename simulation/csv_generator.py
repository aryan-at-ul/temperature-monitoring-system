# simulation/csv_generator.py
import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from .enhanced_data_generator import generate_customer_data, TemperatureReading  # Changed to relative import
from .customer_generator import GeneratedCustomer  # Changed to relative import



class CSVGenerator:
    def __init__(self, output_dir: str = "data/csv_files"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_files = []
    
    def save_customer_csv(self, 
                         customer_id: str, 
                         readings: List[TemperatureReading], 
                         file_suffix: str = None) -> str:
        """Save temperature readings as CSV file"""
        
        if not readings:
            raise ValueError("No readings provided")
        
        # Convert readings to dictionary format
        data = []
        for reading in readings:
            row = reading.to_dict()
            # Handle CSV-specific formatting
            row = self._format_for_csv(row)
            data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Sort by timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Format timestamp for CSV
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if file_suffix is not None:
            filename = f"customer_{customer_id}_data_{file_suffix}_{timestamp}.csv"
        else:
            filename = f"customer_{customer_id}_data_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Save to CSV
        df.to_csv(filepath, index=False, na_rep='')
        
        self.generated_files.append(str(filepath))
        
        print(f"💾 Generated CSV: {filename}")
        print(f"   📊 Records: {len(df)}")
        print(f"   📁 Path: {filepath}")
        
        return filename
    
    def _format_for_csv(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Format row data for CSV output"""
        
        # Handle null values - convert None to empty string or specific null representation
        formatted_row = {}
        for key, value in row.items():
            if value is None:
                if key in ['unit_name', 'city']:
                    formatted_row[key] = ''  # Empty string for text fields
                elif key == 'temperature':
                    formatted_row[key] = None  # Keep None for numeric fields
                else:
                    formatted_row[key] = ''
            else:
                formatted_row[key] = value
        
        # Rename columns to match assignment requirements
        column_mapping = {
            'unit_name': 'storage_room',
            'temperature_unit': 'degrees'
        }
        
        for old_key, new_key in column_mapping.items():
            if old_key in formatted_row:
                formatted_row[new_key] = formatted_row.pop(old_key)
        
        return formatted_row
    
    def generate_daily_files(self, 
                           customer: GeneratedCustomer, 
                           days: int = 7) -> List[str]:
        """Generate multiple daily CSV files for a customer"""
        
        generated_files = []
        
        for day in range(days):
            # Calculate date range for this file
            end_time = datetime.now() - timedelta(days=day)
            start_time = end_time - timedelta(hours=24)
            
            print(f"📅 Generating day {day + 1}/{days}: {start_time.strftime('%Y-%m-%d')}")
            
            # Generate data for this day
            readings = generate_customer_data(customer, hours=24, start_time=start_time)
            
            if readings:
                date_str = start_time.strftime('%Y%m%d')
                filename = self.save_customer_csv(customer.id, readings, f"day_{date_str}")
                generated_files.append(filename)
            else:
                print(f"⚠️  No readings generated for day {day + 1}")
        
        return generated_files
    
    def generate_hourly_files(self, 
                            customer: GeneratedCustomer, 
                            hours: int = 24) -> List[str]:
        """Generate hourly CSV files (for testing frequent uploads)"""
        
        generated_files = []
        
        for hour in range(hours):
            # Calculate time range for this file
            end_time = datetime.now() - timedelta(hours=hour)
            start_time = end_time - timedelta(hours=1)
            
            print(f"🕐 Generating hour {hour + 1}/{hours}: {start_time.strftime('%H:00')}")
            
            # Generate data for this hour
            readings = generate_customer_data(customer, hours=1, start_time=start_time)
            
            if readings:
                hour_str = start_time.strftime('%Y%m%d_%H00')
                filename = self.save_customer_csv(customer.id, readings, f"hour_{hour_str}")
                generated_files.append(filename)
        
        return generated_files
    
    def simulate_csv_download_behavior(self, 
                                     customer: GeneratedCustomer, 
                                     simulation_hours: int = 48) -> List[str]:
        """Simulate realistic CSV download behavior for a customer"""
        
        if customer.data_sharing_method != 'csv':
            raise ValueError(f"Customer {customer.id} does not use CSV method")
        
        download_freq = customer.data_config.get('csv_download_frequency_hours', 24)
        update_freq = customer.data_config.get('csv_update_frequency_minutes', 5)
        
        print(f"📄 Simulating CSV downloads for {customer.name}")
        print(f"   📥 Download frequency: Every {download_freq} hours")
        print(f"   🔄 Data update frequency: Every {update_freq} minutes")
        
        generated_files = []
        downloads_count = simulation_hours // download_freq
        
        for download in range(downloads_count):
            # Calculate when this download would happen
            download_time = datetime.now() - timedelta(hours=download * download_freq)
            
            # Each download contains last 24 hours of data
            data_start = download_time - timedelta(hours=24)
            
            print(f"📥 Download {download + 1}/{downloads_count}: {download_time.strftime('%Y-%m-%d %H:%M')}")
            
            # Generate readings for this download period
            readings = generate_customer_data(
                customer, 
                hours=24, 
                start_time=data_start
            )
            
            if readings:
                download_str = download_time.strftime('%Y%m%d_%H%M')
                filename = self.save_customer_csv(
                    customer.id, 
                    readings, 
                    f"download_{download_str}"
                )
                generated_files.append(filename)
        
        return generated_files
    
    def export_summary(self, output_file: str = None) -> Dict[str, Any]:
        """Export summary of generated CSV files"""
        
        if not output_file:
            output_file = self.output_dir / "generation_summary.json"
        
        summary = {
            "generation_time": datetime.now().isoformat(),
            "output_directory": str(self.output_dir),
            "total_files": len(self.generated_files),
            "files": []
        }
        
        for filepath in self.generated_files:
            file_path = Path(filepath)
            if file_path.exists():
                # Get file stats
                stat = file_path.stat()
                
                # Read CSV to get record count
                try:
                    df = pd.read_csv(file_path)
                    record_count = len(df)
                    customers = df['customer_id'].unique().tolist() if 'customer_id' in df.columns else []
                except Exception as e:
                    record_count = 0
                    customers = []
                
                file_info = {
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "record_count": record_count,
                    "customers": customers
                }
                summary["files"].append(file_info)
        
        # Save summary
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📋 Summary exported to: {output_file}")
        
        return summary
    
    def cleanup_old_files(self, days_old: int = 7) -> int:
        """Clean up CSV files older than specified days"""
        
        cutoff_time = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        for file_path in self.output_dir.glob("*.csv"):
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if file_time < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                print(f"🗑️  Deleted old file: {file_path.name}")
        
        return deleted_count
    
    def get_generated_files(self) -> List[str]:
        """Get list of generated CSV files"""
        return self.generated_files.copy()