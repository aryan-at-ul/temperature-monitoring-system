# dashboard/routes/customer.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
import requests
import json
import datetime
from functools import wraps

from utils import make_api_request, login_required

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
@login_required
def dashboard():
    """Customer dashboard home page"""
    try:
      
        customer_profile = make_api_request('/customers/profile')
        
       
        latest_readings = make_api_request('/temperature/latest')
        
      
        temp_stats = make_api_request('/temperature/stats')
        
 
        facilities = make_api_request('/facilities')
        
        return render_template(
            'customer/dashboard.html',
            profile=customer_profile,
            latest_readings=latest_readings,
            temp_stats=temp_stats,
            facilities=facilities.get('items', [])
        )
    except Exception as e:
        flash(f"Error loading dashboard data: {str(e)}", "danger")
        return render_template('customer/dashboard.html')

@customer_bp.route('/facilities')
@login_required
def facilities():
    """Customer facilities page"""
    try:
    
        facilities_data = make_api_request('/facilities')
        
       
        facilities_with_units = []
        for facility in facilities_data.get('items', []):
            try:
                
                units_data = make_api_request(f'/facilities/{facility["id"]}/units')
                facility['unit_count'] = len(units_data.get('items', []))
            except Exception:
                facility['unit_count'] = 0
                
            facilities_with_units.append(facility)
        
        return render_template(
            'customer/facilities.html', 
            facilities=facilities_with_units
        )
    except Exception as e:
        flash(f"Error loading facilities data: {str(e)}", "danger")
        return render_template('customer/facilities.html', facilities=[])

@customer_bp.route('/facility/<facility_id>')
@login_required
def facility_details(facility_id):
    """Detailed view of a single facility"""
    try:
      
        facility = make_api_request(f'/facilities/{facility_id}/detailed')
        
      
        readings = make_api_request(f'/temperature/facility/{facility_id}')
        
      
        if 'units' not in facility:
            facility['units'] = []
            
          
            try:
                units_data = make_api_request(f'/facilities/{facility_id}/units')
                facility['units'] = units_data.get('items', [])
            except:
                pass
        
        return render_template(
            'customer/facility_details.html',
            facility=facility,
            readings=readings.get('items', [])
        )
    except Exception as e:
        flash(f"Error loading facility details: {str(e)}", "danger")
        return redirect(url_for('customer.facilities'))

@customer_bp.route('/units')
@login_required
def units():
    """All storage units for this customer"""
    facilities_data = make_api_request('/facilities')
    all_units = []
    
    for facility in facilities_data.get('items', []):
        facility_id = facility.get('id')
        units_data = make_api_request(f'/facilities/{facility_id}/units')
        for unit in units_data.get('items', []):
            unit['facility_name'] = facility.get('name') or facility.get('facility_code')
            all_units.append(unit)
    
    return render_template('customer/units.html', units=all_units)

@customer_bp.route('/unit/<unit_id>')
@login_required
def unit_details(unit_id):
    """Detailed view of a single storage unit"""
    try:
      
        unit = make_api_request(f'/units/{unit_id}')
        
    
        readings = make_api_request(f'/temperature/unit/{unit_id}')
        

        facility_id = unit.get('facility_id')
        facility = make_api_request(f'/facilities/{facility_id}')
        
        return render_template(
            'customer/unit_details.html',
            unit=unit,
            readings=readings.get('items', []),
            facility=facility
        )
    except Exception as e:
        flash(f"Error loading unit details: {str(e)}", "danger")
        return redirect(url_for('customer.units'))

@customer_bp.route('/analytics')
@login_required
def analytics():
    """Customer analytics page"""
    try:
   
        temp_summary = make_api_request('/analytics/temperature/summary')
        

        performance = make_api_request('/analytics/performance')
        
    
        alarms = make_api_request('/analytics/alarms/history')
        
  
        end_date = datetime.datetime.now().isoformat()
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
        
        trends = make_api_request(
            '/analytics/temperature/trends',
            params={'interval': 'day', 'start_date': start_date, 'end_date': end_date}
        )
        

        aggregation_data = {
            'group_by': ['day', 'facility'],
            'aggregations': ['avg', 'min', 'max', 'count'],
            'start_date': start_date,
            'end_date': end_date
        }
        
        facility_trends = make_api_request(
            '/temperature/aggregate',
            method="POST",
            data=aggregation_data
        )
        
        return render_template(
            'customer/analytics.html',
            temp_summary=temp_summary,
            performance=performance,
            alarms=alarms.get('items', []),
            trends=trends,
            facility_trends=facility_trends
        )
    except Exception as e:
        flash(f"Error loading analytics data: {str(e)}", "danger")
        return render_template('customer/analytics.html')

@customer_bp.route('/settings')
@login_required
def settings():
    """Customer settings page"""
    try:
   
        profile = make_api_request('/customers/profile')
        
    
        tokens = make_api_request('/customers/tokens')
        
        return render_template(
            'customer/settings.html',
            profile=profile,
            tokens=tokens
        )
    except Exception as e:
        flash(f"Error loading settings data: {str(e)}", "danger")
        return render_template('customer/settings.html')

@customer_bp.route('/ml')
@login_required
def ml():
    """Machine Learning dashboard (placeholder for future)"""
    return render_template('customer/ml.html')


@customer_bp.route('/api/temperature_history/<unit_id>')
@login_required
def temperature_history(unit_id):
    """Get temperature history for a unit in JSON format for charts"""
    try:
        
        readings = make_api_request(f'/temperature/unit/{unit_id}')
        
        
        data = []
        for reading in readings.get('items', []):
            data.append({
                'timestamp': reading.get('recorded_at'),
                'temperature': reading.get('temperature'),
                'status': reading.get('equipment_status')
            })
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_bp.route('/api/facility_stats/<facility_id>')
@login_required
def facility_stats(facility_id):
    """Get aggregated stats for a facility in JSON format for charts"""
    try:
      
        end_date = datetime.datetime.now().isoformat()
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        
       
        aggregation_data = {
            'group_by': ['day'],
            'aggregations': ['avg', 'min', 'max', 'count'],
            'start_date': start_date,
            'end_date': end_date,
            'facility_id': facility_id
        }
        
 
        stats = make_api_request(
            '/temperature/aggregate',
            method="POST",
            data=aggregation_data
        )
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@customer_bp.route('/api/facility_units/<facility_id>')
@login_required
def facility_units(facility_id):
    """Get units for a facility in JSON format"""
    try:
        
        units_data = make_api_request(f'/facilities/{facility_id}/units')
        
       
        return jsonify({
            "facility_id": facility_id,
            "units": units_data.get('items', [])
        })
    except Exception as e:
        return jsonify({"error": str(e), "units": []}), 500