# tests/unit/simulation/test_customer_generator.py
import pytest
from unittest.mock import patch, MagicMock
from simulation.customer_generator import CustomerGenerator, GeneratedCustomer, GeneratedFacility, GeneratedUnit
from simulation.profile_templates import CUSTOMER_TEMPLATES, CustomerTemplate, DataSharingMethod

class TestCustomerGenerator:
    
    @pytest.fixture
    def customer_generator(self):
        return CustomerGenerator()
    
    def test_generate_customer_with_template_name(self, customer_generator):
        """Test generating customer with template name."""
        customer = customer_generator.generate_customer("TEST_001", template_name="pharmaceutical")
        
        assert customer.id == "TEST_001"
        assert customer.data_sharing_method == "api"
        assert len(customer.facilities) >= 1
        assert len(customer.facilities) <= 2
        assert "Pharma Corp TEST_001" in customer.name
    
    def test_generate_customer_with_custom_template(self, customer_generator):
        """Test generating customer with custom template."""
        custom_template = CUSTOMER_TEMPLATES["food_storage"]
        customer = customer_generator.generate_customer("TEST_002", custom_template=custom_template)
        
        assert customer.id == "TEST_002"
        assert customer.data_sharing_method == "csv"
        assert "Food Storage Ltd TEST_002" in customer.name
    
    def test_generate_assignment_customer_a(self, customer_generator):
        """Test generating exact assignment customer A."""
        customer = customer_generator.generate_assignment_customer("A")
        
        assert customer.id == "A"
        assert customer.name == "Customer A"
        assert customer.data_sharing_method == "csv"
        assert len(customer.facilities) == 1
        
        facility = customer.facilities[0]
        assert facility.id == "facility_a_1"
        assert facility.name is None
        assert facility.city is None
        assert facility.country == "England"
        assert len(facility.units) == 1
        
        unit = facility.units[0]
        assert unit.id == "unit_a_1"
        assert unit.name is None
        assert unit.size == 930
        assert unit.size_unit == "sqm"
        assert unit.set_temperature == -20
        assert unit.temperature_unit == "C"
    
    def test_generate_assignment_customer_b(self, customer_generator):
        """Test generating exact assignment customer B."""
        customer = customer_generator.generate_assignment_customer("B")
        
        assert customer.id == "B"
        assert customer.name == "Customer B"
        assert customer.data_sharing_method == "api"
        assert len(customer.facilities) == 1
        
        facility = customer.facilities[0]
        assert facility.id == "facility_b_1"
        assert facility.city == "Manchester"
        assert facility.country == "England"
        assert len(facility.units) == 3
        
        unit_names = [unit.name for unit in facility.units]
        assert "Deep Freeze 1" in unit_names
        assert "Chilled Room 1" in unit_names
        assert "Chilled Room 2" in unit_names
    
    def test_generate_multiple_customers(self, customer_generator):
        """Test generating multiple customers."""
        customers = customer_generator.generate_multiple_customers(5)
        
        assert len(customers) == 5
        customer_ids = [c.id for c in customers]
        assert len(set(customer_ids)) == 5  # All unique IDs
        assert "A" in customer_ids
        assert "B" in customer_ids
    
    def test_get_customer(self, customer_generator):
        """Test retrieving generated customer."""
        customer = customer_generator.generate_customer("TEST_GET", template_name="pharmaceutical")
        retrieved = customer_generator.get_customer("TEST_GET")
        
        assert retrieved is not None
        assert retrieved.id == "TEST_GET"
        assert retrieved.name == customer.name
    
    def test_list_customers(self, customer_generator):
        """Test listing customer IDs."""
        customer_generator.generate_customer("TEST_1", template_name="pharmaceutical")
        customer_generator.generate_customer("TEST_2", template_name="food_storage")
        
        customer_ids = customer_generator.list_customers()
        assert "TEST_1" in customer_ids
        assert "TEST_2" in customer_ids
        assert len(customer_ids) == 2
    
    @patch('yaml.dump')
    @patch('builtins.open')
    def test_export_to_yaml(self, mock_open, mock_yaml_dump, customer_generator):
        """Test exporting customers to YAML."""
        customer_generator.generate_customer("TEST_EXPORT", template_name="pharmaceutical")
        
        customer_generator.export_to_yaml("test_export.yaml")
        
        mock_open.assert_called_once_with("test_export.yaml", 'w')
        mock_yaml_dump.assert_called_once()