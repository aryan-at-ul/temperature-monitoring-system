# database/repositories/temperature_repository.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from database.connection import DatabaseConnection
from database.models import TemperatureReading

class TemperatureRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create_reading(self, reading: TemperatureReading) -> TemperatureReading:
        """Create a new temperature reading"""
        query = """
        INSERT INTO temperature_readings 
        (customer_id, facility_id, storage_unit_id, temperature, temperature_unit,
         recorded_at, sensor_id, quality_score, equipment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
        """
        result = self.db.execute_query(query, (
            reading.customer_id,
            reading.facility_id,
            reading.storage_unit_id,
            reading.temperature,
            reading.temperature_unit,
            reading.recorded_at,
            reading.sensor_id,
            reading.quality_score,
            reading.equipment_status
        ))
        
        reading.id = result[0]['id']
        reading.created_at = result[0]['created_at']
        return reading
    
    def bulk_create_readings(self, readings: List[TemperatureReading]) -> int:
        """Bulk insert temperature readings"""
        if not readings:
            return 0
        
        query = """
        INSERT INTO temperature_readings 
        (customer_id, facility_id, storage_unit_id, temperature, temperature_unit,
         recorded_at, sensor_id, quality_score, equipment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.db.connection.cursor() as cursor:
            for reading in readings:
                cursor.execute(query, (
                    reading.customer_id,
                    reading.facility_id,
                    reading.storage_unit_id,
                    reading.temperature,
                    reading.temperature_unit,
                    reading.recorded_at,
                    reading.sensor_id,
                    reading.quality_score,
                    reading.equipment_status
                ))
            
            self.db.connection.commit()
            return len(readings)
    
    # def get_latest_readings_by_customer(self, customer_code: str, limit: int = 100) -> List[TemperatureReading]:
    #     """Get latest temperature readings for a customer"""
    #     query = """
    #     SELECT tr.id, tr.customer_id, tr.facility_id, tr.storage_unit_id,
    #            tr.temperature, tr.temperature_unit, tr.recorded_at, tr.sensor_id,
    #            tr.quality_score, tr.equipment_status, tr.created_at
    #     FROM temperature_readings tr
    #     JOIN customers c ON tr.customer_id = c.id
    #     WHERE c.customer_code = %s
    #     ORDER BY tr.recorded_at DESC
    #     LIMIT %s
    #     """
    #     results = self.db.execute_query(query, (customer_code, limit))
        
    #     readings = []
    #     for row in results:
    #         reading = TemperatureReading(
    #             id=row['id'],
    #             customer_id=row['customer_id'],
    #             facility_id=row['facility_id'],
    #             storage_unit_id=row['storage_unit_id'],
    #             temperature=float(row['temperature']) if row['temperature'] is not None else None,
    #             temperature_unit=row['temperature_unit'],
    #             recorded_at=row['recorded_at'],
    #             sensor_id=row['sensor_id'],
    #             quality_score=float(row['quality_score']),
    #             equipment_status=row['equipment_status'],
    #             created_at=row['created_at']
    #         )
    #         readings.append(reading)
        
    #     return readings


    def get_latest_readings_by_customer(self, customer_code: str, limit: int = 100) -> List[TemperatureReading]:
        """Get latest temperature readings for a customer"""
        query = """
        SELECT tr.id, tr.customer_id, tr.facility_id, tr.storage_unit_id,
            tr.temperature, tr.temperature_unit, tr.recorded_at, tr.sensor_id,
            tr.quality_score, tr.equipment_status, tr.created_at
        FROM temperature_readings tr
        JOIN customers c ON tr.customer_id = c.id
        WHERE c.customer_code = %s
        ORDER BY tr.recorded_at DESC
        LIMIT %s
        """
        results = self.db.execute_query(query, (customer_code, limit))
        
        readings = []
        for row in results:
            reading = TemperatureReading(
                id=row['id'],
                customer_id=row['customer_id'],
                facility_id=row['facility_id'],
                storage_unit_id=row['storage_unit_id'],
                temperature=float(row['temperature']) if row['temperature'] is not None else None,
                temperature_unit=row['temperature_unit'],
                recorded_at=row['recorded_at'],
                sensor_id=row['sensor_id'],
                quality_score=int(row['quality_score']),  # Changed from float to int
                equipment_status=row['equipment_status'],
                created_at=row['created_at']
            )
            readings.append(reading)
        
        return readings


    
    # def get_readings_by_unit_and_timerange(self, 
    #                                      unit_id: UUID, 
    #                                      start_time: datetime, 
    #                                      end_time: datetime) -> List[TemperatureReading]:
    #     """Get readings for a specific unit within time range"""
    #     query = """
    #     SELECT id, customer_id, facility_id, storage_unit_id,
    #            temperature, temperature_unit, recorded_at, sensor_id,
    #            quality_score, equipment_status, created_at
    #     FROM temperature_readings
    #     WHERE storage_unit_id = %s 
    #     AND recorded_at BETWEEN %s AND %s
    #     ORDER BY recorded_at ASC
    #     """
    #     results = self.db.execute_query(query, (unit_id, start_time, end_time))
        
    #     readings = []
    #     for row in results:
    #         reading = TemperatureReading(
    #             id=row['id'],
    #             customer_id=row['customer_id'],
    #             facility_id=row['facility_id'],
    #             storage_unit_id=row['storage_unit_id'],
    #             temperature=float(row['temperature']) if row['temperature'] is not None else None,
    #             temperature_unit=row['temperature_unit'],
    #             recorded_at=row['recorded_at'],
    #             sensor_id=row['sensor_id'],
    #             quality_score=float(row['quality_score']),
    #             equipment_status=row['equipment_status'],
    #             created_at=row['created_at']
    #         )
    #         readings.append(reading)
        
    #     return readings
    

    def get_readings_by_unit_and_timerange(self, 
                                        unit_id: UUID, 
                                        start_time: datetime, 
                                        end_time: datetime) -> List[TemperatureReading]:
        """Get readings for a specific unit within time range"""
        query = """
        SELECT id, customer_id, facility_id, storage_unit_id,
            temperature, temperature_unit, recorded_at, sensor_id,
            quality_score, equipment_status, created_at
        FROM temperature_readings
        WHERE storage_unit_id = %s 
        AND recorded_at BETWEEN %s AND %s
        ORDER BY recorded_at ASC
        """
        results = self.db.execute_query(query, (unit_id, start_time, end_time))
        
        readings = []
        for row in results:
            reading = TemperatureReading(
                id=row['id'],
                customer_id=row['customer_id'],
                facility_id=row['facility_id'],
                storage_unit_id=row['storage_unit_id'],
                temperature=float(row['temperature']) if row['temperature'] is not None else None,
                temperature_unit=row['temperature_unit'],
                recorded_at=row['recorded_at'],
                sensor_id=row['sensor_id'],
                quality_score=int(row['quality_score']),  # Changed from float to int
                equipment_status=row['equipment_status'],
                created_at=row['created_at']
            )
            readings.append(reading)
        
        return readings



    def get_equipment_failures(self, customer_code: Optional[str] = None, 
                             hours: int = 24) -> List[Dict[str, Any]]:
        """Get equipment failures in the last N hours"""
        base_query = """
        SELECT tr.id, c.customer_code, c.name as customer_name,
               f.facility_code, f.name as facility_name,
               su.unit_code, su.name as unit_name,
               tr.recorded_at, tr.equipment_status
        FROM temperature_readings tr
        JOIN customers c ON tr.customer_id = c.id
        JOIN facilities f ON tr.facility_id = f.id
        JOIN storage_units su ON tr.storage_unit_id = su.id
        WHERE (tr.temperature IS NULL OR tr.equipment_status = 'failure')
        AND tr.recorded_at > %s
        """
        
        params = [datetime.utcnow() - timedelta(hours=hours)]
        
        if customer_code:
            base_query += " AND c.customer_code = %s"
            params.append(customer_code)
        
        base_query += " ORDER BY tr.recorded_at DESC"
        
        results = self.db.execute_query(base_query, tuple(params))
        
        failures = []
        for row in results:
            failure = {
                'reading_id': row['id'],
                'customer_code': row['customer_code'],
                'customer_name': row['customer_name'],
                'facility_code': row['facility_code'],
                'facility_name': row['facility_name'],
                'unit_code': row['unit_code'],
                'unit_name': row['unit_name'],
                'occurred_at': row['recorded_at'],
                'status': row['equipment_status']
            }
            failures.append(failure)
        
        return failures
    
    def get_temperature_statistics(self, customer_code: str, hours: int = 24) -> Dict[str, Any]:
        """Get temperature statistics for a customer"""
        query = """
        SELECT 
            COUNT(*) as total_readings,
            COUNT(CASE WHEN temperature IS NOT NULL THEN 1 END) as valid_readings,
            COUNT(CASE WHEN temperature IS NULL THEN 1 END) as failed_readings,
            AVG(CASE WHEN temperature IS NOT NULL THEN 
                convert_temperature(temperature, temperature_unit, 'C') END) as avg_temp_celsius,
            MIN(CASE WHEN temperature IS NOT NULL THEN 
                convert_temperature(temperature, temperature_unit, 'C') END) as min_temp_celsius,
            MAX(CASE WHEN temperature IS NOT NULL THEN 
                convert_temperature(temperature, temperature_unit, 'C') END) as max_temp_celsius,
            COUNT(DISTINCT storage_unit_id) as active_units
        FROM temperature_readings tr
        JOIN customers c ON tr.customer_id = c.id
        WHERE c.customer_code = %s
        AND tr.recorded_at > %s
        """
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        results = self.db.execute_query(query, (customer_code, start_time))
        
        if not results:
            return {}
        
        row = results[0]
        return {
            'total_readings': row['total_readings'],
            'valid_readings': row['valid_readings'],
            'failed_readings': row['failed_readings'],
            'failure_rate': (row['failed_readings'] / max(row['total_readings'], 1)) * 100,
            'avg_temperature_celsius': float(row['avg_temp_celsius']) if row['avg_temp_celsius'] else None,
            'min_temperature_celsius': float(row['min_temp_celsius']) if row['min_temp_celsius'] else None,
            'max_temperature_celsius': float(row['max_temp_celsius']) if row['max_temp_celsius'] else None,
            'active_units': row['active_units'],
            'period_hours': hours
        }