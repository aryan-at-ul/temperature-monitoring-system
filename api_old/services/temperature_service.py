import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid

from database.connection import db
from api.models.customer import AuthenticatedCustomer
from api.models.temperature import (
    TemperatureReadingDetail, TemperatureQuery, 
    TemperatureStats, TemperatureAggregation,
    AggregationResult
)

logger = logging.getLogger(__name__)


class TemperatureService:
    """Service for temperature-related operations"""
    
    @staticmethod
    async def get_readings(
        customer: AuthenticatedCustomer,
        query: TemperatureQuery,
        facility_id: Optional[str] = None,
        storage_unit_id: Optional[str] = None
    ) -> Tuple[List[TemperatureReadingDetail], int]:
        """
        Get temperature readings for a customer
        
        Args:
            customer: Authenticated customer
            query: Query parameters
            facility_id: Optional facility ID filter
            storage_unit_id: Optional storage unit ID filter
            
        Returns:
            Tuple of (list of readings, total count)
        """
        # Build base query
        base_query = """
            SELECT 
                tr.id,
                tr.customer_id,
                tr.facility_id,
                tr.storage_unit_id,
                tr.temperature,
                tr.temperature_unit,
                tr.recorded_at,
                tr.sensor_id,
                tr.quality_score,
                tr.equipment_status,
                tr.created_at,
                f.facility_code,
                f.name as facility_name,
                f.city,
                f.country,
                su.unit_code,
                su.name as unit_name,
                su.equipment_type,
                su.set_temperature,
                (tr.temperature - su.set_temperature) as temperature_deviation
            FROM 
                public.temperature_readings tr
                JOIN public.facilities f ON tr.facility_id = f.id
                JOIN public.storage_units su ON tr.storage_unit_id = su.id
            WHERE 
                tr.customer_id = $1
        """
        
        count_query = """
            SELECT COUNT(*) 
            FROM 
                public.temperature_readings tr
                JOIN public.facilities f ON tr.facility_id = f.id
                JOIN public.storage_units su ON tr.storage_unit_id = su.id
            WHERE 
                tr.customer_id = $1
        """
        
        # Build where clause and parameters
        where_clauses = []
        params = [customer.customer_id]
        param_index = 2
        
        if facility_id:
            where_clauses.append(f"tr.facility_id = ${param_index}")
            params.append(facility_id)
            param_index += 1
            
        if storage_unit_id:
            where_clauses.append(f"tr.storage_unit_id = ${param_index}")
            params.append(storage_unit_id)
            param_index += 1
            
        if query.start_date:
            where_clauses.append(f"tr.recorded_at >= ${param_index}")
            params.append(query.start_date)
            param_index += 1
            
        if query.end_date:
            where_clauses.append(f"tr.recorded_at <= ${param_index}")
            params.append(query.end_date)
            param_index += 1
            
        if query.min_temperature is not None:
            where_clauses.append(f"tr.temperature >= ${param_index}")
            params.append(query.min_temperature)
            param_index += 1
            
        if query.max_temperature is not None:
            where_clauses.append(f"tr.temperature <= ${param_index}")
            params.append(query.max_temperature)
            param_index += 1
            
        if query.equipment_status:
            where_clauses.append(f"tr.equipment_status = ${param_index}")
            params.append(query.equipment_status)
            param_index += 1
            
        if query.min_quality_score is not None:
            where_clauses.append(f"tr.quality_score >= ${param_index}")
            params.append(query.min_quality_score)
            param_index += 1
            
        if query.sensor_id:
            where_clauses.append(f"tr.sensor_id = ${param_index}")
            params.append(query.sensor_id)
            param_index += 1
            
        if query.temperature_unit:
            where_clauses.append(f"tr.temperature_unit = ${param_index}")
            params.append(query.temperature_unit)
            param_index += 1
            
        # Add where clauses to queries
        if where_clauses:
            additional_clauses = " AND " + " AND ".join(where_clauses)
            base_query += additional_clauses
            count_query += additional_clauses
            
        # Add ordering and pagination
        base_query += " ORDER BY tr.recorded_at DESC LIMIT $" + str(param_index) + " OFFSET $" + str(param_index + 1)
        params.append(query.limit)
        params.append(query.offset)
        
        # Execute queries
        readings = await db.fetch(base_query, *params)
        count_result = await db.fetchval(count_query, *params[:-2])  # Exclude limit and offset
        
        # Convert to model instances
        reading_models = [
            TemperatureReadingDetail(
                id=r['id'],
                customer_id=r['customer_id'],
                facility_id=r['facility_id'],
                storage_unit_id=r['storage_unit_id'],
                temperature=r['temperature'],
                temperature_unit=r['temperature_unit'],
                recorded_at=r['recorded_at'],
                sensor_id=r['sensor_id'],
                quality_score=r['quality_score'],
                equipment_status=r['equipment_status'],
                created_at=r['created_at'],
                facility_code=r['facility_code'],
                facility_name=r['facility_name'],
                unit_code=r['unit_code'],
                unit_name=r['unit_name'],
                equipment_type=r['equipment_type'],
                set_temperature=r['set_temperature'],
                temperature_deviation=r['temperature_deviation'],
                city=r['city'],
                country=r['country']
            )
            for r in readings
        ]
        
        return reading_models, count_result

    @staticmethod
    async def get_admin_readings(
        query: TemperatureQuery,
        customer_id: Optional[str] = None,
        facility_id: Optional[str] = None,
        storage_unit_id: Optional[str] = None
    ) -> Tuple[List[TemperatureReadingDetail], int]:
        """
        Get temperature readings for admin (across all customers)
        
        Args:
            query: Query parameters
            customer_id: Optional customer ID filter
            facility_id: Optional facility ID filter
            storage_unit_id: Optional storage unit ID filter
            
        Returns:
            Tuple of (list of readings, total count)
        """
        # Build base query
        base_query = """
            SELECT 
                tr.id,
                tr.customer_id,
                tr.facility_id,
                tr.storage_unit_id,
                tr.temperature,
                tr.temperature_unit,
                tr.recorded_at,
                tr.sensor_id,
                tr.quality_score,
                tr.equipment_status,
                tr.created_at,
                f.facility_code,
                f.name as facility_name,
                f.city,
                f.country,
                su.unit_code,
                su.name as unit_name,
                su.equipment_type,
                su.set_temperature,
                (tr.temperature - su.set_temperature) as temperature_deviation,
                c.customer_code,
                c.name as customer_name
            FROM 
                public.temperature_readings tr
                JOIN public.facilities f ON tr.facility_id = f.id
                JOIN public.storage_units su ON tr.storage_unit_id = su.id
                JOIN public.customers c ON tr.customer_id = c.id
            WHERE 1=1
        """
        
        count_query = """
            SELECT COUNT(*) 
            FROM 
                public.temperature_readings tr
                JOIN public.facilities f ON tr.facility_id = f.id
                JOIN public.storage_units su ON tr.storage_unit_id = su.id
                JOIN public.customers c ON tr.customer_id = c.id
            WHERE 1=1
        """
        
        # Build where clause and parameters
        where_clauses = []
        params = []
        param_index = 1
        
        if customer_id:
            where_clauses.append(f"tr.customer_id = ${param_index}")
            params.append(customer_id)
            param_index += 1
            
        if facility_id:
            where_clauses.append(f"tr.facility_id = ${param_index}")
            params.append(facility_id)
            param_index += 1
            
        if storage_unit_id:
            where_clauses.append(f"tr.storage_unit_id = ${param_index}")
            params.append(storage_unit_id)
            param_index += 1
            
        if query.start_date:
            where_clauses.append(f"tr.recorded_at >= ${param_index}")
            params.append(query.start_date)
            param_index += 1
            
        if query.end_date:
            where_clauses.append(f"tr.recorded_at <= ${param_index}")
            params.append(query.end_date)
            param_index += 1
            
        if query.min_temperature is not None:
            where_clauses.append(f"tr.temperature >= ${param_index}")
            params.append(query.min_temperature)
            param_index += 1
            
        if query.max_temperature is not None:
            where_clauses.append(f"tr.temperature <= ${param_index}")
            params.append(query.max_temperature)
            param_index += 1
            
        if query.equipment_status:
            where_clauses.append(f"tr.equipment_status = ${param_index}")
            params.append(query.equipment_status)
            param_index += 1
            
        if query.min_quality_score is not None:
            where_clauses.append(f"tr.quality_score >= ${param_index}")
            params.append(query.min_quality_score)
            param_index += 1
            
        if query.sensor_id:
            where_clauses.append(f"tr.sensor_id = ${param_index}")
            params.append(query.sensor_id)
            param_index += 1
            
        if query.temperature_unit:
            where_clauses.append(f"tr.temperature_unit = ${param_index}")
            params.append(query.temperature_unit)
            param_index += 1
            
        # Add where clauses to queries
        if where_clauses:
            additional_clauses = " AND " + " AND ".join(where_clauses)
            base_query += additional_clauses
            count_query += additional_clauses
            
        # Add ordering and pagination
        base_query += " ORDER BY tr.recorded_at DESC LIMIT $" + str(param_index) + " OFFSET $" + str(param_index + 1)
        params.append(query.limit)
        params.append(query.offset)
        
        # Execute queries
        readings = await db.fetch(base_query, *params)
        count_result = await db.fetchval(count_query, *params[:-2])  # Exclude limit and offset
        
        # Convert to model instances
        reading_models = [
            TemperatureReadingDetail(
                id=r['id'],
                customer_id=r['customer_id'],
                facility_id=r['facility_id'],
                storage_unit_id=r['storage_unit_id'],
                temperature=r['temperature'],
                temperature_unit=r['temperature_unit'],
                recorded_at=r['recorded_at'],
                sensor_id=r['sensor_id'],
                quality_score=r['quality_score'],
                equipment_status=r['equipment_status'],
                created_at=r['created_at'],
                facility_code=r['facility_code'],
                facility_name=r['facility_name'],
                unit_code=r['unit_code'],
                unit_name=r['unit_name'],
                equipment_type=r['equipment_type'],
                set_temperature=r['set_temperature'],
                temperature_deviation=r['temperature_deviation'],
                city=r['city'],
                country=r['country']
            )
            for r in readings
        ]
        
        return reading_models, count_result
        
    @staticmethod
    async def get_statistics(
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        facility_id: Optional[str] = None,
        storage_unit_id: Optional[str] = None
    ) -> TemperatureStats:
        """
        Get temperature statistics for a customer
        
        Args:
            customer_id: Customer ID
            start_date: Optional start date
            end_date: Optional end date
            facility_id: Optional facility ID filter
            storage_unit_id: Optional storage unit ID filter
            
        Returns:
            Temperature statistics
        """
        # Build query
        query = """
            SELECT 
                COUNT(*) as count,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(temperature) as avg_temperature,
                STDDEV(temperature) as std_deviation,
                MAX(recorded_at) as latest_reading,
                SUM(CASE WHEN equipment_status = 'normal' THEN 1 ELSE 0 END) as normal_count,
                SUM(CASE WHEN equipment_status = 'warning' THEN 1 ELSE 0 END) as warning_count,
                SUM(CASE WHEN equipment_status = 'critical' THEN 1 ELSE 0 END) as critical_count
            FROM 
                public.temperature_readings
            WHERE 
                customer_id = $1
        """
        
        # Build parameters
        params = [customer_id]
        param_index = 2
        
        # Add additional filters
        where_clauses = []
        
        if facility_id:
            where_clauses.append(f"facility_id = ${param_index}")
            params.append(facility_id)
            param_index += 1
            
        if storage_unit_id:
            where_clauses.append(f"storage_unit_id = ${param_index}")
            params.append(storage_unit_id)
            param_index += 1
            
        if start_date:
            where_clauses.append(f"recorded_at >= ${param_index}")
            params.append(start_date)
            param_index += 1
            
        if end_date:
            where_clauses.append(f"recorded_at <= ${param_index}")
            params.append(end_date)
            param_index += 1
            
        # Add where clauses to query
        if where_clauses:
            query += " AND " + " AND ".join(where_clauses)
            
        # Execute query
        result = await db.fetchrow(query, *params)
        
        # Create stats model
        stats = TemperatureStats(
            count=result['count'],
            min_temperature=result['min_temperature'] if result['min_temperature'] is not None else 0,
            max_temperature=result['max_temperature'] if result['max_temperature'] is not None else 0,
            avg_temperature=result['avg_temperature'] if result['avg_temperature'] is not None else 0,
            std_deviation=result['std_deviation'],
            latest_reading=result['latest_reading'],
            normal_count=result['normal_count'],
            warning_count=result['warning_count'],
            critical_count=result['critical_count']
        )
        
        return stats
        
    @staticmethod
    async def get_aggregation(
        customer_id: str,
        aggregation: TemperatureAggregation
    ) -> List[AggregationResult]:
        """
        Get aggregated temperature data
        
        Args:
            customer_id: Customer ID
            aggregation: Aggregation parameters
            
        Returns:
            List of aggregation results
        """
        # Validate aggregation type
        valid_aggregations = ["avg", "min", "max", "count"]
        if aggregation.aggregation not in valid_aggregations:
            raise ValueError(f"Invalid aggregation type: {aggregation.aggregation}")
            
        # Validate group by
        valid_groups = ["hour", "day", "week", "month", "facility", "unit", "sensor"]
        if aggregation.group_by not in valid_groups:
            raise ValueError(f"Invalid group by: {aggregation.group_by}")
            
        # Build base query
        agg_function = aggregation.aggregation
        if agg_function == "avg":
            agg_function = "AVG(tr.temperature)"
        elif agg_function == "min":
            agg_function = "MIN(tr.temperature)"
        elif agg_function == "max":
            agg_function = "MAX(tr.temperature)"
        elif agg_function == "count":
            agg_function = "COUNT(*)"
            
        # Build group by clause
        group_by_clause = ""
        select_clause = ""
        
        if aggregation.group_by == "hour":
            group_by_clause = "DATE_TRUNC('hour', tr.recorded_at)"
            select_clause = "DATE_TRUNC('hour', tr.recorded_at) as group_value"
        elif aggregation.group_by == "day":
            group_by_clause = "DATE_TRUNC('day', tr.recorded_at)"
            select_clause = "DATE_TRUNC('day', tr.recorded_at) as group_value"
        elif aggregation.group_by == "week":
            group_by_clause = "DATE_TRUNC('week', tr.recorded_at)"
            select_clause = "DATE_TRUNC('week', tr.recorded_at) as group_value"
        elif aggregation.group_by == "month":
            group_by_clause = "DATE_TRUNC('month', tr.recorded_at)"
            select_clause = "DATE_TRUNC('month', tr.recorded_at) as group_value"
        elif aggregation.group_by == "facility":
            group_by_clause = "tr.facility_id"
            select_clause = "f.facility_code as group_value"
        elif aggregation.group_by == "unit":
            group_by_clause = "tr.storage_unit_id"
            select_clause = "su.unit_code as group_value"
        elif aggregation.group_by == "sensor":
            group_by_clause = "tr.sensor_id"
            select_clause = "tr.sensor_id as group_value"
            
        # Build query
        query = f"""
            SELECT 
                {select_clause},
                {agg_function} as value
            FROM 
                public.temperature_readings tr
                JOIN public.facilities f ON tr.facility_id = f.id
                JOIN public.storage_units su ON tr.storage_unit_id = su.id
            WHERE 
                tr.customer_id = $1
        """
        
        # Build parameters
        params = [customer_id]
        param_index = 2
        
        # Add additional filters
        where_clauses = []
        
        if aggregation.facility_id:
            where_clauses.append(f"tr.facility_id = ${param_index}")
            params.append(aggregation.facility_id)
            param_index += 1
            
        if aggregation.storage_unit_id:
            where_clauses.append(f"tr.storage_unit_id = ${param_index}")
            params.append(aggregation.storage_unit_id)
            param_index += 1
            
        if aggregation.sensor_id:
            where_clauses.append(f"tr.sensor_id = ${param_index}")
            params.append(aggregation.sensor_id)
            param_index += 1
            
        if aggregation.equipment_status:
            where_clauses.append(f"tr.equipment_status = ${param_index}")
            params.append(aggregation.equipment_status)
            param_index += 1
            
        if aggregation.start_date:
            where_clauses.append(f"tr.recorded_at >= ${param_index}")
            params.append(aggregation.start_date)
            param_index += 1
            
        if aggregation.end_date:
            where_clauses.append(f"tr.recorded_at <= ${param_index}")
            params.append(aggregation.end_date)
            param_index += 1
            
        # Add where clauses to query
        if where_clauses:
            query += " AND " + " AND ".join(where_clauses)
            
        # Add group by and order
        query += f" GROUP BY {group_by_clause} ORDER BY {group_by_clause}"
        
        # Execute query
        results = await db.fetch(query, *params)
        
        # Convert to model instances
        return [
            AggregationResult(
                group_value=r['group_value'],
                value=r['value']
            )
            for r in results
        ]