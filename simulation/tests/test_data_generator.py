# simulation/tests/test_data_generator.py
import pytest
from datetime import datetime, timedelta
from simulation.enhanced_data_generator import (  # Absolute import for tests
    EnhancedTemperatureGenerator, 
    generate_customer_data,
    TemperatureReading
)
from simulation.customer_generator import CustomerGenerator  # Absolute import for tests


class TestEnhancedTemperatureGenerator:
    
    def setup_method(self):
        """Setup for each test method"""
        self.generator = EnhancedTemperatureGenerator()
        self.customer_generator = CustomerGenerator()
    
    def test_generate_single_reading(self):
        """Test generating a single temperature reading"""
        customer = self.customer_generator.generate_customer('TEST', 'pharmaceutical')
        facility = customer.facilities[0]
        unit = facility.units[0]
        
        reading = self.generator.generate_reading(customer, facility, unit, datetime.now())
        
        assert isinstance(reading, TemperatureReading)
        assert reading.customer_id == customer.id
        assert reading.facility_id == facility.id
        assert reading.unit_id == unit.id
        assert reading.temperature_unit == unit.temperature_unit
        assert reading.set_temperature == unit.set_temperature
        assert 0 <= reading.quality_score <= 1
    
    def test_temperature_realistic_bounds(self):
        """Test that generated temperatures stay within realistic bounds"""
        customer = self.customer_generator.generate_customer('TEST', 'pharmaceutical')
        facility = customer.facilities[0]
        unit = facility.units[0]
        
        readings = []
        for i in range(100):
            timestamp = datetime.now() + timedelta(minutes=i)
            reading = self.generator.generate_reading(customer, facility, unit, timestamp)
            if reading.temperature is not None:
                readings.append(reading.temperature)
        
        # Should have some valid readings
        assert len(readings) > 50
        
        # Temperatures should be within reasonable bounds of set point
        set_temp = unit.set_temperature
        temp_range = 20 if unit.temperature_unit == 'C' else 35
        
        for temp in readings:
            assert set_temp - temp_range <= temp <= set_temp + temp_range
    
    def test_null_readings_probability(self):
        """Test that null readings occur at expected probability"""
        # Use small_business template which has higher null probability
        customer = self.customer_generator.generate_customer('TEST', 'small_business')
        facility = customer.facilities[0]
        unit = facility.units[0]
        
        null_count = 0
        total_count = 1000
        
        for i in range(total_count):
            timestamp = datetime.now() + timedelta(minutes=i)
            reading = self.generator.generate_reading(customer, facility, unit, timestamp)
            if reading.temperature is None:
                null_count += 1
        
        # Should have some null readings for low-reliability equipment
        expected_null_rate = unit.data_quality['null_reading_probability']
        actual_null_rate = null_count / total_count
        
        # Allow some variance in the probability
        assert abs(actual_null_rate - expected_null_rate) < 0.005
    
    def test_temperature_momentum(self):
        """Test that temperature changes show realistic momentum"""
        customer = self.customer_generator.generate_customer('TEST', 'food_storage')
        facility = customer.facilities[0]
        unit = facility.units[0]
        
        readings = []
        for i in range(10):
            timestamp = datetime.now() + timedelta(minutes=i * 5)
            reading = self.generator.generate_reading(customer, facility, unit, timestamp)
            if reading.temperature is not None:
                readings.append(reading.temperature)
        
        # Should have gradual changes, not wild jumps
        if len(readings) >= 3:
            changes = [abs(readings[i+1] - readings[i]) for i in range(len(readings)-1)]
            avg_change = sum(changes) / len(changes)
            
            # Average change should be relatively small
            assert avg_change < 2.0  # Less than 2 degrees average change
    

    def test_unit_specific_characteristics(self):
        """Test that different unit types have appropriate characteristics"""
        # Generate different customer types
        pharma = self.customer_generator.generate_customer('PHARMA', 'pharmaceutical')
        small_biz = self.customer_generator.generate_customer('SMALL', 'small_business')
        
        # Generate multiple readings to get average quality
        pharma_qualities = []
        small_qualities = []
        
        for i in range(10):  # Generate 10 readings each
            pharma_reading = self.generator.generate_reading(
                pharma, pharma.facilities[0], pharma.facilities[0].units[0], datetime.now()
            )
            small_reading = self.generator.generate_reading(
                small_biz, small_biz.facilities[0], small_biz.facilities[0].units[0], datetime.now()
            )
            
            pharma_qualities.append(pharma_reading.quality_score)
            small_qualities.append(small_reading.quality_score)
        
        # Compare average quality scores
        avg_pharma_quality = sum(pharma_qualities) / len(pharma_qualities)
        avg_small_quality = sum(small_qualities) / len(small_qualities)
        
        # Pharmaceutical should have higher average quality
        # Allow some tolerance since it's random
        assert avg_pharma_quality >= avg_small_quality - 0.1
        
        # Check equipment reliability settings
        pharma_unit = pharma.facilities[0].units[0]
        small_unit = small_biz.facilities[0].units[0]
        
        # Pharmaceutical should have higher reliability
        assert pharma_unit.data_quality['equipment_reliability'] == 'high'
        assert small_unit.data_quality['equipment_reliability'] == 'low'
    
    def test_generate_customer_data_function(self):
        """Test the main generate_customer_data function"""
        customer = self.customer_generator.generate_customer('TEST', 'industrial')
        
        readings = generate_customer_data(customer, hours=2)
        
        # Should have readings for all units
        expected_units = sum(len(f.units) for f in customer.facilities)
        unit_ids = set(r.unit_id for r in readings)
        
        assert len(unit_ids) == expected_units
        
        # Should have multiple readings per unit (2 hours of data)
        assert len(readings) > expected_units
        
        # Readings should be sorted by timestamp
        timestamps = [r.timestamp for r in readings]
        assert timestamps == sorted(timestamps)
    
    def test_reading_to_dict(self):
        """Test TemperatureReading to_dict method"""
        customer = self.customer_generator.generate_customer('TEST', 'pharmaceutical')
        facility = customer.facilities[0]
        unit = facility.units[0]
        
        reading = self.generator.generate_reading(customer, facility, unit, datetime.now())
        data_dict = reading.to_dict()
        
        # Check all required fields are present
        required_fields = [
            'customer_id', 'facility_id', 'unit_id', 'temperature', 
            'temperature_unit', 'timestamp', 'sensor_id', 'set_temperature',
            'size', 'size_unit', 'city', 'country', 'quality_score'
        ]
        
        for field in required_fields:
            assert field in data_dict
        
        # Check data types
        assert isinstance(data_dict['timestamp'], str)
        assert isinstance(data_dict['quality_score'], float)
    
    def test_sensor_id_generation(self):
        """Test that sensor IDs are generated appropriately"""
        customer = self.customer_generator.generate_customer('TEST', 'food_storage')
        facility = customer.facilities[0]
        unit = facility.units[0]
        
        sensor_ids = set()
        for i in range(50):
            timestamp = datetime.now() + timedelta(minutes=i)
            reading = self.generator.generate_reading(customer, facility, unit, timestamp)
            sensor_ids.add(reading.sensor_id)
        
        # Should have some variety in sensor IDs
        assert len(sensor_ids) >= 2
        
        # All should contain 'sensor'
        assert all('sensor' in sid for sid in sensor_ids)

if __name__ == '__main__':
    pytest.main([__file__])