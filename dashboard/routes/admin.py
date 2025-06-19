# dashboard/routes/admin.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
import requests
import json
import datetime
from functools import wraps


from utils import make_api_request, admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard home page"""
    try:
        
        customers = make_api_request('/admin/customers')
        
       
        system_config = make_api_request('/admin/config')
        
      
        ingestion_logs = make_api_request('/admin/ingestion/logs')
        
       
        temp_summary = make_api_request('/admin/analytics/temperature/summary')
        
 
        facilities = make_api_request('/admin/facilities')
        
        return render_template(
            'admin/dashboard.html',
            customers=customers.get('items', []),
            system_config=system_config,
            ingestion_logs=ingestion_logs.get('items', []),
            temp_summary=temp_summary,
            facilities=facilities.get('items', [])
        )
    except Exception as e:
        flash(f"Error loading admin dashboard data: {str(e)}", "danger")
        return render_template('admin/dashboard.html')

@admin_bp.route('/customers')
@admin_required
def customers():
    """Admin customers management page"""
    try:
   
        customers_data = make_api_request('/admin/customers')
        
        return render_template(
            'admin/customers.html', 
            customers=customers_data.get('items', [])
        )
    except Exception as e:
        flash(f"Error loading customers data: {str(e)}", "danger")
        return render_template('admin/customers.html', customers=[])

@admin_bp.route('/customer/<customer_id>')
@admin_required
def customer_details(customer_id):
    """Detailed view of a single customer"""
    try:
    
        customer = make_api_request(f'/admin/customers/{customer_id}')
        
      
        tokens = make_api_request(f'/admin/customers/{customer_id}/tokens')

        all_facilities = make_api_request('/admin/facilities')
        facilities = [f for f in all_facilities.get('items', []) if f.get('customer_id') == customer_id]
        
        return render_template(
            'admin/customer_details.html',
            customer=customer,
            tokens=tokens,
            facilities=facilities
        )
    except Exception as e:
        flash(f"Error loading customer details: {str(e)}", "danger")
        return redirect(url_for('admin.customers'))

@admin_bp.route('/facilities')
@admin_required
def facilities():
    """Admin facilities management page"""
    try:
       
        facilities_data = make_api_request('/admin/facilities')
        
    
        customers_data = make_api_request('/admin/customers')

        customer_lookup = {}
        for customer in customers_data.get('items', []):
            customer_lookup[customer.get('id')] = customer.get('name') or customer.get('customer_code')
        
        return render_template(
            'admin/facilities.html', 
            facilities=facilities_data.get('items', []),
            customer_lookup=customer_lookup
        )
    except Exception as e:
        flash(f"Error loading facilities data: {str(e)}", "danger")
        return render_template('admin/facilities.html', facilities=[])

@admin_bp.route('/facility/<facility_id>')
@admin_required
def facility_details(facility_id):
    """Admin detailed view of a single facility"""
    try:

        readings = make_api_request(f'/admin/temperature/facility/{facility_id}')
        

        all_facilities = make_api_request('/admin/facilities')
        facility = next((f for f in all_facilities.get('items', []) if f.get('id') == facility_id), None)
        
        if not facility:
            flash("Facility not found", "danger")
            return redirect(url_for('admin.facilities'))
        
    
        customer_id = facility.get('customer_id')
        customer = make_api_request(f'/admin/customers/{customer_id}')
      
        all_units = []  
        
        return render_template(
            'admin/facility_details.html',
            facility=facility,
            readings=readings.get('items', []),
            customer=customer,
            units=all_units
        )
    except Exception as e:
        flash(f"Error loading facility details: {str(e)}", "danger")
        return redirect(url_for('admin.facilities'))

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Admin analytics dashboard"""
    try:
 
        temp_summary = make_api_request('/admin/analytics/temperature/summary')
     
        customers = make_api_request('/admin/customers')
        
    
        ingestion_logs = make_api_request('/admin/ingestion/logs')
        
        return render_template(
            'admin/analytics.html',
            temp_summary=temp_summary,
            customers=customers.get('items', []),
            ingestion_logs=ingestion_logs.get('items', [])
        )
    except Exception as e:
        flash(f"Error loading analytics data: {str(e)}", "danger")
        return render_template('admin/analytics.html')

@admin_bp.route('/config', methods=['GET', 'POST'])
@admin_required
def config():
    """Admin system configuration page"""
    if request.method == 'POST':
     
        config_key = request.form.get('key')
        config_value = request.form.get('value')
        config_description = request.form.get('description')
        
        if config_key and config_value:
            data = {
                'value': config_value,
                'description': config_description
            }
            
            try:
                result = make_api_request(f'/admin/config/{config_key}', method="PUT", data=data)
                flash(f"Configuration updated successfully", "success")
            except Exception as e:
                flash(f"Error updating configuration: {str(e)}", "danger")
    
    try:
        
        system_config = make_api_request('/admin/config')
        
        return render_template(
            'admin/config.html',
            system_config=system_config
        )
    except Exception as e:
        flash(f"Error loading configuration data: {str(e)}", "danger")
        return render_template('admin/config.html')

@admin_bp.route('/ml')
@admin_required
def ml():
    """Admin Machine Learning dashboard (placeholder for future)"""
    return render_template('admin/ml.html')


@admin_bp.route('/api/customer_stats')
@admin_required
def customer_stats():
    """Get aggregated stats per customer in JSON format for charts"""
    try:
        
        customers = make_api_request('/admin/customers')
        
 
        stats = []
        for customer in customers.get('items', []):
            customer_id = customer.get('id')
            customer_code = customer.get('customer_code')
            

            stats.append({
                'customer_id': customer_id,
                'customer_code': customer_code,
                'facility_count': customer.get('facility_count', 0),
                'unit_count': customer.get('unit_count', 0),
                'reading_count': customer.get('active_readings_count', 0)
            })
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/ingestion_summary')
@admin_required
def ingestion_summary():
    """Get summary of recent ingestion processes for charts"""
    try:
       
        logs = make_api_request('/admin/ingestion/logs')
        

        success_count = 0
        failure_count = 0
        total_records = 0
        
        for log in logs.get('items', []):
            if log.get('status') == 'success':
                success_count += 1
                total_records += log.get('records_processed', 0)
            else:
                failure_count += 1
        
        summary = {
            'success_count': success_count,
            'failure_count': failure_count,
            'total_records': total_records,
            'success_rate': (success_count / (success_count + failure_count)) * 100 if (success_count + failure_count) > 0 else 0
        }
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500