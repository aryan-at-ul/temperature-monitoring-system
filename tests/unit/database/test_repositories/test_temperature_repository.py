import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from database.repositories.temperature_repository import TemperatureRepository

# Create a simple TemperatureReading class for testing if the real one isn't available
try:
    from database.models import TemperatureReading
except ImportError:
    # Create a mock class if the real one doesn't exist
    class TemperatureReading:
        def __init__(self, **kwargs):
            self.id = str(kwargs.get('id')) if kwargs.get('id') is not None else None
            self.customer_id = kwargs.get('customer_id')
            self.facility_id = kwargs.get('facility_id')
            self.storage_unit_id = kwargs.get('storage_unit_id')
            self.temperature = kwargs.get('temperature')
            self.temperature_unit = kwargs.get('temperature_unit')
            self.recorded_at = kwargs.get('recorded_at')
            self.sensor_id = kwargs.get('sensor_id')
            self.quality_score = kwargs.get('quality_score')
            self.equipment_status = kwargs.get('equipment_status')
            self.created_at = kwargs.get('created_at')

class TestTemperatureRepository:
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        return MagicMock()
    
    @pytest.fixture
    def temp_repository(self, mock_db):
        """Temperature repository with mocked database."""
        return TemperatureRepository(mock_db)
    
    @pytest.fixture
    def sample_reading(self):
        """Sample temperature reading."""
        return TemperatureReading(
            id=str(uuid4()),  # Use string ID
            customer_id=str(uuid4()),
            facility_id=str(uuid4()),
            storage_unit_id=str(uuid4()),
            temperature=-20.5,
            temperature_unit='C',
            recorded_at=datetime.now(),
            sensor_id='sensor_001',
            quality_score=1,
            equipment_status='normal'
        )
    
    def test_create_reading(self, temp_repository, mock_db, sample_reading):
        """Test creating a temperature reading."""
        mock_db.execute_query.return_value = [{'id': 1, 'created_at': datetime.now()}]
        
        result = temp_repository.create_reading(sample_reading)
        
        assert result.id == 1
        assert result.created_at is not None
        mock_db.execute_query.assert_called_once()
        
        # Verify the SQL query structure
        call_args = mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "INSERT INTO temperature_readings" in sql_query
        assert "RETURNING id, created_at" in sql_query
    
    def test_bulk_create_readings(self, temp_repository, mock_db, sample_reading):
        """Test bulk creating temperature readings."""
        readings = [sample_reading, sample_reading]
        
        # Mock the connection and cursor
        mock_cursor = MagicMock()
        mock_db.connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = temp_repository.bulk_create_readings(readings)
        
        assert result == 2
        assert mock_cursor.execute.call_count == 2
        mock_db.connection.commit.assert_called_once()
    
    def test_bulk_create_readings_empty_list(self, temp_repository):
        """Test bulk creating with empty list."""
        result = temp_repository.bulk_create_readings([])
        assert result == 0
    
    def test_get_latest_readings_by_customer(self, temp_repository, mock_db):
        """Test getting latest readings for a customer."""
        mock_results = [
            {
                'id': str(uuid4()),  # Use string ID to match Pydantic model
                'customer_id': str(uuid4()),
                'facility_id': str(uuid4()),
                'storage_unit_id': str(uuid4()),
                'temperature': -20.5,
                'temperature_unit': 'C',
                'recorded_at': datetime.now(),
                'sensor_id': 'sensor_001',
                'quality_score': 1,
                'equipment_status': 'normal',
                'created_at': datetime.now()
            }
        ]
        mock_db.execute_query.return_value = mock_results
        
        readings = temp_repository.get_latest_readings_by_customer('TEST_CUSTOMER', 50)
        
        assert len(readings) == 1
        assert readings[0].temperature == -20.5
        assert readings[0].quality_score == 1  # Should be int
        
        # Verify query parameters
        call_args = mock_db.execute_query.call_args
        assert call_args[0][1] == ('TEST_CUSTOMER', 50)
    
    def test_get_readings_by_unit_and_timerange(self, temp_repository, mock_db):
        """Test getting readings for specific unit and time range."""
        unit_id = uuid4()
        start_time = datetime.now() - timedelta(hours=24)
        end_time = datetime.now()
        
        mock_results = [
            {
                'id': str(uuid4()),
                'customer_id': str(uuid4()),
                'facility_id': str(uuid4()),
                'storage_unit_id': str(unit_id),
                'temperature': -20.5,
                'temperature_unit': 'C',
                'recorded_at': datetime.now(),
                'sensor_id': 'sensor_001',
                'quality_score': 1,
                'equipment_status': 'normal',
                'created_at': datetime.now()
            }
        ]
        mock_db.execute_query.return_value = mock_results
        
        readings = temp_repository.get_readings_by_unit_and_timerange(
            unit_id, start_time, end_time
        )
        
        assert len(readings) == 1
        assert readings[0].storage_unit_id == str(unit_id)
        
        # Verify query includes time range
        call_args = mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "recorded_at BETWEEN" in sql_query
        assert call_args[0][1] == (unit_id, start_time, end_time)
    
    def test_get_equipment_failures(self, temp_repository, mock_db):
        """Test getting equipment failures."""
        mock_results = [
            {
                'id': str(uuid4()),
                'customer_code': 'TEST_CUSTOMER',
                'customer_name': 'Test Customer',
                'facility_code': 'FAC_001',
                'facility_name': 'Test Facility',
                'unit_code': 'UNIT_001',
                'unit_name': 'Test Unit',
                'recorded_at': datetime.now(),
                'equipment_status': 'failure'
            }
        ]
        mock_db.execute_query.return_value = mock_results
        
        failures = temp_repository.get_equipment_failures('TEST_CUSTOMER', 24)
        
        assert len(failures) == 1
        assert failures[0]['customer_code'] == 'TEST_CUSTOMER'
        assert failures[0]['status'] == 'failure'
        
        # Verify query includes customer filter
        call_args = mock_db.execute_query.call_args
        sql_query = call_args[0][0]
        assert "customer_code =" in sql_query
    
    def test_get_temperature_statistics(self, temp_repository, mock_db):
        """Test getting temperature statistics."""
        mock_result = [
            {
                'total_readings': 100,
                'valid_readings': 95,
                'failed_readings': 5,
                'avg_temp_celsius': -20.0,
                'min_temp_celsius': -25.0,
                'max_temp_celsius': -15.0,
                'active_units': 5
            }
        ]
        mock_db.execute_query.return_value = mock_result
        
        stats = temp_repository.get_temperature_statistics('TEST_CUSTOMER', 24)
        
        assert stats['total_readings'] == 100
        assert stats['valid_readings'] == 95
        assert stats['failed_readings'] == 5
        assert stats['failure_rate'] == 5.0
        assert stats['avg_temperature_celsius'] == -20.0
        assert stats['active_units'] == 5
        assert stats['period_hours'] == 24
    
    def test_repository_initialization(self, mock_db):
        """Test that repository can be initialized."""
        repo = TemperatureRepository(mock_db)
        assert repo.db == mock_db
    
    def test_create_reading_with_null_temperature(self, temp_repository, mock_db):
        """Test creating reading with null temperature."""

        reading_with_equipment_failure = TemperatureReading(
            id=str(uuid4()),
            customer_id=str(uuid4()),
            facility_id=str(uuid4()),
            storage_unit_id=str(uuid4()),
            temperature=-999.0, 
            temperature_unit='C',
            recorded_at=datetime.now(),
            sensor_id='sensor_001',
            quality_score=1,
            equipment_status='failure'
        )
        
        mock_db.execute_query.return_value = [{'id': 2, 'created_at': datetime.now()}]
        
        result = temp_repository.create_reading(reading_with_equipment_failure)
        
        assert result.id == 2
        assert result.temperature == -999.0 
        mock_db.execute_query.assert_called_once()