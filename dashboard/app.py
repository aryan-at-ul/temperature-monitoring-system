#!/usr/bin/env python3


from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
import requests
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')


API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
HEALTH_URL = os.environ.get('HEALTH_URL', 'http://localhost:8000/health')


from utils import make_api_request, login_required, admin_required


from routes.common import common_bp
from routes.customer import customer_bp
from routes.admin import admin_bp


app.register_blueprint(common_bp)
app.register_blueprint(customer_bp, url_prefix='/customer')
app.register_blueprint(admin_bp, url_prefix='/admin')


@app.route('/')
def index():
    if 'token' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))
    return redirect(url_for('login'))

# Replace your existing login route in app.py

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        customer_code = request.form.get('customer_code')
        token_type = request.form.get('token_type', 'read')
        
        # Add debug logging
        print(f"Login attempt: customer_code={customer_code}, token_type={token_type}")
        
        # Check if admin login
        if customer_code == 'admin':
            admin_token = request.form.get('token')
            # Test the admin token
            headers = {"Authorization": f"Bearer {admin_token}"}
            try:
                print(f"Testing admin token: {admin_token[:5]}...")
                response = requests.get(f"{API_BASE_URL}/admin/customers", headers=headers)
                print(f"Admin API response: {response.status_code}")
                if response.status_code == 200:
                    session['token'] = admin_token
                    session['role'] = 'admin'
                    session['customer_code'] = 'admin'
                    flash('Admin login successful', 'success')
                    return redirect(url_for('admin.dashboard'))
                else:
                    flash('Invalid admin token', 'danger')
            except requests.exceptions.RequestException as e:
                print(f"API request error: {str(e)}")
                flash('API service unavailable', 'danger')
        else:
            # Customer login
            token = request.form.get('token')
            
            headers = {"Authorization": f"Bearer {token}"}
            try:
                print(f"Testing customer token with facilities endpoint: {token[:5]}...")
                response = requests.get(f"{API_BASE_URL}/facilities", headers=headers)
                print(f"Customer API facilities response: {response.status_code}")
                
                if response.status_code == 200:
                    session['token'] = token
                    session['role'] = 'customer'
                    session['customer_code'] = customer_code
                    flash('Login successful', 'success')
                    return redirect(url_for('customer.dashboard'))
                else:
                    # Try temperature endpoint as a fallback
                    response = requests.get(f"{API_BASE_URL}/temperature/latest", headers=headers)
                    print(f"Temperature API response: {response.status_code}")
                    
                    if response.status_code == 200:
                        session['token'] = token
                        session['role'] = 'customer'
                        session['customer_code'] = customer_code
                        flash('Login successful', 'success')
                        return redirect(url_for('customer.dashboard'))
                    else:
                        flash('Invalid token', 'danger')
            except requests.exceptions.RequestException as e:
                print(f"API request error: {str(e)}")
                flash('API service unavailable', 'danger')
    
    # Check API health before showing login page
    try:
        health_response = requests.get(HEALTH_URL)
        api_status = health_response.json().get('status') == 'ok'
    except:
        api_status = False
    
    return render_template('login.html', api_status=api_status)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/api/health')
def api_health():
    try:
        response = requests.get(HEALTH_URL)
        return jsonify(response.json())
    except:
        return jsonify({"status": "error", "message": "API service unavailable"})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Server error occurred"), 500


@app.context_processor
def utility_processor():
    def api_url():
        return API_BASE_URL
    
    def customer_name():
        if 'token' in session and session.get('role') == 'customer':
            try:
                profile = make_api_request('/customers/profile')
                return profile.get('name', session.get('customer_code', 'Customer'))
            except:
                return session.get('customer_code', 'Customer')
        return 'Guest'
    
    return dict(api_url=api_url, customer_name=customer_name)

@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object or ISO timestamp string to a readable format."""
    if value is None:
        return ""
    
    # If value is already a datetime object
    if isinstance(value, datetime):
        return value.strftime(format)
    
    # If value is a string, try to parse it
    try:
        # Handle ISO format with timezone
        if isinstance(value, str):
            # Remove any timezone part for simpler parsing
            if 'T' in value:
                # ISO format with 'T' separator
                parts = value.split('.')
                if len(parts) > 1:
                    # Has milliseconds
                    dt_str = parts[0]
                else:
                    # No milliseconds
                    if '+' in value:
                        dt_str = value.split('+')[0]
                    elif 'Z' in value:
                        dt_str = value.replace('Z', '')
                    else:
                        dt_str = value
                
                # Parse the datetime
                dt = datetime.fromisoformat(dt_str.replace('Z', ''))
            else:
                # Simple format without 'T'
                dt = datetime.fromisoformat(value)
            
            return dt.strftime(format)
    except (ValueError, TypeError):
        # If parsing fails, return the original value
        return value
    
    # If all else fails, return the original value
    return value



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)