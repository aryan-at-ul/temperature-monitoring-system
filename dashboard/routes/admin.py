# # dashboard/routes/admin.py
# from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
# import requests
# import json
# import datetime
# from functools import wraps

# # Import from utils.py instead of app.py
# from utils import make_api_request, admin_required

# admin_bp = Blueprint('admin', __name__)

# @admin_bp.route('/')
# @admin_required
# def dashboard():
#     """Admin dashboard home page"""
#     try:
#         # Get all customers
#         customers = make_api_request('/admin/customers')
        
#         # Get system configuration
#         system_config = make_api_request('/admin/config')
        
#         # Get recent ingestion logs
#         ingestion_logs = make_api_request('/admin/ingestion/logs')
        
#         # Get temperature summary across all customers
#         temp_summary = make_api_request('/admin/analytics/temperature/summary')
        
#         # Get all facilities 
#         facilities = make_api_request('/admin/facilities')
        
#         return render_template(
#             'admin/dashboard.html',
#             customers=customers.get('items', []),
#             system_config=system_config,
#             ingestion_logs=ingestion_logs.get('items', []),
#             temp_summary=temp_summary,
#             facilities=facilities.get('items', [])
#         )
#     except Exception as e:
#         flash(f"Error loading admin dashboard data: {str(e)}", "danger")
#         return render_template('admin/dashboard.html')

# @admin_bp.route('/customers')
# @admin_required
# def customers():
#     """Admin customers management page"""
#     try:
#         # Get all customers
#         customers_data = make_api_request('/admin/customers')
        
#         return render_template(
#             'admin/customers.html', 
#             customers=customers_data.get('items', [])
#         )
#     except Exception as e:
#         flash(f"Error loading customers data: {str(e)}", "danger")
#         return render_template('admin/customers.html', customers=[])

# @admin_bp.route('/customer/<customer_id>')
# @admin_required
# def customer_details(customer_id):
#     """Detailed view of a single customer"""
#     try:
#         # Get customer details
#         customer = make_api_request(f'/admin/customers/{customer_id}')
        
#         # Get customer tokens
#         tokens = make_api_request(f'/admin/customers/{customer_id}/tokens')
        
#         # Get facilities for this customer
#         # We need to get all facilities and filter by customer_id
#         all_facilities = make_api_request('/admin/facilities')
#         facilities = [f for f in all_facilities.get('items', []) if f.get('customer_id') == customer_id]
        
#         return render_template(
#             'admin/customer_details.html',
#             customer=customer,
#             tokens=tokens,
#             facilities=facilities
#         )
#     except Exception as e:
#         flash(f"Error loading customer details: {str(e)}", "danger")
#         return redirect(url_for('admin.customers'))

# @admin_bp.route('/facilities')
# @admin_required
# def facilities():
#     """Admin facilities management page"""
#     try:
#         # Get all facilities
#         facilities_data = make_api_request('/admin/facilities')
        
#         # Get all customers for mapping customer_id to names
#         customers_data = make_api_request('/admin/customers')
        
#         # Create a customer lookup dict
#         customer_lookup = {}
#         for customer in customers_data.get('items', []):
#             customer_lookup[customer.get('id')] = customer.get('name') or customer.get('customer_code')
        
#         return render_template(
#             'admin/facilities.html', 
#             facilities=facilities_data.get('items', []),
#             customer_lookup=customer_lookup
#         )
#     except Exception as e:
#         flash(f"Error loading facilities data: {str(e)}", "danger")
#         return render_template('admin/facilities.html', facilities=[])

# @admin_bp.route('/facility/<facility_id>')
# @admin_required
# def facility_details(facility_id):
#     """Admin detailed view of a single facility"""
#     try:
#         # Since we're admin, we need to use admin endpoints
#         # Get temperature readings for this facility
#         readings = make_api_request(f'/admin/temperature/facility/{facility_id}')
        
#         # Get all facilities to find the one we need
#         all_facilities = make_api_request('/admin/facilities')
#         facility = next((f for f in all_facilities.get('items', []) if f.get('id') == facility_id), None)
        
#         if not facility:
#             flash("Facility not found", "danger")
#             return redirect(url_for('admin.facilities'))
        
#         # Get customer info
#         customer_id = facility.get('customer_id')
#         customer = make_api_request(f'/admin/customers/{customer_id}')
        
#         # Get storage units for this facility
#         # We don't have a direct admin endpoint for this, so we'll need to improvise
#         all_units = []  # This would ideally come from an admin API endpoint
        
