#!/usr/bin/env python3
# api/tests/test_all_endpoints.py

import requests
import json
import sys
import os
import time
from pathlib import Path
import argparse
from datetime import datetime, timedelta
from uuid import UUID

# Get project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"

def load_tokens():
    """Load tokens from api_tokens.json file"""
    try:
        # Try to load from project root
        token_path = project_root / "api_tokens.json"
        if token_path.exists():
            with open(token_path, "r") as f:
                return json.load(f)
        
        # Hardcoded tokens as fallback
        return {
            "A": {
                "read_token": "read_A_65_token_2025",
                "write_token": "write_A_65_token_2025"
            },
            "B": {
                "read_token": "read_B_66_token_2025",
                "write_token": "write_B_66_token_2025"
            },
            "C": {
                "read_token": "read_C_67_token_2025",
                "write_token": "write_C_67_token_2025"
            },
            "D": {
                "read_token": "read_D_68_token_2025",
                "write_token": "write_D_68_token_2025"
            },
            "E": {
                "read_token": "read_E_69_token_2025",
                "write_token": "write_E_69_token_2025"
            },
            "admin": {
                "admin_token": "admin_A_65_admin_token_2025"
            }
        }
    except Exception as e:
        print(f"Error loading tokens: {e}")
        sys.exit(1)

def get_token(customer_code, token_type="read"):
    """Get a token for the specified customer and token type"""
    tokens = load_tokens()
    
    if customer_code == "admin":
        return tokens.get("admin", {}).get("admin_token")
    else:
        return tokens.get(customer_code, {}).get(f"{token_type}_token")

