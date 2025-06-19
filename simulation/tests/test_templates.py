# simulation/tests/test_templates.py
import pytest
from simulation.profile_templates import (  # Absolute import for tests
    CUSTOMER_TEMPLATES, 
    CustomerTemplate,
    DataQualityProfile,
    EquipmentReliability
)


class TestProfileTemplates:
    
    def test_all_templates_exist(self):
        """Test that all expected templates are defined"""
        expected_templates = ['pharmaceutical', 'food_storage', 'small_business', 'industrial']
        
        for template_name in expected_templates:
            assert template_name in CUSTOMER_TEMPLATES
            assert isinstance(CUSTOMER_TEMPLATES[template_name], CustomerTemplate)
    
    def test_template_data_sharing_methods(self):
        """Test that templates have appropriate data sharing methods"""
        # API customers
        api_templates = ['pharmaceutical', 'industrial']
        for template_name in api_templates:
            template = CUSTOMER_TEMPLATES[template_name]
            assert template.data_sharing_method.value == 'api'
        
        # CSV customers  
        csv_templates = ['food_storage', 'small_business']
        for template_name in csv_templates:
            template = CUSTOMER_TEMPLATES[template_name]
            assert template.data_sharing_method.value == 'csv'
    
    def test_template_reliability_levels(self):
        """Test that templates have appropriate reliability levels"""
        # High reliability
        high_rel = CUSTOMER_TEMPLATES['pharmaceutical']
        assert high_rel.global_data_quality.equipment_reliability == EquipmentReliability.HIGH
        
        # Medium reliability
        med_rel = CUSTOMER_TEMPLATES['food_storage']
        assert med_rel.global_data_quality.equipment_reliability == EquipmentReliability.MEDIUM
        
        # Low reliability
        low_rel = CUSTOMER_TEMPLATES['small_business']
        assert low_rel.global_data_quality.equipment_reliability == EquipmentReliability.LOW
    
    def test_template_null_probabilities(self):
        """Test that null probabilities are realistic"""
        for template_name, template in CUSTOMER_TEMPLATES.items():
            data_quality = template.facility_template.unit_template.data_quality
            
            # Null reading probability should be small
            assert 0 <= data_quality.null_reading_probability <= 0.02
            
            # Null name probability varies by customer type
            if template_name == 'small_business':
                assert data_quality.null_name_probability > 0.5  # Often missing names
            elif template_name == 'pharmaceutical':
                assert data_quality.null_name_probability == 0.0  # Always have names
    
    def test_template_size_ranges(self):
        """Test that size ranges are appropriate for customer types"""
        # Pharmaceutical - smaller, precise units
        pharma = CUSTOMER_TEMPLATES['pharmaceutical']
        pharma_size_range = pharma.facility_template.unit_template.size_range
        assert pharma_size_range[1] <= 500  # Max 500 sqm
        
        # Industrial - larger units
        industrial = CUSTOMER_TEMPLATES['industrial']
        industrial_size_range = industrial.facility_template.unit_template.size_range
        assert industrial_size_range[0] >= 5000  # Min 5000 sqft
    
    def test_template_temperature_ranges(self):
        """Test that temperature ranges make sense"""
        for template_name, template in CUSTOMER_TEMPLATES.items():
            temp_range = template.facility_template.unit_template.temperature_range
            
            # Range should be valid
            assert temp_range[0] <= temp_range[1]
            
            # Should be within realistic bounds
            if template.facility_template.unit_template.temperature_unit.value == 'C':
                assert temp_range[0] >= -85  # Ultra-low freezer limit
                assert temp_range[1] <= 60   # Upper reasonable limit
            else:  # Fahrenheit
                assert temp_range[0] >= -120
                assert temp_range[1] <= 140
    
    def test_template_data_frequencies(self):
        """Test that data frequencies are reasonable"""
        for template_name, template in CUSTOMER_TEMPLATES.items():
            freq_range = template.facility_template.unit_template.data_frequency_range
            
            # Frequency should be positive
            assert freq_range[0] > 0
            assert freq_range[1] >= freq_range[0]
            
            # Should be reasonable (1 minute to 30 minutes)
            assert freq_range[0] >= 60    # At least 1 minute
            assert freq_range[1] <= 1800  # At most 30 minutes
    
    def test_data_quality_profile_defaults(self):
        """Test DataQualityProfile default values"""
        profile = DataQualityProfile()
        
        assert profile.null_reading_probability == 0.001
        assert profile.null_name_probability == 0.0
        assert profile.null_location_probability == 0.0
        assert profile.sensor_drift_factor == 1.0
        assert profile.equipment_reliability == EquipmentReliability.HIGH
        assert profile.timestamp_jitter_seconds == 0
    
    def test_template_location_pools(self):
        """Test that location pools are appropriate"""
        for template_name, template in CUSTOMER_TEMPLATES.items():
            location_pool = template.facility_template.location_pool
            
            # Should have at least one location
            assert len(location_pool) > 0
            
            # All locations should have country
            for location in location_pool:
                assert 'country' in location
                assert location['country'] is not None
                
                # City can be null for some templates
                assert 'city' in location
    
    def test_equipment_reliability_enum(self):
        """Test EquipmentReliability enum values"""
        assert EquipmentReliability.HIGH.value == "high"
        assert EquipmentReliability.MEDIUM.value == "medium" 
        assert EquipmentReliability.LOW.value == "low"
        assert EquipmentReliability.FAULTY.value == "faulty"

if __name__ == '__main__':
    pytest.main([__file__])