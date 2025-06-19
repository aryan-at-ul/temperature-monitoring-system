# tests/conftest.py
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

@pytest.fixture
def mock_db():
    """Mock database connection with async methods."""
    mock = MagicMock()
    mock.fetch = AsyncMock()
    mock.fetchrow = AsyncMock()
    mock.execute = AsyncMock()
    return mock

@pytest.fixture
def api_client():
    """Create FastAPI test client."""
    try:
        from api.main import app
        return TestClient(app)
    except ImportError:
        # If we can't import the app, return a mock
        return MagicMock()

@pytest.fixture
def sample_customer():
    """Sample customer data."""
    return {
        'id': str(uuid4()),
        'customer_code': 'TEST_CUSTOMER',
        'name': 'Test Customer',
        'api_url': 'http://localhost:8001/temperature/current',
        'data_method': 'api'
    }

@pytest.fixture
def sample_temperature_data():
    """Sample temperature reading data."""
    return {
        "customer_id": "A",
        "facility_id": "facility_A_1",
        "storage_unit_id": "unit_A_1_1",
        "temperature": -20.5,
        "temperature_unit": "C",
        "recorded_at": datetime.now(),
        "sensor_id": "sensor_001",
        "quality_score": 1,
        "equipment_status": "normal"
    }

@pytest.fixture
def api_tokens():
    """API tokens for testing."""
    return {
        "A": {
            "read_token": "read_A_65_token_2025",
            "write_token": "write_A_65_token_2025"
        },
        "B": {
            "read_token": "read_B_66_token_2025",
            "write_token": "write_B_66_token_2025"
        },
        "admin": {
            "admin_token": "admin_A_65_admin_token_2025"
        }
    }

@pytest.fixture
def auth_headers(api_tokens):
    """Authentication headers for API testing."""
    return {"Authorization": f"Bearer {api_tokens['A']['read_token']}"}