def test_endpoint(url, method="GET", headers=None, params=None, data=None, expected_status=None):
    """Test an API endpoint and print the result"""
    full_url = url if url.startswith("http") else f"{BASE_URL}{url}"
    
    print(f"\n===== Testing {method} {full_url} =====")
    if headers:
        print(f"Headers: {headers.get('Authorization', 'No Auth')}")
    if params:
        print(f"Params: {params}")
    if data:
        print(f"Data: {json.dumps(data, default=str, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(full_url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(full_url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(full_url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(full_url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return None
        
        status_code = response.status_code
        status_emoji = "✅" if expected_status is None or status_code == expected_status else "❌"
        print(f"{status_emoji} Status code: {status_code}")
        
        try:
            resp_data = response.json()
            print(f"Response: {json.dumps(resp_data, default=str, indent=2)[:500]}...")
            if len(json.dumps(resp_data, default=str)) > 500:
                print("(response truncated)")
            return resp_data
        except:
            print(f"Response: {response.text[:500]}")
            if len(response.text) > 500:
                print("(response truncated)")
            return response.text
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_health_endpoint():
    """Test the health endpoint"""
    print("\n\n====== TESTING HEALTH ENDPOINTS ======")
    
    # Test health endpoint
    health_response = test_endpoint(HEALTH_URL, "GET")
    
    # Test ping endpoint
    test_endpoint("http://localhost:8000/ping", "GET")

def test_temperature_endpoints(customer_code="B", token_type="read"):
    """Test temperature endpoints"""
    print(f"\n\n====== TESTING TEMPERATURE ENDPOINTS FOR {customer_code} ({token_type}) ======")
    
    token = get_token(customer_code, token_type)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get all temperature readings
    readings = test_endpoint("/temperature", "GET", headers)
    
    # Test get latest temperature readings
    test_endpoint("/temperature/latest", "GET", headers)
    
    # Get sample facility_id and unit_id
    facility_id = None
    unit_id = None
    
    # Test get facilities to find a facility_id
    facilities = test_endpoint("/facilities", "GET", headers)
    if facilities and "items" in facilities and len(facilities["items"]) > 0:
        facility_id = facilities["items"][0]["id"]
        print(f"Found facility_id: {facility_id}")
        
        # Test get temperature readings for a facility
        test_endpoint(f"/temperature/facility/{facility_id}", "GET", headers)
        
        # Test get storage units to find a unit_id
        units = test_endpoint(f"/facilities/{facility_id}/units", "GET", headers)
        if units and "items" in units and len(units["items"]) > 0:
            unit_id = units["items"][0]["id"]
            print(f"Found unit_id: {unit_id}")
            
            # Test get temperature readings for a storage unit
            test_endpoint(f"/temperature/unit/{unit_id}", "GET", headers)
    
    # Test get temperature statistics
    test_endpoint("/temperature/stats", "GET", headers)
    
    # Test get temperature statistics with date range
    yesterday = datetime.now() - timedelta(days=1)
    params = {
        "start_date": yesterday.isoformat(),
        "end_date": datetime.now().isoformat()
    }
    test_endpoint("/temperature/stats", "GET", headers, params)
    
    # Test temperature aggregation (if write token)
    if token_type == "write" and unit_id:
        # Test create temperature reading
        reading_data = {
            "storage_unit_id": unit_id,
            "temperature": -18.5,
            "temperature_unit": "C",
            "recorded_at": datetime.now().isoformat(),
            "sensor_id": f"test_sensor_{int(time.time())}",
            "quality_score": 1,
            "equipment_status": "normal"
        }
        test_endpoint("/temperature", "POST", headers, data=reading_data, expected_status=201)
    
    # Test temperature aggregation
    aggregation_data = {
        "group_by": ["day", "facility"],
        "aggregations": ["avg", "min", "max", "count"],
        "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_date": datetime.now().isoformat()
    }
    if facility_id:
        aggregation_data["facility_id"] = facility_id
    test_endpoint("/temperature/aggregate", "POST", headers, data=aggregation_data)

def test_facilities_endpoints(customer_code="B", token_type="read"):
    """Test facilities endpoints"""
    print(f"\n\n====== TESTING FACILITIES ENDPOINTS FOR {customer_code} ({token_type}) ======")
    
    token = get_token(customer_code, token_type)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get all facilities
    facilities = test_endpoint("/facilities", "GET", headers)
    
    facility_id = None
    if facilities and "items" in facilities and len(facilities["items"]) > 0:
        facility_id = facilities["items"][0]["id"]
        print(f"Found facility_id: {facility_id}")
        
        # Test get facility
        test_endpoint(f"/facilities/{facility_id}", "GET", headers)
        
        # Test get facility with units
        test_endpoint(f"/facilities/{facility_id}/detailed", "GET", headers)
        
        # Test get storage units for a facility
        units = test_endpoint(f"/facilities/{facility_id}/units", "GET", headers)
        
        unit_id = None
        if units and "items" in units and len(units["items"]) > 0:
            unit_id = units["items"][0]["id"]
            print(f"Found unit_id: {unit_id}")
            
            # Test get storage unit
            test_endpoint(f"/units/{unit_id}", "GET", headers)
    
    # Test create facility (if write token)
    if token_type == "write":
        # Create facility
        facility_data = {
            "facility_code": f"test_facility_{int(time.time())}",
            "name": "Test Facility",
            "city": "Test City",
            "country": "Test Country"
        }
        new_facility = test_endpoint("/facilities", "POST", headers, data=facility_data, expected_status=201)
        
        if new_facility and "id" in new_facility:
            new_facility_id = new_facility["id"]
            print(f"Created new facility with ID: {new_facility_id}")
            
            # Update facility
            update_data = {
                "name": f"Updated Test Facility {int(time.time())}"
            }
            test_endpoint(f"/facilities/{new_facility_id}", "PUT", headers, data=update_data)
            
            # Create storage unit
            unit_data = {
                "unit_code": f"test_unit_{int(time.time())}",
                "name": "Test Storage Unit",
                "size_value": 1000,
                "size_unit": "sqft",
                "set_temperature": -18.0,
                "temperature_unit": "C",
                "equipment_type": "freezer"
            }
            new_unit = test_endpoint(f"/facilities/{new_facility_id}/units", "POST", headers, data=unit_data, expected_status=201)
            
            if new_unit and "id" in new_unit:
                new_unit_id = new_unit["id"]
                print(f"Created new storage unit with ID: {new_unit_id}")
                
                # Update storage unit
                update_unit_data = {
                    "name": f"Updated Test Unit {int(time.time())}"
                }
                test_endpoint(f"/units/{new_unit_id}", "PUT", headers, data=update_unit_data)

def test_customer_endpoints(customer_code="B", token_type="read"):
    """Test customer endpoints"""
    print(f"\n\n====== TESTING CUSTOMER ENDPOINTS FOR {customer_code} ({token_type}) ======")
    
    token = get_token(customer_code, token_type)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get customer profile
    test_endpoint("/customers/profile", "GET", headers)
    
    # Test get customer tokens
    tokens = test_endpoint("/customers/tokens", "GET", headers)
    
    # Test create and revoke token (if write token)
    if token_type == "write":
        # Create token
        token_data = {
            "token_name": f"Test Token {int(time.time())}",
            "permissions": ["read"],
            "rate_limit_per_hour": 100
        }
        new_token = test_endpoint("/customers/tokens", "POST", headers, data=token_data, expected_status=201)
        
        if new_token and "id" in new_token:
            token_id = new_token["id"]
            print(f"Created new token with ID: {token_id}")
            
            # Revoke token
            test_endpoint(f"/customers/tokens/{token_id}", "DELETE", headers)
        
        # Update customer profile
        update_data = {
            "name": f"Updated Test Customer {int(time.time())}"
        }
        test_endpoint("/customers/profile", "PUT", headers, data=update_data)

def test_analytics_endpoints(customer_code="B", token_type="read"):
    """Test analytics endpoints"""
    print(f"\n\n====== TESTING ANALYTICS ENDPOINTS FOR {customer_code} ({token_type}) ======")
    
    token = get_token(customer_code, token_type)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get temperature summary
    test_endpoint("/analytics/temperature/summary", "GET", headers)
    
    # Test get temperature trends
    params = {
        "interval": "day",
        "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_date": datetime.now().isoformat()
    }
    test_endpoint("/analytics/temperature/trends", "GET", headers, params)
    
    # Test get alarm history
    test_endpoint("/analytics/alarms/history", "GET", headers)
    
    # Test get performance metrics
    test_endpoint("/analytics/performance", "GET", headers)

def test_admin_endpoints():
    """Test admin endpoints"""
    print("\n\n====== TESTING ADMIN ENDPOINTS ======")
    
    token = get_token("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get all customers
    customers = test_endpoint("/admin/customers", "GET", headers)
    
    customer_id = None
    if customers and "items" in customers and len(customers["items"]) > 0:
        customer_id = customers["items"][0]["id"]
        print(f"Found customer_id: {customer_id}")
        
        # Test get customer
        test_endpoint(f"/admin/customers/{customer_id}", "GET", headers)
        
        # Test get customer tokens
        test_endpoint(f"/admin/customers/{customer_id}/tokens", "GET", headers)
        
        # Test create customer token
        token_data = {
            "token_name": f"Admin Created Token {int(time.time())}",
            "permissions": ["read"],
            "rate_limit_per_hour": 100
        }
        test_endpoint(f"/admin/customers/{customer_id}/tokens", "POST", headers, data=token_data, expected_status=201)
        
        # Test update customer
        update_data = {
            "name": f"Admin Updated Customer {int(time.time())}"
        }
        test_endpoint(f"/admin/customers/{customer_id}", "PUT", headers, data=update_data)
    
    # Test get all facilities
    facilities = test_endpoint("/admin/facilities", "GET", headers)
    
    # Test get system configuration
    test_endpoint("/admin/config", "GET", headers)
    
    # Test update system configuration
    config_data = {
        "value": 2555,
        "description": "Number of days to retain temperature data"
    }
    test_endpoint("/admin/config/data_retention_days", "PUT", headers, data=config_data)
    
    # Test get ingestion logs
    test_endpoint("/admin/ingestion/logs", "GET", headers)
    
    # Test get temperature summary
    test_endpoint("/admin/analytics/temperature/summary", "GET", headers)

def test_admin_temperature_endpoints():
    """Test admin temperature endpoints"""
    print("\n\n====== TESTING ADMIN TEMPERATURE ENDPOINTS ======")
    
    token = get_token("admin", "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get all temperature readings
    test_endpoint("/admin/temperature", "GET", headers)
    
    # Get a facility ID
    facilities = test_endpoint("/admin/facilities", "GET", headers)
    
    if facilities and "items" in facilities and len(facilities["items"]) > 0:
        facility_id = facilities["items"][0]["id"]
        print(f"Found facility_id: {facility_id}")
        
        # Test get temperature readings for a facility
        test_endpoint(f"/admin/temperature/facility/{facility_id}", "GET", headers)

def run_all_tests(customer_code="B", token_type="read", admin=False, all_tests=False):
    """Run all tests"""
    print("\n\n======= RUNNING API ENDPOINT TESTS =======")
    print(f"Customer: {customer_code}, Token Type: {token_type}")
    print(f"Admin: {admin}, All Tests: {all_tests}")
    
    # Start timer
    start_time = time.time()
    
    # Test health endpoint
    test_health_endpoint()
    
    # Test customer endpoints
    if all_tests:
        # Test with multiple customers
        for code in ["A", "B", "C"]:
            test_temperature_endpoints(code, token_type)
            test_facilities_endpoints(code, token_type)
            test_customer_endpoints(code, token_type)
            test_analytics_endpoints(code, token_type)
    else:
        # Test with specific customer
        test_temperature_endpoints(customer_code, token_type)
        test_facilities_endpoints(customer_code, token_type)
        test_customer_endpoints(customer_code, token_type)
        test_analytics_endpoints(customer_code, token_type)
    
    # Test admin endpoints
    if admin or all_tests:
        test_admin_endpoints()
        test_admin_temperature_endpoints()
    
    # Calculate and print elapsed time
    elapsed_time = time.time() - start_time
    print(f"\n\n======= TESTS COMPLETED IN {elapsed_time:.2f} SECONDS =======")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test all API endpoints")
    parser.add_argument("--customer", default="B", help="Customer code to use (default: B)")
    parser.add_argument("--token-type", default="read", choices=["read", "write"], help="Token type to use (default: read)")
    parser.add_argument("--admin", action="store_true", help="Run admin tests")
    parser.add_argument("--all", action="store_true", help="Run tests for multiple customers")
    
    args = parser.parse_args()
    
    run_all_tests(args.customer, args.token_type, args.admin, args.all)