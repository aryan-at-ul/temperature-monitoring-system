import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from api.services.temperature_service import TemperatureService

class TestTemperatureService:
    
    @pytest.fixture
    def mock_query(self):
        """Mock query object."""
        query = MagicMock()
        query.start_date = None
        query.end_date = None
        query.min_temperature = None
        query.max_temperature = None
        query.equipment_status = None
        query.quality_score = None
        query.sensor_id = None
        query.limit = 100
        query.offset = 0
        return query
    
    @pytest.fixture
    def sample_customer(self):
        """Sample customer data."""
        return {'id': str(uuid4())}
    
    @pytest.mark.asyncio
    @patch('api.services.temperature_service.db')
    async def test_get_readings_basic(self, mock_db, sample_customer, mock_query):
        """Test basic get_readings functionality."""
        # Mock database responses with AsyncMock
        mock_readings = [
            {
                'id': 1,
                'temperature': -20.5,
                'recorded_at': datetime.now(),
                'facility_name': 'Test Facility',
                'unit_name': 'Test Unit'
            }
        ]
        mock_db.fetch = AsyncMock(return_value=mock_readings)
        mock_db.fetchrow = AsyncMock(return_value={'count': 1})
        
        readings, total = await TemperatureService.get_readings(
            sample_customer, mock_query
        )
        
        assert len(readings) == 1
        assert total == 1
        assert readings[0]['temperature'] == -20.5
        mock_db.fetch.assert_called_once()
        mock_db.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('api.services.temperature_service.db')
    async def test_get_readings_with_filters(self, mock_db, sample_customer, mock_query):
        """Test get_readings with various filters."""
        mock_query.start_date = datetime.now() - timedelta(days=1)
        mock_query.end_date = datetime.now()
        mock_query.min_temperature = -25.0
        mock_query.max_temperature = -15.0
        mock_query.equipment_status = "normal"
        
        mock_db.fetch = AsyncMock(return_value=[])
        mock_db.fetchrow = AsyncMock(return_value={'count': 0})
        
        readings, total = await TemperatureService.get_readings(
            sample_customer, mock_query, facility_id="facility_1"
        )
        
        assert readings == []
        assert total == 0
        # Verify the SQL query includes filters
        call_args = mock_db.fetch.call_args[0]
        sql_query = call_args[0]
        assert "recorded_at >=" in sql_query
        assert "recorded_at <=" in sql_query
        assert "temperature >=" in sql_query
        assert "temperature <=" in sql_query
        assert "equipment_status =" in sql_query
        assert "facility_id =" in sql_query
    
    @pytest.mark.asyncio
    @patch('api.services.temperature_service.db')
    async def test_create_reading_success(self, mock_db, sample_temperature_data):
        """Test successful temperature reading creation."""
        customer_id = uuid4()
        
        # Mock database responses with AsyncMock
        mock_db.fetchrow = AsyncMock()
        mock_db.fetchrow.side_effect = [
            {'id': 'unit_123'},  # Unit exists
            {'facility_id': 'facility_123'},  # Facility lookup
            {'id': 1, 'created_at': datetime.now()}  # Insert result
        ]
        
        reading_data = MagicMock()
        reading_data.storage_unit_id = 'unit_123'
        reading_data.temperature = -20.5
        reading_data.temperature_unit = 'C'
        reading_data.recorded_at = datetime.now()
        reading_data.sensor_id = 'sensor_001'
        reading_data.quality_score = 1
        reading_data.equipment_status = 'normal'
        reading_data.dict.return_value = sample_temperature_data
        
        result = await TemperatureService.create_reading(customer_id, reading_data)
        
        assert result['id'] == 1
        assert result['customer_id'] == customer_id
        assert result['facility_id'] == 'facility_123'
        assert mock_db.fetchrow.call_count == 3
    
    @pytest.mark.asyncio
    @patch('api.services.temperature_service.db')
    async def test_create_reading_unit_not_found(self, mock_db):
        """Test creating reading with non-existent unit."""
        customer_id = uuid4()
        mock_db.fetchrow = AsyncMock(return_value=None)  # Unit not found
        
        reading_data = MagicMock()
        reading_data.storage_unit_id = 'nonexistent_unit'
        
        with pytest.raises(ValueError, match="Storage unit not found"):
            await TemperatureService.create_reading(customer_id, reading_data)
    
    @pytest.mark.asyncio
    @patch('api.services.temperature_service.db')
    async def test_get_statistics(self, mock_db, sample_customer):
        """Test getting temperature statistics."""
        customer_id = uuid4()
        
        mock_stats = {
            'min_temperature': -25.0,
            'max_temperature': -15.0,
            'avg_temperature': -20.0,
            'reading_count': 100,
            'normal_count': 95,
            'warning_count': 5,
            'error_count': 0,
            'time_range_start': datetime.now() - timedelta(hours=24),
            'time_range_end': datetime.now(),
            'unit_count': 5,
            'temperature_unit': 'C'
        }
        mock_db.fetchrow = AsyncMock(return_value=mock_stats)
        
        stats = await TemperatureService.get_statistics(customer_id)
        
        assert stats['min_temperature'] == -25.0
        assert stats['max_temperature'] == -15.0
        assert stats['avg_temperature'] == -20.0
        assert stats['reading_count'] == 100
        assert stats['unit_count'] == 5
    
    @pytest.mark.asyncio
    @patch('api.services.temperature_service.db')
    async def test_get_aggregation(self, mock_db):
        """Test temperature data aggregation."""
        customer_id = uuid4()
        
        aggregation_params = MagicMock()
        aggregation_params.group_by = ['day', 'facility']
        aggregation_params.aggregations = ['avg', 'count']
        aggregation_params.facility_id = None
        aggregation_params.storage_unit_id = None
        aggregation_params.start_date = datetime.now() - timedelta(days=7)
        aggregation_params.end_date = datetime.now()
        
        mock_results = [
            {
                'day': datetime.now().date(),
                'facility_id': 'facility_1',
                'facility_name': 'Test Facility',
                'avg_temperature': -20.0,
                'reading_count': 50
            }
        ]
        mock_db.fetch = AsyncMock(return_value=mock_results)
        
        results = await TemperatureService.get_aggregation(customer_id, aggregation_params)
        
        assert len(results) == 1
        assert 'group_key' in results[0]
        assert 'metrics' in results[0]
        assert results[0]['group_key']['facility_id'] == 'facility_1'
        assert results[0]['metrics']['avg_temperature'] == -20.0
