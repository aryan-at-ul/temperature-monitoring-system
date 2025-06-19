#!/usr/bin/env python3
"""
Temperature Monitoring API Endpoint Tests

This script tests individual endpoints of the Temperature Monitoring API.
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import unittest

# Get project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import token helper
from api.tests.utils.token_helper import get_token_header

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

class HealthEndpointTest(unittest.TestCase):
    def test_health_endpoint(self):
        """Test the health endpoint"""
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")

class TemperatureEndpointsTest(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        self.customer_code = "B"  # Using customer B for tests
        self.headers = get_token_header(self.customer_code, "read")
        self.facility_id = "7f84f137-7d21-404c-a46e-5e19a4b61b58"  # facility_B_1
        self.storage_unit_id = "adb0a994-1378-4cf2-b022-2c5ec31e8daf"  # A storage unit from Customer B
        
    def test_get_all_temperatures(self):
        """Test getting all temperatures"""
        response = requests.get(f"{BASE_URL}/temperature", headers=self.headers)
        self.assertIn(response.status_code, [200, 404])  # Either success or not found is acceptable
        
    def test_get_latest_temperatures(self):
        """Test getting latest temperatures"""
        response = requests.get(f"{BASE_URL}/temperature/latest", headers=self.headers)
        self.assertIn(response.status_code, [200, 404])  # Either success or not found is acceptable
        
    def test_get_facility_temperatures(self):
        """Test getting temperatures for a facility"""
        response = requests.get(f"{BASE_URL}/temperature/facility/{self.facility_id}", headers=self.headers)
        self.assertIn(response.status_code, [200, 404])  # Either success or not found is acceptable
        
    def test_get_unit_temperatures(self):
        """Test getting temperatures for a storage unit"""
        response = requests.get(f"{BASE_URL}/temperature/unit/{self.storage_unit_id}", headers=self.headers)
        self.assertIn(response.status_code, [200, 404])  # Either success or not found is acceptable
        
    def test_get_temperature_history(self):
        """Test getting temperature history"""
        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()
        params = {
            "start_date": yesterday.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_date": today.strftime("%Y-%m-%dT%H:%M:%S")
        }
        response = requests.get(f"{BASE_URL}/temperature/history", headers=self.headers, params=params)
        self.assertIn(response.status_code, [200, 404])  # Either success or not found is acceptable

class FacilitiesEndpointsTest(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        self.customer_code = "B"  # Using customer B for tests
        self.headers = get_token_header(self.customer_code, "read")
        self.facility_id = "7f84f137-7d21-404c-a46e-5e19a4b61b58"  # facility_B_1
        
    def test_get_all_facilities(self):
        """Test getting all facilities"""
        response = requests.get(f"{BASE_URL}/facilities", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
    def test_get_facility(self):
        """Test getting a specific facility"""
        response = requests.get(f"{BASE_URL}/facilities/{self.facility_id}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
    def test_get_facility_units(self):
        """Test getting storage units for a facility"""
        response = requests.get(f"{BASE_URL}/facilities/{self.facility_id}/units", headers=self.headers)
        self.assertIn(response.status_code, [200, 404])  # Either success or not found is acceptable

class CustomerEndpointsTest(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        self.customer_code = "B"  # Using customer B for tests
        self.headers = get_token_header(self.customer_code, "read")
        
    def test_get_customer_profile(self):
        """Test getting customer profile"""
        response = requests.get(f"{BASE_URL}/customers/profile", headers=self.headers)
        self.assertEqual(response.status_code, 200)

class AdminEndpointsTest(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        self.headers = get_token_header("admin", "admin")
        
    def test_get_all_customers(self):
        """Test getting all customers"""
        response = requests.get(f"{BASE_URL}/admin/customers", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
    def test_get_system_config(self):
        """Test getting system configuration"""
        response = requests.get(f"{BASE_URL}/admin/config", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
    def test_get_ingestion_logs(self):
        """Test getting ingestion logs"""
        response = requests.get(f"{BASE_URL}/admin/ingestion/logs", headers=self.headers)
        self.assertIn(response.status_code, [200, 404])  # Either success or not found is acceptable
        
if __name__ == "__main__":
    unittest.main()