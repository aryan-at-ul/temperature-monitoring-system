#!/usr/bin/env python3
# api/tests/test_all_endpoints.py

import requests
import json
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_endpoints(token, customer_code):
    """Test all endpoints with the given token"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Testing endpoints for customer {customer_code} with token: {token[:10]}...")
    
    # 1. Health endpoint (no auth required)
    test_endpoint(f"{BASE_URL}/health", "GET")
    
    # 2. Customer endpoints
    api_v1 = f"{BASE_URL}/api/v1"
    
    # Temperature endpoints
    print("\n=== Testing Temperature Endpoints ===")
    test_endpoint(f"{api_v1}/temperature", "GET", headers)
    test_endpoint(f"{api_v1}/temperature/latest", "GET", headers)
    
    # Facility endpoints
    print("\n=== Testing Facility Endpoints ===")
    test_endpoint(f"{api_v1}/facilities", "GET", headers)
    
    # If we have a facility ID from the facilities endpoint, test more endpoints
    facilities_response = requests.get(f"{api_v1}/facilities", headers=headers)
    if facilities_response.status_code == 200:
        facilities = facilities_response.json()
        if isinstance(facilities, dict) and "items" in facilities:
            facilities = facilities["items"]
        
        if facilities and len(facilities) > 0:
            facility_id = facilities[0].get("id")
            if facility_id:
                print(f"\nFound facility ID: {facility_id}, testing more endpoints...")
                test_endpoint(f"{api_v1}/facilities/{facility_id}", "GET", headers)
                test_endpoint(f"{api_v1}/facilities/{facility_id}/units", "GET", headers)
                test_endpoint(f"{api_v1}/temperature/facility/{facility_id}", "GET", headers)
                
                # If we have a storage unit ID, test unit endpoints
                units_response = requests.get(f"{api_v1}/facilities/{facility_id}/units", headers=headers)
                if units_response.status_code == 200:
                    units = units_response.json()
                    if isinstance(units, dict) and "items" in units:
                        units = units["items"]
                    
                    if units and len(units) > 0:
                        unit_id = units[0].get("id")
                        if unit_id:
                            print(f"\nFound unit ID: {unit_id}, testing more endpoints...")
                            test_endpoint(f"{api_v1}/temperature/unit/{unit_id}", "GET", headers)
    
    # Customer endpoints
    print("\n=== Testing Customer Endpoints ===")
    test_endpoint(f"{api_v1}/customers/profile", "GET", headers)
    
    # Analytics endpoints
    print("\n=== Testing Analytics Endpoints ===")
    test_endpoint(f"{api_v1}/analytics/temperature/summary", "GET", headers)
    
    # Admin endpoints (will likely fail for non-admin tokens)
    if "admin" in token:
        print("\n=== Testing Admin Endpoints ===")
        test_endpoint(f"{api_v1}/admin/customers", "GET", headers)
        test_endpoint(f"{api_v1}/admin/config", "GET", headers)
        test_endpoint(f"{api_v1}/admin/facilities", "GET", headers)

def test_endpoint(url, method="GET", headers=None, data=None):
    """Test an API endpoint and print the response"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return
        
        status_emoji = "✅" if response.status_code < 400 else "❌"
        print(f"{status_emoji} {method} {url}: {response.status_code}")
        
        if response.status_code < 400:
            try:
                # Pretty print the first few items of the response
                resp_json = response.json()
                if isinstance(resp_json, dict) and "items" in resp_json and isinstance(resp_json["items"], list):
                    items = resp_json["items"]
                    print(f"  Found {len(items)} items")
                    if len(items) > 0:
                        print(f"  First item: {json.dumps(items[0], indent=2)[:200]}...")
                elif isinstance(resp_json, list):
                    print(f"  Found {len(resp_json)} items")
                    if len(resp_json) > 0:
                        print(f"  First item: {json.dumps(resp_json[0], indent=2)[:200]}...")
                else:
                    print(f"  Response: {json.dumps(resp_json, indent=2)[:200]}...")
            except:
                if len(response.text) > 0:
                    print(f"  Response: {response.text[:200]}...")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def main():
    # Use the tokens from your api_tokens.json file
    try:
        with open(project_root / "api_tokens.json", "r") as f:
            tokens = json.load(f)
    except:
        print("Failed to load api_tokens.json, using hardcoded tokens")
        tokens = {
            "B": {
                "read_token": "read_B_66_token_2025",
                "write_token": "write_B_66_token_2025"
            },
            "admin": {
                "admin_token": "admin_A_65_admin_token_2025"
            }
        }
    
    # Get customer code from command line
    customer_code = sys.argv[1] if len(sys.argv) > 1 else "B"
    token_type = sys.argv[2] if len(sys.argv) > 2 else "read"
    
    if customer_code == "admin":
        token = tokens.get("admin", {}).get("admin_token")
    else:
        token = tokens.get(customer_code, {}).get(f"{token_type}_token")
    
    if not token:
        print(f"No {token_type} token found for customer {customer_code}")
        sys.exit(1)
    
    test_endpoints(token, customer_code)

if __name__ == "__main__":
    main()