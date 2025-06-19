# api/utils/helpers.py
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def trigger_data_generation(customer_id: str, data_method: str) -> Dict[str, Any]:
    """Trigger data generation for a customer"""
    try:
        if data_method == 'csv':
            # Generate new CSV file
            cmd = f"python -m simulation.cli generate-csv --customer-id {customer_id} --hours 1 --files 1"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": f"CSV data generated for customer {customer_id}",
                    "method": "csv",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"CSV generation failed: {result.stderr}",
                    "method": "csv"
                }
        
        elif data_method == 'api':
            # Generate new JSON file
            cmd = f"python scripts/generate_api_data.py --customer {customer_id} --hours 1"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                return {
                    "status": "success", 
                    "message": f"API data generated for customer {customer_id}",
                    "method": "api",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"API generation failed: {result.stderr}",
                    "method": "api"
                }
        
        else:
            return {
                "status": "error",
                "message": f"Unsupported data method: {data_method}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Data generation failed: {str(e)}"
        }

def get_latest_data_files(customer_id: str) -> Dict[str, Any]:
    """Get latest data files for a customer"""
    data_info = {
        "csv_files": [],
        "json_files": [],
        "latest_csv": None,
        "latest_json": None
    }
    
    # Check CSV files
    csv_pattern = f"customer_{customer_id}_*.csv"
    for csv_dir in ["data/csv_files", "data/assignment/csv_files"]:
        if os.path.exists(csv_dir):
            csv_files = list(Path(csv_dir).glob(csv_pattern))
            data_info["csv_files"].extend([str(f) for f in csv_files])
    
    # Check JSON files  
    json_pattern = f"customer_{customer_id}_*.json"
    for json_dir in ["data/generated", "data/assignment"]:
        if os.path.exists(json_dir):
            json_files = list(Path(json_dir).glob(json_pattern))
            data_info["json_files"].extend([str(f) for f in json_files])
    
    # Get latest files
    if data_info["csv_files"]:
        data_info["latest_csv"] = max(data_info["csv_files"], key=os.path.getmtime)
    
    if data_info["json_files"]:
        data_info["latest_json"] = max(data_info["json_files"], key=os.path.getmtime)
    
    return data_info