import random
import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from .customer_generator import GeneratedCustomer, GeneratedUnit, GeneratedFacility

@dataclass
class TemperatureReading:
    customer_id: str
    facility_id: str
    unit_id: str
    unit_name: Optional[str]
    temperature: Optional[float]  # Can be None for faulty readings
    temperature_unit: str
    timestamp: datetime
    sensor_id: str
    set_temperature: float
    size: int
    size_unit: str
    city: Optional[str]
    country: str
    quality_score: float  # 0-1, indicates reading reliability
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'customer_id': self.customer_id,
            'facility_id': self.facility_id,
            'unit_id': self.unit_id,
            'unit_name': self.unit_name,
            'temperature': self.temperature,
            'temperature_unit': self.temperature_unit,
            'timestamp': self.timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'set_temperature': self.set_temperature,
            'size': self.size,
            'size_unit': self.size_unit,
            'city': self.city,
            'country': self.country,
            'quality_score': self.quality_score
        }

class EnhancedTemperatureGenerator:
    def __init__(self):
        self.previous_temperatures = {}  # Track previous temps for momentum
        self.equipment_states = {}       # Track equipment state
        self.sensor_drift = {}          # Track sensor drift over time
        self.fault_states = {}          # Track ongoing faults
    
    def generate_reading(self, 
                        customer: GeneratedCustomer,
                        facility: GeneratedFacility,
                        unit: GeneratedUnit, 
                        timestamp: datetime) -> TemperatureReading:
        """Generate a realistic temperature reading with potential faults"""
        
        unit_key = f"{customer.id}_{facility.id}_{unit.id}"
        
        # Check for null reading based on equipment reliability
        null_prob = unit.data_quality.get('null_reading_probability', 0.001)
        if random.random() < null_prob:
            return self._create_null_reading(customer, facility, unit, timestamp)
        
        # Get previous temperature for momentum
        previous_temp = self.previous_temperatures.get(unit_key, unit.set_temperature)
        
        # Apply sensor drift over time
        drift_factor = unit.data_quality.get('sensor_drift_factor', 1.0)
        
        # Calculate realistic temperature
        new_temperature = self._calculate_temperature_with_faults(
            unit, previous_temp, timestamp, unit_key, drift_factor
        )
        
        # Store for next iteration
        self.previous_temperatures[unit_key] = new_temperature
        
        # Generate sensor ID with potential issues
        sensor_id = self._generate_sensor_id(unit, unit_key)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(unit, new_temperature, timestamp)
        
        # Apply timestamp jitter if configured
        jitter = unit.data_quality.get('timestamp_jitter_seconds', 0)
        if jitter > 0:
            timestamp += timedelta(seconds=random.randint(-jitter, jitter))
        
        return TemperatureReading(
            customer_id=customer.id,
            facility_id=facility.id,
            unit_id=unit.id,
            unit_name=unit.name,
            temperature=round(new_temperature, 2),
            temperature_unit=unit.temperature_unit,
            timestamp=timestamp,
            sensor_id=sensor_id,
            set_temperature=unit.set_temperature,
            size=unit.size,
            size_unit=unit.size_unit,
            city=facility.city,
            country=facility.country,
            quality_score=quality_score
        )
    
    def _create_null_reading(self, customer, facility, unit, timestamp) -> TemperatureReading:
        """Create a reading with null temperature (equipment failure)"""
        return TemperatureReading(
            customer_id=customer.id,
            facility_id=facility.id,
            unit_id=unit.id,
            unit_name=unit.name,
            temperature=None,  # Null reading
            temperature_unit=unit.temperature_unit,
            timestamp=timestamp,
            sensor_id=self._generate_sensor_id(unit, f"{customer.id}_{facility.id}_{unit.id}"),
            set_temperature=unit.set_temperature,
            size=unit.size,
            size_unit=unit.size_unit,
            city=facility.city,
            country=facility.country,
            quality_score=0.0  # Zero quality for null readings
        )
    
    def _calculate_temperature_with_faults(self, 
                                         unit: GeneratedUnit, 
                                         previous_temp: float, 
                                         timestamp: datetime,
                                         unit_key: str,
                                         drift_factor: float) -> float:
        """Calculate temperature with realistic faults and variations"""
        
        target_temp = unit.set_temperature
        size = unit.size
        
        # Convert size to consistent unit (sqm) for calculations
        if unit.size_unit == "sqft":
            size_sqm = size * 0.092903
        else:
            size_sqm = size
        
        # Thermal mass effect
        thermal_mass_factor = math.log(max(size_sqm, 1)) / 10
        
        # Equipment state management
        if unit_key not in self.equipment_states:
            self.equipment_states[unit_key] = {
                'cycle_position': random.uniform(0, 2 * math.pi),
                'efficiency': random.uniform(0.85, 0.98),
                'last_maintenance': timestamp - timedelta(days=random.randint(1, 365))
            }
        
        equipment = self.equipment_states[unit_key]
        
        # Equipment degradation over time
        days_since_maintenance = (timestamp - equipment['last_maintenance']).days
        degradation_factor = max(0.7, 1.0 - (days_since_maintenance / 365) * 0.2)
        
        # Equipment cycling
        cycle_period = random.uniform(1800, 3600)  # 30-60 minute cycles
        equipment['cycle_position'] += (2 * math.pi) / cycle_period
        cooling_power = equipment['efficiency'] * degradation_factor * (
            0.6 + 0.4 * (1 + math.sin(equipment['cycle_position'])) / 2
        )
        
        # Environmental factors
        ambient_temp = self._get_ambient_temperature(timestamp)
        heat_load = self._calculate_heat_load(size_sqm, timestamp)
        
        # Sensor drift (accumulates over time)
        if unit_key not in self.sensor_drift:
            self.sensor_drift[unit_key] = 0.0
        
        # Gradual sensor drift
        self.sensor_drift[unit_key] += random.gauss(0, 0.001) * drift_factor
        
        # Temperature physics
        temp_difference = previous_temp - target_temp
        ambient_drift = (ambient_temp - previous_temp) * 0.003 / thermal_mass_factor
        cooling_response = -temp_difference * cooling_power * 0.15
        heat_impact = heat_load / (size_sqm * 12)
        
        # Equipment and sensor noise
        equipment_noise = random.gauss(0, 0.08)
        sensor_noise = random.gauss(0, 0.03) + self.sensor_drift[unit_key]
        
        # Major equipment faults (rare)
        if random.random() < 0.0005:  # 0.05% chance
            fault_magnitude = random.uniform(5, 15)
            fault_direction = random.choice([-1, 1])
            equipment_noise += fault_magnitude * fault_direction
            
            # Track fault state
            self.fault_states[unit_key] = {
                'start_time': timestamp,
                'magnitude': fault_magnitude * fault_direction,
                'duration': random.randint(300, 3600)  # 5 minutes to 1 hour
            }
        
        # Apply ongoing faults
        if unit_key in self.fault_states:
            fault = self.fault_states[unit_key]
            if (timestamp - fault['start_time']).total_seconds() < fault['duration']:
                equipment_noise += fault['magnitude'] * random.uniform(0.7, 1.3)
            else:
                del self.fault_states[unit_key]
        
        # Calculate final temperature
        temperature_change = ambient_drift + cooling_response + heat_impact + equipment_noise
        new_temperature = previous_temp + temperature_change + sensor_noise
        
        # Realistic bounds based on equipment capabilities
        if unit.temperature_unit == 'F':
            min_bound = target_temp - 25
            max_bound = target_temp + 35
        else:
            min_bound = target_temp - 15
            max_bound = target_temp + 20
        
        return max(min_bound, min(max_bound, new_temperature))
    
    def _generate_sensor_id(self, unit: GeneratedUnit, unit_key: str) -> str:
        """Generate sensor ID with potential naming inconsistencies"""
        
        # Sometimes sensor IDs are inconsistent or missing
        if random.random() < 0.05:  # 5% chance of weird sensor ID
            return f"sensor_unknown_{random.randint(1, 999)}"
        
        sensor_num = random.randint(1, 4)
        
        if unit.name:
            # Use unit name in sensor ID
            clean_name = unit.name.lower().replace(' ', '_')
            return f"sensor_{clean_name}_{sensor_num}"
        else:
            # Use unit ID
            return f"sensor_{unit.id.split('_')[-1]}_{sensor_num}"
    
    def _calculate_quality_score(self, unit: GeneratedUnit, temperature: float, timestamp: datetime) -> float:
        """Calculate reading quality score based on various factors"""
        
        base_quality = 1.0
        
        # Equipment reliability impact (more deterministic)
        reliability = unit.data_quality.get('equipment_reliability', 'high')
        reliability_scores = {
            'high': 0.95,
            'medium': 0.85,
            'low': 0.75,
            'faulty': 0.65
        }
        base_quality *= reliability_scores.get(reliability, 0.85)
        
        # Temperature deviation impact
        deviation = abs(temperature - unit.set_temperature)
        if deviation > 10:
            base_quality *= 0.7
        elif deviation > 5:
            base_quality *= 0.85
        elif deviation > 2:
            base_quality *= 0.95
        
        # Add smaller random variation to reduce test flakiness
        quality_noise = random.uniform(-0.02, 0.02)  # Reduced from 0.05
        
        return max(0.0, min(1.0, base_quality + quality_noise))
    
    def _get_ambient_temperature(self, timestamp: datetime) -> float:
        """Calculate ambient temperature with seasonal and daily variations"""
        base_temp = 12.0  # UK average
        
        # Seasonal variation
        day_of_year = timestamp.timetuple().tm_yday
        seasonal = 8 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        
        # Daily variation
        daily = 4 * math.sin(2 * math.pi * (timestamp.hour - 6) / 24)
        
        # Weather variation
        weather = random.gauss(0, 3)
        
        return base_temp + seasonal + daily + weather
    
    def _calculate_heat_load(self, size_sqm: float, timestamp: datetime) -> float:
        """Calculate heat load based on facility usage"""
        base_load = size_sqm * 0.015
        
        # Business hours effect
        if 7 <= timestamp.hour <= 19:
            multiplier = 1.6
        elif 5 <= timestamp.hour <= 23:
            multiplier = 1.2
        else:
            multiplier = 0.7
        
        return base_load * multiplier * random.uniform(0.7, 1.3)

