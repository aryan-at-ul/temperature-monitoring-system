#!/usr/bin/env python3


import os
import requests
from flask import session, redirect, url_for, flash
from functools import wraps


API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')


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
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            if hasattr(e.response, 'json'):
                try:
                    return e.response.json(), e.response.status_code
                except:
                    return {"error": str(e)}, getattr(e.response, 'status_code', 500)
        return {"error": str(e)}, 500