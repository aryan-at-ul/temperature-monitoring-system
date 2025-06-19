# api/services/temperature_service.py
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import logging
from database.connection import db

logger = logging.getLogger(__name__)

class TemperatureService:
    @classmethod
    async def get_readings(cls, customer: Dict, query, facility_id=None, storage_unit_id=None):
        """
        Get temperature readings based on the query parameters.
        """
        # Build the query
        sql_query = """
            SELECT tr.*, f.name as facility_name, su.name as unit_name
            FROM temperature_readings tr
            JOIN facilities f ON tr.facility_id = f.id
            JOIN storage_units su ON tr.storage_unit_id = su.id
            WHERE tr.customer_id = $1
        """
        
        params = [customer['id']]
        param_count = 2
        
        if facility_id:
            sql_query += f" AND tr.facility_id = ${param_count}"
            params.append(facility_id)
            param_count += 1
        
        if storage_unit_id:
            sql_query += f" AND tr.storage_unit_id = ${param_count}"
            params.append(storage_unit_id)
            param_count += 1
            
        if query.start_date:
            sql_query += f" AND tr.recorded_at >= ${param_count}"
            params.append(query.start_date)
            param_count += 1
            
        if query.end_date:
            sql_query += f" AND tr.recorded_at <= ${param_count}"
            params.append(query.end_date)
            param_count += 1
            
        if query.min_temperature is not None:
            sql_query += f" AND tr.temperature >= ${param_count}"
            params.append(query.min_temperature)
            param_count += 1
            
        if query.max_temperature is not None:
            sql_query += f" AND tr.temperature <= ${param_count}"
            params.append(query.max_temperature)
            param_count += 1
            
        if query.equipment_status:
            sql_query += f" AND tr.equipment_status = ${param_count}"
            params.append(query.equipment_status)
            param_count += 1
            
        if query.quality_score is not None:
            sql_query += f" AND tr.quality_score = ${param_count}"
            params.append(query.quality_score)
            param_count += 1
            
        if query.sensor_id:
            sql_query += f" AND tr.sensor_id = ${param_count}"
            params.append(query.sensor_id)
            param_count += 1
        
        # Add ordering
        sql_query += " ORDER BY tr.recorded_at DESC"
        
        # Add pagination
        sql_query += f" LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([query.limit, query.offset])
        
        # Execute the query
        readings = await db.fetch(sql_query, *params)
        
        # Get total count using the same filters
        count_query = """
            SELECT COUNT(*) as count
            FROM temperature_readings tr
            WHERE tr.customer_id = $1
        """
        
        count_params = [customer['id']]
        param_count = 2
        
        if facility_id:
            count_query += f" AND tr.facility_id = ${param_count}"
            count_params.append(facility_id)
            param_count += 1
        
        if storage_unit_id:
            count_query += f" AND tr.storage_unit_id = ${param_count}"
            count_params.append(storage_unit_id)
            param_count += 1
            
        if query.start_date:
            count_query += f" AND tr.recorded_at >= ${param_count}"
            count_params.append(query.start_date)
            param_count += 1
            
        if query.end_date:
            count_query += f" AND tr.recorded_at <= ${param_count}"
            count_params.append(query.end_date)
            param_count += 1
            
        if query.min_temperature is not None:
            count_query += f" AND tr.temperature >= ${param_count}"
            count_params.append(query.min_temperature)
            param_count += 1
            
        if query.max_temperature is not None:
            count_query += f" AND tr.temperature <= ${param_count}"
            count_params.append(query.max_temperature)
            param_count += 1
            
        if query.equipment_status:
            count_query += f" AND tr.equipment_status = ${param_count}"
            count_params.append(query.equipment_status)
            param_count += 1
            
        if query.quality_score is not None:
            count_query += f" AND tr.quality_score = ${param_count}"
            count_params.append(query.quality_score)
            param_count += 1
            
        if query.sensor_id:
            count_query += f" AND tr.sensor_id = ${param_count}"
            count_params.append(query.sensor_id)
            param_count += 1
        
        count_result = await db.fetchrow(count_query, *count_params)
        total = count_result['count'] if count_result else 0
        
        return readings, total
    
    @classmethod
    async def get_admin_readings(cls, query, customer_id=None, facility_id=None, storage_unit_id=None):
        """
        Get temperature readings for admin users.
        This allows viewing data across all customers.
        """
        # Build the query
        sql_query = """
            SELECT tr.*, f.name as facility_name, su.name as unit_name, c.customer_code, c.name as customer_name
            FROM temperature_readings tr
            JOIN facilities f ON tr.facility_id = f.id
            JOIN storage_units su ON tr.storage_unit_id = su.id
            JOIN customers c ON tr.customer_id = c.id
            WHERE 1=1
        """
        
        params = []
        param_count = 1
        
        if customer_id:
            sql_query += f" AND tr.customer_id = ${param_count}"
            params.append(customer_id)
            param_count += 1
        
        if facility_id:
            sql_query += f" AND tr.facility_id = ${param_count}"
            params.append(facility_id)
            param_count += 1
        
        if storage_unit_id:
            sql_query += f" AND tr.storage_unit_id = ${param_count}"
            params.append(storage_unit_id)
            param_count += 1
            
        if query.start_date:
            sql_query += f" AND tr.recorded_at >= ${param_count}"
            params.append(query.start_date)
            param_count += 1
            
        if query.end_date:
            sql_query += f" AND tr.recorded_at <= ${param_count}"
            params.append(query.end_date)
            param_count += 1
            
        if query.min_temperature is not None:
            sql_query += f" AND tr.temperature >= ${param_count}"
            params.append(query.min_temperature)
            param_count += 1
            
        if query.max_temperature is not None:
            sql_query += f" AND tr.temperature <= ${param_count}"
            params.append(query.max_temperature)
            param_count += 1
            
        if query.equipment_status:
            sql_query += f" AND tr.equipment_status = ${param_count}"
            params.append(query.equipment_status)
            param_count += 1
            
        if query.quality_score is not None:
            sql_query += f" AND tr.quality_score = ${param_count}"
            params.append(query.quality_score)
            param_count += 1
            
        if query.sensor_id:
            sql_query += f" AND tr.sensor_id = ${param_count}"
            params.append(query.sensor_id)
            param_count += 1
        
        # Add ordering
        sql_query += " ORDER BY tr.recorded_at DESC"
        
        # Add pagination
        sql_query += f" LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([query.limit, query.offset])
        
        # Execute the query
        readings = await db.fetch(sql_query, *params)
        
        # Get total count using the same filters
        count_query = """
            SELECT COUNT(*) as count
            FROM temperature_readings tr
            WHERE 1=1
        """
        
        count_params = []
        param_count = 1
        
        if customer_id:
            count_query += f" AND tr.customer_id = ${param_count}"
            count_params.append(customer_id)
            param_count += 1
        
        if facility_id:
            count_query += f" AND tr.facility_id = ${param_count}"
            count_params.append(facility_id)
            param_count += 1
        
        if storage_unit_id:
            count_query += f" AND tr.storage_unit_id = ${param_count}"
            count_params.append(storage_unit_id)
            param_count += 1
            
        if query.start_date:
            count_query += f" AND tr.recorded_at >= ${param_count}"
            count_params.append(query.start_date)
            param_count += 1
            
        if query.end_date:
            count_query += f" AND tr.recorded_at <= ${param_count}"
            count_params.append(query.end_date)
            param_count += 1
            
        if query.min_temperature is not None:
            count_query += f" AND tr.temperature >= ${param_count}"
            count_params.append(query.min_temperature)
            param_count += 1
            
        if query.max_temperature is not None:
            count_query += f" AND tr.temperature <= ${param_count}"
            count_params.append(query.max_temperature)
            param_count += 1
            
        if query.equipment_status:
            count_query += f" AND tr.equipment_status = ${param_count}"
            count_params.append(query.equipment_status)
            param_count += 1
            
        if query.quality_score is not None:
            count_query += f" AND tr.quality_score = ${param_count}"
            count_params.append(query.quality_score)
            param_count += 1
            
        if query.sensor_id:
            count_query += f" AND tr.sensor_id = ${param_count}"
            count_params.append(query.sensor_id)
            param_count += 1
        
        count_result = await db.fetchrow(count_query, *count_params)
        total = count_result['count'] if count_result else 0
        
        return readings, total
    
    @classmethod
    async def create_reading(cls, customer_id: UUID, reading_data):
        """
        Create a new temperature reading.
        """
        # First, verify the storage unit belongs to the customer
        query = """
            SELECT su.id
            FROM storage_units su
            JOIN facilities f ON su.facility_id = f.id
            WHERE su.id = $1 AND f.customer_id = $2
        """
        unit = await db.fetchrow(query, str(reading_data.storage_unit_id), str(customer_id))
        
        if not unit:
            raise ValueError("Storage unit not found or does not belong to the customer")
        
        # Get the facility ID for the storage unit
        facility_query = "SELECT facility_id FROM storage_units WHERE id = $1"
        facility_result = await db.fetchrow(facility_query, str(reading_data.storage_unit_id))
        
        if not facility_result:
            raise ValueError("Storage unit not found")
        
        facility_id = facility_result['facility_id']
        
        # Insert the reading
        insert_query = """
            INSERT INTO temperature_readings (
                customer_id, facility_id, storage_unit_id, temperature, temperature_unit,
                recorded_at, sensor_id, quality_score, equipment_status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
            RETURNING id, created_at
        """
        
        result = await db.fetchrow(
            insert_query,
            str(customer_id),
            str(facility_id),
            str(reading_data.storage_unit_id),
            reading_data.temperature,
            reading_data.temperature_unit,
            reading_data.recorded_at,
            reading_data.sensor_id,
            reading_data.quality_score,
            reading_data.equipment_status
        )
        
        # Create a complete reading object for the response
        reading = {
            **reading_data.dict(),
            "id": result['id'],
            "customer_id": customer_id,
            "facility_id": facility_id,
            "created_at": result['created_at']
        }
        
        return reading
    
    @classmethod
    async def get_statistics(cls, customer_id: UUID, start_date=None, end_date=None, facility_id=None, storage_unit_id=None):
        """
        Get temperature statistics for a customer.
        """
        # Build the query
        sql_query = """
            SELECT 
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(temperature) as avg_temperature,
                COUNT(*) as reading_count,
                COUNT(CASE WHEN equipment_status = 'normal' THEN 1 END) as normal_count,
                COUNT(CASE WHEN equipment_status = 'warning' THEN 1 END) as warning_count,
                COUNT(CASE WHEN equipment_status = 'error' THEN 1 END) as error_count,
                MIN(recorded_at) as time_range_start,
                MAX(recorded_at) as time_range_end,
                COUNT(DISTINCT storage_unit_id) as unit_count,
                MODE() WITHIN GROUP (ORDER BY temperature_unit) as temperature_unit
            FROM temperature_readings
            WHERE customer_id = $1
        """
        
        params = [str(customer_id)]
        param_count = 2
        
        if facility_id:
            sql_query += f" AND facility_id = ${param_count}"
            params.append(str(facility_id))
            param_count += 1
        
        if storage_unit_id:
            sql_query += f" AND storage_unit_id = ${param_count}"
            params.append(str(storage_unit_id))
            param_count += 1
            
        if start_date:
            sql_query += f" AND recorded_at >= ${param_count}"
            params.append(start_date)
            param_count += 1
            
        if end_date:
            sql_query += f" AND recorded_at <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        # Execute the query
        stats = await db.fetchrow(sql_query, *params)
        
        return stats

    @classmethod
    async def get_aggregation(cls, customer_id: UUID, aggregation_params):
        """
        Get aggregated temperature data.
        """
        valid_group_by = ['hour', 'day', 'week', 'month', 'facility', 'unit', 'sensor']
        valid_aggregations = ['avg', 'min', 'max', 'count']
        
        # Validate parameters
        for group in aggregation_params.group_by:
            if group not in valid_group_by:
                raise ValueError(f"Invalid group_by parameter: {group}. Valid values are {valid_group_by}")
                
        for agg in aggregation_params.aggregations:
            if agg not in valid_aggregations:
                raise ValueError(f"Invalid aggregation parameter: {agg}. Valid values are {valid_aggregations}")
        
        # Build the query
        select_clause = []
        group_by_clause = []
        
        # Add group by expressions
        for group in aggregation_params.group_by:
            if group == 'hour':
                select_clause.append("DATE_TRUNC('hour', recorded_at) as hour")
                group_by_clause.append("DATE_TRUNC('hour', recorded_at)")
            elif group == 'day':
                select_clause.append("DATE_TRUNC('day', recorded_at) as day")
                group_by_clause.append("DATE_TRUNC('day', recorded_at)")
            elif group == 'week':
                select_clause.append("DATE_TRUNC('week', recorded_at) as week")
                group_by_clause.append("DATE_TRUNC('week', recorded_at)")
            elif group == 'month':
                select_clause.append("DATE_TRUNC('month', recorded_at) as month")
                group_by_clause.append("DATE_TRUNC('month', recorded_at)")
            elif group == 'facility':
                select_clause.append("tr.facility_id, f.name as facility_name")
                group_by_clause.extend(["tr.facility_id", "f.name"])
            elif group == 'unit':
                select_clause.append("tr.storage_unit_id, su.name as unit_name")
                group_by_clause.extend(["tr.storage_unit_id", "su.name"])
            elif group == 'sensor':
                select_clause.append("tr.sensor_id")
                group_by_clause.append("tr.sensor_id")
        
        # Add aggregation expressions
        for agg in aggregation_params.aggregations:
            if agg == 'avg':
                select_clause.append("AVG(tr.temperature) as avg_temperature")
            elif agg == 'min':
                select_clause.append("MIN(tr.temperature) as min_temperature")
            elif agg == 'max':
                select_clause.append("MAX(tr.temperature) as max_temperature")
            elif agg == 'count':
                select_clause.append("COUNT(*) as reading_count")
        
        # Build the final query
        sql_query = f"""
            SELECT {', '.join(select_clause)}
            FROM temperature_readings tr
            JOIN facilities f ON tr.facility_id = f.id
            JOIN storage_units su ON tr.storage_unit_id = su.id
            WHERE tr.customer_id = $1
        """
        
        params = [str(customer_id)]
        param_count = 2
        
        if aggregation_params.facility_id:
            sql_query += f" AND tr.facility_id = ${param_count}"
            params.append(str(aggregation_params.facility_id))
            param_count += 1
        
        if aggregation_params.storage_unit_id:
            sql_query += f" AND tr.storage_unit_id = ${param_count}"
            params.append(str(aggregation_params.storage_unit_id))
            param_count += 1
            
        if aggregation_params.start_date:
            sql_query += f" AND tr.recorded_at >= ${param_count}"
            params.append(aggregation_params.start_date)
            param_count += 1
            
        if aggregation_params.end_date:
            sql_query += f" AND tr.recorded_at <= ${param_count}"
            params.append(aggregation_params.end_date)
            param_count += 1
        
        # Add group by clause
        if group_by_clause:
            sql_query += f" GROUP BY {', '.join(group_by_clause)}"
        
        if any(g in aggregation_params.group_by for g in ['hour', 'day', 'week', 'month']):
            for g in ['hour', 'day', 'week', 'month']:
                if g in aggregation_params.group_by:
                    sql_query += f" ORDER BY {g}"
                    break
        
        # Execute the query
        results = await db.fetch(sql_query, *params)
        
        # Transform results into the expected format
        aggregated_results = []
        for row in results:
            group_key = {}
            metrics = {}
            
            # Extract group keys
            for group in aggregation_params.group_by:
                if group == 'hour':
                    group_key['hour'] = row.get('hour')
                elif group == 'day':
                    group_key['day'] = row.get('day')
                elif group == 'week':
                    group_key['week'] = row.get('week')
                elif group == 'month':
                    group_key['month'] = row.get('month')
                elif group == 'facility':
                    group_key['facility_id'] = row.get('facility_id')
                    group_key['facility_name'] = row.get('facility_name')
                elif group == 'unit':
                    group_key['storage_unit_id'] = row.get('storage_unit_id')
                    group_key['unit_name'] = row.get('unit_name')
                elif group == 'sensor':
                    group_key['sensor_id'] = row.get('sensor_id')
            
            # Extract metrics
            for agg in aggregation_params.aggregations:
                if agg == 'avg':
                    metrics['avg_temperature'] = row.get('avg_temperature')
                elif agg == 'min':
                    metrics['min_temperature'] = row.get('min_temperature')
                elif agg == 'max':
                    metrics['max_temperature'] = row.get('max_temperature')
                elif agg == 'count':
                    metrics['reading_count'] = row.get('reading_count')
            
            aggregated_results.append({
                'group_key': group_key,
                'metrics': metrics
            })
        
        return aggregated_results