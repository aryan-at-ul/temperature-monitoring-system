#!/usr/bin/env python3
# dashboard/utils.py

import os
import requests
from flask import session, redirect, url_for, flash
from functools import wraps

# API Configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token' not in session or session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# old only for cusotmer not admin
# def make_api_request(endpoint, method="GET", params=None, data=None):
#     """Make an API request with the stored token"""
#     headers = {}
#     if 'token' in session:
#         headers['Authorization'] = f"Bearer {session['token']}"
    
#     url = f"{API_BASE_URL}{endpoint}"
    
#     try:
#         if method == "GET":
#             response = requests.get(url, headers=headers, params=params)
#         elif method == "POST":
#             response = requests.post(url, headers=headers, json=data)
#         elif method == "PUT":
#             response = requests.put(url, headers=headers, json=data)
#         elif method == "DELETE":
#             response = requests.delete(url, headers=headers)
        
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         if hasattr(e, 'response') and e.response:
#             if hasattr(e.response, 'json'):
#                 try:
#                     return e.response.json(), e.response.status_code
#                 except:
#                     return {"error": str(e)}, getattr(e.response, 'status_code', 500)
#         return {"error": str(e)}, 500

def make_api_request(endpoint, method="GET", params=None, data=None):
    """Make an API request with the stored token"""
    headers = {}
    if 'token' in session:
        headers['Authorization'] = f"Bearer {session['token']}"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        # If response status is 401 or 403, session might be invalid
        if response.status_code in [401, 403]:
            print(f"Authentication error: {response.status_code} - {url}")
            # Check if we're in a customer-specific route
            if session.get('role') == 'customer':
                # Session might be expired, redirect to login
                return {"error": "Authentication failed. Please log in again."}, response.status_code
        
        # If response status is 404, the endpoint doesn't exist
        if response.status_code == 404:
            print(f"Endpoint not found: {url}")
            return {"error": f"Endpoint not found: {endpoint}"}, response.status_code
        
        # Try to parse JSON response
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            # Not a JSON response
            return response.text
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            if hasattr(e.response, 'json'):
                try:
                    return e.response.json(), getattr(e.response, 'status_code', 500)
                except:
                    return {"error": str(e)}, getattr(e.response, 'status_code', 500)
        return {"error": str(e)}, 500