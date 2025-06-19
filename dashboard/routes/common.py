# dashboard/routes/common.py
from flask import Blueprint, render_template, jsonify, request
import requests
import os

common_bp = Blueprint('common', __name__)

# API Configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
HEALTH_URL = os.environ.get('HEALTH_URL', 'http://localhost:8000/health')

@common_bp.route('/health')
def health():
    """System health status page"""
    try:
        health_response = requests.get(HEALTH_URL)
        api_data = health_response.json()
        api_status = api_data.get('status') == 'ok'
        api_version = api_data.get('version', 'Unknown')
        api_uptime = api_data.get('uptime_seconds', 0)
        database_status = api_data.get('database', 'Unknown')
        rabbitmq_status = api_data.get('rabbitmq', 'Unknown')
    except:
        api_status = False
        api_version = 'Unknown'
        api_uptime = 0
        database_status = 'Unknown'
        rabbitmq_status = 'Unknown'
    
    return render_template(
        'health.html', 
        api_status=api_status,
        api_version=api_version,
        api_uptime=api_uptime,
        database_status=database_status,
        rabbitmq_status=rabbitmq_status
    )

@common_bp.route('/ping')
def ping():
    """Simple ping endpoint for health checks"""
    return jsonify({"ping": "pong"})