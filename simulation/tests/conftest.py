# simulation/tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_customers():
    """Create sample customers for testing"""
    from simulation.customer_generator import CustomerGenerator  # Absolute import for tests
    
    generator = CustomerGenerator()
    
    customers = {
        'pharma': generator.generate_customer('PHARMA_TEST', 'pharmaceutical'),
        'food': generator.generate_customer('FOOD_TEST', 'food_storage'),
        'small': generator.generate_customer('SMALL_TEST', 'small_business'),
        'industrial': generator.generate_customer('IND_TEST', 'industrial'),
        'assignment_a': generator.generate_assignment_customer('A'),
        'assignment_b': generator.generate_assignment_customer('B')
    }
    
    return customers

@pytest.fixture
def sample_readings():
    """Generate sample temperature readings for testing"""
    from simulation.enhanced_data_generator import generate_customer_data  # Absolute import for tests
    from simulation.customer_generator import CustomerGenerator  # Absolute import for tests
    
    generator = CustomerGenerator()
    customer = generator.generate_customer('TEST', 'pharmaceutical')
    
    return generate_customer_data(customer, hours=2)