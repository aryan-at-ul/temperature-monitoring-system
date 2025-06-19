#!/usr/bin/env python3
"""
Run all API tests for the Temperature Monitoring System

This script runs all the API tests in the test directory.
"""

import unittest
import sys
import os
from pathlib import Path
import argparse

# Get project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_endpoint_tests():
    """Run all endpoint tests"""
    print("Running endpoint tests...")
    
    # Discover and run all tests in the endpoint_tests directory
    test_dir = Path(__file__).parent / "endpoint_tests"
    test_suite = unittest.defaultTestLoader.discover(test_dir)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Run all integration tests"""
    print("Running integration tests...")
    
    # Discover and run all tests in the integration_tests directory
    test_dir = Path(__file__).parent / "integration_tests"
    test_suite = unittest.defaultTestLoader.discover(test_dir)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result.wasSuccessful()

def run_performance_tests():
    """Run all performance tests"""
    print("Running performance tests...")
    
    # Discover and run all tests in the performance_tests directory
    test_dir = Path(__file__).parent / "performance_tests"
    test_suite = unittest.defaultTestLoader.discover(test_dir)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result.wasSuccessful()

def run_all_tests():
    """Run all tests"""
    print("Running all tests...")
    
    endpoint_success = run_endpoint_tests()
    integration_success = run_integration_tests()
    performance_success = run_performance_tests()
    
    return endpoint_success and integration_success and performance_success

def main():
    parser = argparse.ArgumentParser(description="Run API tests for Temperature Monitoring System")
    parser.add_argument("--endpoint", action="store_true", help="Run endpoint tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    # If no arguments are provided, run all tests
    if not any(vars(args).values()):
        args.all = True
    
    success = True
    
    if args.endpoint:
        success = run_endpoint_tests() and success
    
    if args.integration:
        success = run_integration_tests() and success
    
    if args.performance:
        success = run_performance_tests() and success
    
    if args.all:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
