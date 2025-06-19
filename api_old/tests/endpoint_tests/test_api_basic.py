#!/usr/bin/env python3
"""
Basic Temperature Monitoring API Test Script

This script tests the basic endpoints of the Temperature Monitoring API.

Usage:
    python test_api_basic.py [customer_code] [token_type]

    customer_code: Customer code to use (A, B, C, etc.)
    token_type: Token type to use (read, write, admin)
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import token helper
from api.tests.utils.token_helper import get_token_header

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(endpoint, headers, method="GET", data=None, params=None):
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}/{endpoint}"
    
    print(f"\n===== Testing {method} {url} =====")
    
    if params:
        print(f"Params: {json.dumps(params, indent=2)}")
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return None
        
        print(f"Status code: {response.status_code}")
        
        try:
            resp_data = response.json()
            print(f"Response: {json.dumps(resp_data, indent=2)}")
            return resp_data
        except:
            print(f"Response: {response.text}")
            return response.text
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_health():
    """Test the health endpoint"""
    url = f"{BASE_URL.replace('/api/v1', '')}/health"
    print(f"\n===== Testing GET {url} =====")
    
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        
        try:
            resp_data = response.json()
            print(f"Response: {json.dumps(resp_data, indent=2)}")
            return resp_data
        except:
            print(f"Response: {response.text}")
            return response.text
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    # Default to customer B with read token if no arguments provided
    customer_code = sys.argv[1] if len(sys.argv) > 1 else "B"
    token_type = sys.argv[2] if len(sys.argv) > 2 else "read"
    
    print(f"Testing API with customer {customer_code} and {token_type} token")
    
    # Get headers for API calls
    headers = get_token_header(customer_code, token_type)
    
    # Test health endpoint (no auth required)
    test_health()
    
    # Test basic endpoints
    test_endpoint("temperature", headers)
    test_endpoint("temperature/latest", headers)
    
    if customer_code == "B":
        # Test with known facility ID for customer B
        facility_id = "7f84f137-7d21-404c-a46e-5e19a4b61b58"  # facility_B_1
        test_endpoint(f"temperature/facility/{facility_id}", headers)
        
        # Test with known storage unit ID for customer B
        unit_id = "adb0a994-1378-4cf2-b022-2c5ec31e8daf"
        test_endpoint(f"temperature/unit/{unit_id}", headers)
    
    # Test facilities endpoint
    test_endpoint("facilities", headers)
    
    # Test customer profile endpoint
    test_endpoint("customers/profile", headers)
    
    # Test analytics endpoint
    test_endpoint("analytics/temperature/summary", headers)
    
    # Test admin endpoints if using admin token
    if token_type == "admin":
        test_endpoint("admin/customers", headers)
        test_endpoint("admin/config", headers)
        test_endpoint("admin/ingestion/logs", headers)

if __name__ == "__main__":
    main()