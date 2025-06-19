from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
import requests
import os
import json
from datetime import datetime

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# API configuration - point to your existing API
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
API_TIMEOUT = 10  # seconds

# Helper function to call the API
def call_api(endpoint, method='GET', data=None, params=None, headers=None):
    """Make an API call and handle errors"""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Set default headers
    if headers is None:
        headers = {}
    
    # Add auth token if available
    if 'api_token' in session:
        headers['Authorization'] = f"Bearer {session['api_token']}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=API_TIMEOUT)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=API_TIMEOUT)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, headers=headers, timeout=API_TIMEOUT)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=API_TIMEOUT)
        else:
            return {'error': 'Invalid method'}, 400
        
        # Check if the response is JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            result = response.json()
        else:
            result = {'data': response.text}
        
        # Check for API errors
        if not response.ok:
            error_message = result.get('detail', 'Unknown API error')
            return {'error': error_message}, response.status_code
        
        return result, response.status_code
        
    except requests.exceptions.Timeout:
        return {'error': 'API request timed out'}, 504
    except requests.exceptions.ConnectionError:
        return {'error': 'Could not connect to API server'}, 503
    except Exception as e:
        return {'error': str(e)}, 500

# Routes
@app.route('/')
def index():
    """Dashboard home page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        # Get form data
        token = request.form.get('token')
        
        if not token:
            flash('Please enter an API token', 'danger')
            return render_template('login.html')
        
        # Validate token by making an API request
        headers = {'Authorization': f"Bearer {token}"}
        try:
            response = requests.get(f"{API_BASE_URL}/customers/me", headers=headers, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                customer_data = response.json()
                
                # Store user data in session
                session['user_id'] = customer_data.get('id')
                session['customer_name'] = customer_data.get('name')
                session['api_token'] = token
                session['is_admin'] = 'admin' in customer_data.get('permissions', [])
                
                flash('Login successful', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid API token', 'danger')
                return render_template('login.html')
                
        except requests.exceptions.RequestException as e:
            flash(f'Error connecting to API: {str(e)}', 'danger')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/customers/<customer_id>')
def customer_view(customer_id):
    """Customer detail view"""
    # Check if user is logged in and has admin privileges
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not session.get('is_admin') and session.get('user_id') != customer_id:
        flash('You do not have permission to view this customer', 'danger')
        return redirect(url_for('index'))
    
    # Get customer data from API
    result, status_code = call_api(f"/admin/customers/{customer_id}/status")
    
    if status_code != 200:
        flash(f"Error: {result.get('error', 'Could not load customer data')}", 'danger')
        return redirect(url_for('index'))
    
    # Get API details for the customer
    api_token = session.get('api_token', '')
    api_endpoint = f"{API_BASE_URL}/temperatures"
    
    return render_template('customer_view.html', 
                          customer=result.get('customer', {}),
                          api_token=api_token,
                          api_endpoint=api_endpoint)

@app.route('/admin')
def admin_panel():
    """Admin panel view"""
    # Check if user is logged in and has admin privileges
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not session.get('is_admin'):
        flash('You do not have permission to access the admin panel', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin_panel.html')

@app.route('/api_docs')
def api_docs():
    """API documentation view"""
    return render_template('api_docs.html', api_base_url=API_BASE_URL)

# Forward API requests directly to your real API
@app.route('/api/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def api_proxy(endpoint):
    """Proxy API requests to the real API"""
    # Get the token from the session
    token = session.get('api_token')
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Forward the request to the real API
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {'Authorization': f"Bearer {token}"}
    
    # Get params from request
    params = request.args.to_dict() if request.args else {}
    
    # Get data from request
    data = request.get_json() if request.is_json else None
    
    try:
        if request.method == 'GET':
            response = requests.get(url, params=params, headers=headers, timeout=API_TIMEOUT)
        elif request.method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=API_TIMEOUT)
        elif request.method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=API_TIMEOUT)
        elif request.method == 'PATCH':
            response = requests.patch(url, json=data, headers=headers, timeout=API_TIMEOUT)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=API_TIMEOUT)
        else:
            return jsonify({'error': 'Invalid method'}), 400
        
        # Return the response from the API
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

# Favicon route
@app.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                              'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Helper template functions
@app.template_filter('format_date')
def format_date(value, format='%Y-%m-%d %H:%M'):
    """Format a date string or timestamp"""
    if not value:
        return ''
    
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return value
    
    return value.strftime(format)

if __name__ == '__main__':
    # Start development server
    app.run(debug=True, host='0.0.0.0', port=5000)