def generate_customer_data(customer: GeneratedCustomer, 
                          hours: int = 24,
                          start_time: datetime = None) -> List[TemperatureReading]:
    """Generate temperature data for a customer over specified time period
    
    Args:
        customer: Customer to generate data for
        hours: Number of hours of data to generate
        start_time: Start time for data generation (default: hours ago from now)
    
    Returns:
        List of TemperatureReading objects
    """
    
    generator = EnhancedTemperatureGenerator()
    readings = []
    
    if start_time is None:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
    else:
        end_time = start_time + timedelta(hours=hours)
    
    for facility in customer.facilities:
        for unit in facility.units:
            current_time = start_time
            
            while current_time <= end_time:
                reading = generator.generate_reading(customer, facility, unit, current_time)
                readings.append(reading)
                
                # Advance time based on unit's data frequency
                current_time += timedelta(seconds=unit.data_frequency)
    
    # Sort readings by timestamp
    readings.sort(key=lambda r: r.timestamp)
    
    return readings

def generate_customer_data_with_offset(customer: GeneratedCustomer, 
                                     hours: int, 
                                     days_offset: int) -> List[TemperatureReading]:
    """Generate customer data with time offset for historical simulation"""
    
    end_time = datetime.now() - timedelta(days=days_offset)
    start_time = end_time - timedelta(hours=hours)
    
    return generate_customer_data(customer, hours, start_time)