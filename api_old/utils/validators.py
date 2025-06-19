# api/utils/validators.py
from typing import Optional
import re

def validate_customer_code(customer_code: str) -> bool:
    """Validate customer code format"""
    return bool(re.match(r'^[A-Z]$', customer_code))

def validate_facility_code(facility_code: str) -> bool:
    """Validate facility code format"""
    return bool(re.match(r'^facility_[A-Z]_\d+$', facility_code))

def validate_unit_code(unit_code: str) -> bool:
    """Validate unit code format"""
    return bool(re.match(r'^unit_[A-Z]_\d+_\d+$', unit_code))