#         return render_template(
#             'admin/facility_details.html',
#             facility=facility,
#             readings=readings.get('items', []),
#             customer=customer,
#             units=all_units
#         )
#     except Exception as e:
#         flash(f"Error loading facility details: {str(e)}", "danger")
#         return redirect(url_for('admin.facilities'))

# @admin_bp.route('/analytics')
# @admin_required
# def analytics():
#     """Admin analytics dashboard"""
#     try:
#         # Get temperature summary across all customers
#         temp_summary = make_api_request('/admin/analytics/temperature/summary')
        
#         # Get customer aggregation data
#         customers = make_api_request('/admin/customers')
        
#         # Get recent ingestion logs
#         ingestion_logs = make_api_request('/admin/ingestion/logs')
        
#         return render_template(
#             'admin/analytics.html',
#             temp_summary=temp_summary,
#             customers=customers.get('items', []),
#             ingestion_logs=ingestion_logs.get('items', [])
#         )
#     except Exception as e:
#         flash(f"Error loading analytics data: {str(e)}", "danger")
#         return render_template('admin/analytics.html')

# @admin_bp.route('/config', methods=['GET', 'POST'])
# @admin_required
# def config():
#     """Admin system configuration page"""
#     if request.method == 'POST':
#         # Handle configuration updates
#         config_key = request.form.get('key')
#         config_value = request.form.get('value')
#         config_description = request.form.get('description')
        
#         if config_key and config_value:
#             data = {
#                 'value': config_value,
#                 'description': config_description
#             }
            
#             try:
#                 result = make_api_request(f'/admin/config/{config_key}', method="PUT", data=data)
#                 flash(f"Configuration updated successfully", "success")
#             except Exception as e:
#                 flash(f"Error updating configuration: {str(e)}", "danger")
    
#     try:
#         # Get system configuration
#         system_config = make_api_request('/admin/config')
        
#         return render_template(
#             'admin/config.html',
#             system_config=system_config
#         )
#     except Exception as e:
#         flash(f"Error loading configuration data: {str(e)}", "danger")
#         return render_template('admin/config.html')

# @admin_bp.route('/ml')
# @admin_required
# def ml():
#     """Admin Machine Learning dashboard (placeholder for future)"""
#     return render_template('admin/ml.html')

# # API endpoints for AJAX requests
# @admin_bp.route('/api/customer_stats')
# @admin_required
# def customer_stats():
#     """Get aggregated stats per customer in JSON format for charts"""
#     try:
#         # Get all customers
#         customers = make_api_request('/admin/customers')
        
#         # Build stats for each customer
#         stats = []
#         for customer in customers.get('items', []):
#             customer_id = customer.get('id')
#             customer_code = customer.get('customer_code')
            
#             # This is a simplification - in reality, you'd need an admin endpoint
#             # that provides per-customer statistics
#             stats.append({
#                 'customer_id': customer_id,
#                 'customer_code': customer_code,
#                 'facility_count': customer.get('facility_count', 0),
#                 'unit_count': customer.get('unit_count', 0),
#                 'reading_count': customer.get('active_readings_count', 0)
#             })
        
#         return jsonify(stats)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @admin_bp.route('/api/ingestion_summary')
# @admin_required
# def ingestion_summary():
#     """Get summary of recent ingestion processes for charts"""
#     try:
#         # Get ingestion logs
#         logs = make_api_request('/admin/ingestion/logs')
        
#         # Process logs to get summary data
#         success_count = 0
#         failure_count = 0
#         total_records = 0
        
#         for log in logs.get('items', []):
#             if log.get('status') == 'success':
#                 success_count += 1
#                 total_records += log.get('records_processed', 0)
#             else:
#                 failure_count += 1
        
#         summary = {
#             'success_count': success_count,
#             'failure_count': failure_count,
#             'total_records': total_records,
#             'success_rate': (success_count / (success_count + failure_count)) * 100 if (success_count + failure_count) > 0 else 0
#         }
        
#         return jsonify(summary)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# dashboard/routes/admin.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
import requests
import json
import datetime
from functools import wraps
from datetime import datetime, timedelta

# Import from utils.py instead of app.py
from utils import make_api_request, admin_required

admin_bp = Blueprint('admin', __name__)

