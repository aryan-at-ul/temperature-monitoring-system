# api/utils/converters.py
def convert_temperature_value(temp_value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between units"""
    if from_unit == to_unit:
        return temp_value
    
    # Convert to Celsius first
    if from_unit == 'F':
        temp_celsius = (temp_value - 32) * 5.0/9.0
    elif from_unit == 'K':
        temp_celsius = temp_value - 273.15
    else:  # 'C'
        temp_celsius = temp_value
    
    # Convert from Celsius to target unit
    if to_unit == 'F':
        return temp_celsius * 9.0/5.0 + 32
    elif to_unit == 'K':
        return temp_celsius + 273.15
    else:  # 'C'
        return temp_celsius