def process_customer_data(customers_data):
    """
    Process customer data to ensure all required fields are present.
    Adds 'active_readings_count' field if missing.
    """
    if not customers_data or not isinstance(customers_data, dict):
        return {"items": []}
    
    items = customers_data.get('items', [])
    
    # Add missing 'active_readings_count' field to each customer
    for customer in items:
        if 'active_readings_count' not in customer:
            # Default to reading_count if available, otherwise 0
            customer['active_readings_count'] = customer.get('reading_count', 0)
    
    return {"items": items}

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard home page"""
    # Initialize variables with default values that match the expected template structure
    customers = []
    system_config = {}
    ingestion_logs = []
    
    # Structure temp_summary with ALL required fields
    temp_summary = {
        'avg_temperature': 0.0,
        'min_temperature': 0.0,
        'max_temperature': 0.0,
        'temperature_unit': 'C',
        'total_readings': 0,
        'reading_count': 1,  # Set to 1 to avoid division by zero
        'time_range_start': datetime.now() - timedelta(days=7),
        'time_range_end': datetime.now(),
        'readings_by_customer': [],
        'readings_by_hour': [],
        'normal_count': 0,
        'warning_count': 0,
        'critical_count': 0,
        'error_count': 0,
        'unknown_count': 0,
        'by_status': {
            'normal': 0,
            'warning': 0,
            'critical': 0,
            'error': 0,
            'unknown': 0
        },
        'by_customer': [],
        'by_facility': [],
        'by_hour': []
    }
    
    facilities = []
    
    try:
        # Get all customers with error handling
        try:
            customers_data = make_api_request('/admin/customers')
            if isinstance(customers_data, tuple):
                # Error response
                flash(f"Error loading customer data: {customers_data[0].get('error', 'Unknown error')}", "warning")
            else:
                customers = customers_data.get('items', [])
        except Exception as e:
            flash(f"Error loading customer data: {str(e)}", "warning")
        
        # Get system configuration
        try:
            system_config = make_api_request('/admin/config')
            if isinstance(system_config, tuple):
                flash(f"Error loading system configuration: {system_config[0].get('error', 'Unknown error')}", "warning")
                system_config = {}
        except Exception as e:
            flash(f"Error loading system configuration: {str(e)}", "warning")
            system_config = {}
        
        # Get recent ingestion logs
        try:
            ingestion_logs_data = make_api_request('/admin/ingestion/logs')
            if isinstance(ingestion_logs_data, tuple):
                flash(f"Error loading ingestion logs: {ingestion_logs_data[0].get('error', 'Unknown error')}", "warning")
                ingestion_logs = []
            else:
                ingestion_logs = ingestion_logs_data.get('items', [])
        except Exception as e:
            flash(f"Error loading ingestion logs: {str(e)}", "warning")
            ingestion_logs = []
        
        # Get temperature summary across all customers
        try:
            temp_summary_data = make_api_request('/admin/analytics/temperature/summary')
            if isinstance(temp_summary_data, tuple):
                flash(f"Error loading temperature summary: {temp_summary_data[0].get('error', 'Unknown error')}", "warning")
            else:
                # Debug output
                print(f"Temperature summary data structure: {temp_summary_data}")
                
                # Check if we have the 'system' key (aggregated data)
                if isinstance(temp_summary_data, dict) and 'system' in temp_summary_data:
                    system_data = temp_summary_data.get('system', {})
                    
                    # Update our temp_summary with the system data
                    temp_summary['min_temperature'] = system_data.get('min_temperature', 0.0)
                    temp_summary['max_temperature'] = system_data.get('max_temperature', 0.0)
                    temp_summary['avg_temperature'] = system_data.get('avg_temperature', 0.0)
                    temp_summary['temperature_unit'] = system_data.get('temperature_unit', 'C')
                    temp_summary['total_readings'] = system_data.get('reading_count', 0)
                    temp_summary['reading_count'] = max(system_data.get('reading_count', 1), 1)  # Avoid division by zero
                    temp_summary['time_range_start'] = system_data.get('time_range_start', datetime.now() - timedelta(days=7))
                    temp_summary['time_range_end'] = system_data.get('time_range_end', datetime.now())
                    temp_summary['normal_count'] = system_data.get('normal_count', 0)
                    temp_summary['warning_count'] = system_data.get('warning_count', 0)
                    temp_summary['critical_count'] = system_data.get('critical_count', 0)
                    temp_summary['error_count'] = system_data.get('error_count', 0)
                    
                    # Create by_customer data from individual customer entries
                    temp_summary['by_customer'] = []
                    for customer_code, customer_data in temp_summary_data.items():
                        if customer_code != 'system':
                            temp_summary['by_customer'].append({
                                'customer_code': customer_code,
                                'reading_count': customer_data.get('reading_count', 0),
                                'avg_temperature': customer_data.get('avg_temperature', 0.0),
                                'min_temperature': customer_data.get('min_temperature', 0.0),
                                'max_temperature': customer_data.get('max_temperature', 0.0)
                            })
                elif isinstance(temp_summary_data, dict):
                    # If the response has a different structure, try to adapt
                    for key, value in temp_summary_data.items():
                        if key in temp_summary:
                            temp_summary[key] = value
        except Exception as e:
            flash(f"Error loading temperature summary: {str(e)}", "warning")
        
       
        try:
            facilities_data = make_api_request('/admin/facilities')
            if isinstance(facilities_data, tuple):
                flash(f"Error loading facilities data: {facilities_data[0].get('error', 'Unknown error')}", "warning")
                facilities = []
            else:
                facilities = facilities_data.get('items', [])
        except Exception as e:
            flash(f"Error loading facilities data: {str(e)}", "warning")
            facilities = []
        
        return render_template(
            'admin/dashboard.html',
            customers=customers,
            system_config=system_config,
            ingestion_logs=ingestion_logs,
            temp_summary=temp_summary,
            facilities=facilities
        )
    except Exception as e:
        flash(f"Error loading admin dashboard data: {str(e)}", "danger")
        
        return render_template(
            'admin/dashboard.html',
            customers=[],
            system_config={},
            ingestion_logs=[],
            temp_summary=temp_summary,
            facilities=[]
        )


@admin_bp.route('/customers')
@admin_required
def customers():
    """Admin customers management page"""
    try:
        # Get all customers with error handling
        try:
            customers_data = make_api_request('/admin/customers')
            processed_data = process_customer_data(customers_data)
            customers = processed_data.get('items', [])
        except Exception as e:
            flash(f"Error loading customer data: {str(e)}", "warning")
            customers = []
        
        return render_template(
            'admin/customers.html', 
            customers=customers
        )
    except Exception as e:
        flash(f"Error loading customers data: {str(e)}", "danger")
        return render_template('admin/customers.html', customers=[])

@admin_bp.route('/customer/<customer_id>')
@admin_required
def customer_details(customer_id):
    """Detailed view of a single customer"""
    try:
        # Get customer details
        customer = make_api_request(f'/admin/customers/{customer_id}')
        
        # Get customer tokens
        tokens = make_api_request(f'/admin/customers/{customer_id}/tokens')
        
        # Get facilities for this customer
        # We need to get all facilities and filter by customer_id
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
        # Get all facilities
        facilities_data = make_api_request('/admin/facilities')
        
        # Get all customers for mapping customer_id to names
        try:
            customers_data = make_api_request('/admin/customers')
            processed_data = process_customer_data(customers_data)
            customer_lookup = {}
            for customer in processed_data.get('items', []):
                customer_lookup[customer.get('id')] = customer.get('name') or customer.get('customer_code')
        except Exception:
            customer_lookup = {}
        
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
        # Since we're admin, we need to use admin endpoints
        # Get temperature readings for this facility
        readings = make_api_request(f'/admin/temperature/facility/{facility_id}')
        
        # Get all facilities to find the one we need
        all_facilities = make_api_request('/admin/facilities')
        facility = next((f for f in all_facilities.get('items', []) if f.get('id') == facility_id), None)
        
        if not facility:
            flash("Facility not found", "danger")
            return redirect(url_for('admin.facilities'))
        
        # Get customer info
        customer_id = facility.get('customer_id')
        customer = make_api_request(f'/admin/customers/{customer_id}')
        
        # Get storage units for this facility
        # We don't have a direct admin endpoint for this, so we'll need to improvise
        all_units = []  # This would ideally come from an admin API endpoint
        
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
        # Get temperature summary across all customers
        temp_summary = make_api_request('/admin/analytics/temperature/summary')
        
        # Get customer aggregation data with error handling
        try:
            customers_data = make_api_request('/admin/customers')
            processed_data = process_customer_data(customers_data)
            customers = processed_data.get('items', [])
        except Exception:
            customers = []
        
        # Get recent ingestion logs
        ingestion_logs = make_api_request('/admin/ingestion/logs')
        
        return render_template(
            'admin/analytics.html',
            temp_summary=temp_summary,
            customers=customers,
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
        # Handle configuration updates
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
        # Get system configuration
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

# API endpoints for AJAX requests
@admin_bp.route('/api/customer_stats')
@admin_required
def customer_stats():
    """Get aggregated stats per customer in JSON format for charts"""
    try:
        # Get all customers with error handling
        try:
            customers_data = make_api_request('/admin/customers')
            processed_data = process_customer_data(customers_data)
            customers = processed_data.get('items', [])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        # Build stats for each customer
        stats = []
        for customer in customers:
            customer_id = customer.get('id')
            customer_code = customer.get('customer_code')
            
            # This is a simplification - in reality, you'd need an admin endpoint
            # that provides per-customer statistics
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
        # Get ingestion logs
        logs = make_api_request('/admin/ingestion/logs')
        
        # Process logs to get summary data
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