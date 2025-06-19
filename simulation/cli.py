# simulation/cli.py
import click
import yaml
import json
from pathlib import Path
from typing import List

# from .customer_generator import CustomerGenerator, CUSTOMER_TEMPLATES
from .customer_generator import CustomerGenerator, CUSTOMER_TEMPLATES, GeneratedCustomer, reconstruct_customer_from_config
from .enhanced_data_generator import generate_customer_data
from .csv_generator import CSVGenerator
from .api_simulator import CustomerAPISimulator, MultiCustomerAPIManager  # Fixed import names

@click.group()
def cli():
    """Temperature Monitoring Customer Simulation CLI"""
    pass

@cli.command()
@click.option('--count', '-n', default=5, help='Number of customers to generate')
@click.option('--output', '-o', default='simulation/config/generated_customers.yaml', 
              help='Output file for customer configurations')
@click.option('--template-distribution', '-d', 
              help='JSON string defining template distribution (e.g., \'{"pharmaceutical": 0.2, "food_storage": 0.5}\')')
def generate_customers(count, output, template_distribution):
    """Generate customer profiles from templates"""
    
    generator = CustomerGenerator()
    
    # Parse template distribution if provided
    distribution = None
    if template_distribution:
        try:
            distribution = json.loads(template_distribution)
        except json.JSONDecodeError:
            click.echo("❌ Invalid JSON for template distribution")
            return
    
    # Generate customers
    customers = generator.generate_multiple_customers(count, distribution)
    
    # Export to YAML
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    generator.export_to_yaml(output)
    
    # Print summary
    click.echo(f"✅ Generated {len(customers)} customers")
    click.echo(f"📁 Saved to: {output}")
    
    # Show customer summary
    for customer in customers:
        total_units = sum(len(f.units) for f in customer.facilities)
        click.echo(f"   {customer.id}: {customer.name} ({customer.data_sharing_method}) - {total_units} units")

@cli.command()
@click.option('--customer-id', '-c', required=True, help='Customer ID to generate data for')
@click.option('--template', '-t', type=click.Choice(list(CUSTOMER_TEMPLATES.keys())), 
              help='Template to use for customer generation')
@click.option('--hours', '-h', default=24, help='Hours of data to generate')
@click.option('--output-dir', '-o', default='data/generated', help='Output directory')
@click.option('--format', '-f', type=click.Choice(['csv', 'json', 'both']), default='csv',
              help='Output format')
def generate_data(customer_id, template, hours, output_dir, format):
    """Generate temperature data for a specific customer"""
    
    # Generate customer profile
    generator = CustomerGenerator()
    customer = generator.generate_customer(customer_id, template)
    
    click.echo(f"🏢 Generated customer profile for {customer.name}")
    click.echo(f"   📡 Data method: {customer.data_sharing_method}")
    
    total_units = sum(len(f.units) for f in customer.facilities)
    click.echo(f"   🌡️  Total units: {total_units}")
    
    # Generate temperature data
    click.echo(f"📊 Generating {hours}h of temperature data...")
    readings = generate_customer_data(customer, hours)
    
    click.echo(f"✅ Generated {len(readings)} temperature readings")
    
    # Show some statistics
    null_readings = sum(1 for r in readings if r.temperature is None)
    if null_readings > 0:
        click.echo(f"⚠️  {null_readings} null readings ({null_readings/len(readings)*100:.1f}%)")
    
    # Show temperature ranges per unit
    unit_stats = {}
    for reading in readings:
        if reading.temperature is not None:
            if reading.unit_id not in unit_stats:
                unit_stats[reading.unit_id] = {
                    'temps': [],
                    'unit_name': reading.unit_name or reading.unit_id,
                    'target': reading.set_temperature,
                    'unit': reading.temperature_unit
                }
            unit_stats[reading.unit_id]['temps'].append(reading.temperature)
    
    for unit_id, stats in unit_stats.items():
        temps = stats['temps']
        avg_temp = sum(temps) / len(temps)
        min_temp = min(temps)
        max_temp = max(temps)
        deviation = abs(avg_temp - stats['target'])
        
        click.echo(f"   📊 {stats['unit_name']}: {avg_temp:.1f}°{stats['unit']} "
                  f"(target: {stats['target']}°{stats['unit']}, "
                  f"range: {min_temp:.1f}-{max_temp:.1f}, "
                  f"deviation: {deviation:.1f})")
    
    # Save data
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if format in ['csv', 'both']:
        save_csv_data(readings, customer, output_path)
    
    if format in ['json', 'both']:
        save_json_data(readings, customer, output_path)

@cli.command()
@click.option('--config', '-c', default='simulation/config/generated_customers.yaml',
              help='Customer configuration file')
@click.option('--customer-id', help='Specific customer ID (default: all CSV customers)')
@click.option('--hours', default=24, help='Hours of data per file')
@click.option('--files', default=1, help='Number of CSV files to generate')
@click.option('--output-dir', default='data/csv_files', help='Output directory')
def generate_csv(config, customer_id, hours, files, output_dir):
    """Generate CSV files for customers using CSV data sharing method"""
    
    # If no config file exists, generate some customers first
    if not Path(config).exists():
        click.echo(f"⚠️  Configuration file not found: {config}")
        click.echo("   Generating sample customers first...")
        
        generator = CustomerGenerator()
        customers = generator.generate_multiple_customers(3)
        generator.export_to_yaml(config)
        
    # Load customer configurations
    with open(config, 'r') as f:
        config_data = yaml.safe_load(f)
    
    customers = config_data.get('customers', {})
    
    # Filter customers
    if customer_id:
        if customer_id not in customers:
            click.echo(f"❌ Customer {customer_id} not found in configuration")
            return
        target_customers = {customer_id: customers[customer_id]}
    else:
        # Only CSV customers
        target_customers = {
            cid: cdata for cid, cdata in customers.items() 
            if cdata.get('data_sharing_method') == 'csv'
        }
    
    if not target_customers:
        click.echo("❌ No CSV customers found")
        return
    
    click.echo(f"📄 Generating CSV files for {len(target_customers)} customers")
    
    csv_gen = CSVGenerator(output_dir)
    
    for cust_id, cust_data in target_customers.items():
        click.echo(f"\n🏢 Processing {cust_data['name']} ({cust_id})")
        
        # Reconstruct customer object
        customer = reconstruct_customer_from_config(cust_id, cust_data)
        
        # Generate multiple files if requested
        for file_num in range(files):
            timestamp_offset = file_num * 24  # Each file represents a different day
            readings = generate_customer_data_with_offset(customer, hours, timestamp_offset)
            
            filename = csv_gen.save_customer_csv(cust_id, readings, f"file_{file_num+1}")
            click.echo(f"   📁 Generated: {filename} ({len(readings)} readings)")

@cli.command()
@click.option('--config', '-c', default='simulation/config/generated_customers.yaml',
              help='Customer configuration file')
@click.option('--customer-id', help='Specific customer ID (default: all API customers)')
@click.option('--port-start', default=8001, help='Starting port number')
def start_api_servers(config, customer_id, port_start):
    """Start API servers for customers using API data sharing method"""
    
    # If no config file exists, generate some customers first
    if not Path(config).exists():
        click.echo(f"⚠️  Configuration file not found: {config}")
        click.echo("   Generating sample customers first...")
        
        generator = CustomerGenerator()
        customers = generator.generate_multiple_customers(3)
        generator.export_to_yaml(config)
    
    # Load customer configurations  
    with open(config, 'r') as f:
        config_data = yaml.safe_load(f)
    
    customers = config_data.get('customers', {})
    
    # Filter customers
    if customer_id:
        if customer_id not in customers:
            click.echo(f"❌ Customer {customer_id} not found")
            return
        target_customers = {customer_id: customers[customer_id]}
    else:
        # Only API customers
        target_customers = {
            cid: cdata for cid, cdata in customers.items() 
            if cdata.get('data_sharing_method') == 'api'
        }
    
    if not target_customers:
        click.echo("❌ No API customers found")
        return
    
    click.echo(f"🔗 Found {len(target_customers)} API customers")
    click.echo("📋 API servers would start on:")
    
    # Show what would start (actual implementation would use multiprocessing)
    for i, (cust_id, cust_data) in enumerate(target_customers.items()):
        port = port_start + i
        click.echo(f"   🚀 {cust_data['name']} ({cust_id}): http://localhost:{port}")
    
    click.echo("\n💡 To actually start servers, implement with asyncio/multiprocessing")

@cli.command()
def list_templates():
    """List available customer templates"""
    
    click.echo("📋 Available customer templates:")
    
    for template_name, template in CUSTOMER_TEMPLATES.items():
        click.echo(f"\n🏷️  {template_name}")
        click.echo(f"   📡 Data method: {template.data_sharing_method.value}")
        click.echo(f"   🏭 Facilities: {template.facilities_count_range[0]}-{template.facilities_count_range[1]}")
        click.echo(f"   🌡️  Units per facility: {template.facility_template.units_count_range[0]}-{template.facility_template.units_count_range[1]}")
        click.echo(f"   📊 Temperature unit: {template.facility_template.unit_template.temperature_unit.value}")
        click.echo(f"   📏 Size unit: {template.facility_template.unit_template.size_unit.value}")
        
        reliability = template.facility_template.unit_template.data_quality.equipment_reliability.value
        null_prob = template.facility_template.unit_template.data_quality.null_reading_probability
        click.echo(f"   🔧 Reliability: {reliability} (null readings: {null_prob*100:.2f}%)")

@cli.command()
@click.option('--config', '-c', default='simulation/config/generated_customers.yaml')
def show_customers(config):
    """Show generated customer profiles"""
    
    if not Path(config).exists():
        click.echo(f"❌ Configuration file not found: {config}")
        click.echo("   Run 'generate-customers' first")
        return
    
    with open(config, 'r') as f:
        config_data = yaml.safe_load(f)
    
    customers = config_data.get('customers', {})
    
    if not customers:
        click.echo("❌ No customers found. Run 'generate-customers' first.")
        return
    
    click.echo(f"🏢 Generated Customers ({len(customers)} total):")
    
    for cust_id, cust_data in customers.items():
        click.echo(f"\n📊 {cust_id}: {cust_data['name']}")
        click.echo(f"   📡 Data method: {cust_data['data_sharing_method']}")
        
        total_units = sum(len(f['units']) for f in cust_data['facilities'])
        click.echo(f"   🌡️  Total units: {total_units}")
        
        # Show facilities and units
        for facility in cust_data['facilities']:
            fac_name = facility['name'] or '[Unnamed]'
            location = f"{facility['city'] or '[Unknown]'}, {facility['country']}"
            click.echo(f"   🏭 {fac_name} ({location})")
            
            for unit in facility['units']:
                unit_name = unit['name'] or '[Unnamed]'
                temp_info = f"{unit['set_temperature']}°{unit['temperature_unit']}"
                size_info = f"{unit['size']} {unit['size_unit']}"
                freq_info = f"every {unit['data_frequency']}s"
                
                click.echo(f"      🌡️  {unit_name}: {temp_info}, {size_info}, {freq_info}")

@cli.command()
@click.option('--customer', type=click.Choice(['A', 'B', 'both']), default='both')
@click.option('--hours', default=24, help='Hours of data to generate')
@click.option('--output-dir', default='data/assignment', help='Output directory')
def generate_assignment_data(customer, hours, output_dir):
    """Generate data for assignment customers A and B (exact specifications)"""
    
    generator = CustomerGenerator()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if customer in ['A', 'both']:
        click.echo("🏢 Generating Customer A (Assignment specifications)")
        customer_a = generator.generate_assignment_customer('A')
        
        # Generate CSV data for Customer A
        csv_gen = CSVGenerator(output_path / 'csv_files')
        readings_a = generate_customer_data(customer_a, hours)
        
        filename = csv_gen.save_customer_csv('A', readings_a, 'assignment')
        click.echo(f"   📄 Generated: {filename}")
        click.echo(f"   📊 Records: {len(readings_a)}")
        
        # Show sample data
        if readings_a:
            sample = readings_a[0]
            click.echo(f"   🔍 Sample: {sample.unit_name or '[null]'}, "
                      f"{sample.temperature}°{sample.temperature_unit}, "
                      f"{sample.city or '[null]'}")
    
    if customer in ['B', 'both']:
        click.echo("🏢 Generating Customer B (Assignment specifications)")
        customer_b = generator.generate_assignment_customer('B')
        
        # Generate data for Customer B
        readings_b = generate_customer_data(customer_b, hours)
        
        # Save as JSON (API-style)
        save_json_data(readings_b, customer_b, output_path)
        
        click.echo(f"   📊 Generated {len(readings_b)} readings")
        click.echo("   🔗 Customer B uses API method - data saved as JSON")
        click.echo("   📋 Units: Deep Freeze 1, Chilled Room 1, Chilled Room 2")

@cli.command()
def validate_assignment():
    """Validate that generated data matches assignment requirements"""
    
    generator = CustomerGenerator()
    
    click.echo("🔍 Validating assignment customer specifications...")
    
    # Generate and validate Customer A
    customer_a = generator.generate_assignment_customer('A')
    click.echo(f"\n✅ Customer A: {customer_a.name}")
    click.echo(f"   Data method: {customer_a.data_sharing_method}")
    click.echo(f"   Facilities: {len(customer_a.facilities)}")
    
    facility_a = customer_a.facilities[0]
    click.echo(f"   Facility name: {facility_a.name or '[null]'} ✓")
    click.echo(f"   City: {facility_a.city or '[null]'} ✓") 
    click.echo(f"   Country: {facility_a.country} ✓")
    
    unit_a = facility_a.units[0]
    click.echo(f"   Unit name: {unit_a.name or '[null]'} ✓")
    click.echo(f"   Size: {unit_a.size} {unit_a.size_unit} ✓")
    click.echo(f"   Set temp: {unit_a.set_temperature}°{unit_a.temperature_unit} ✓")
    
    # Generate and validate Customer B
    customer_b = generator.generate_assignment_customer('B')
    click.echo(f"\n✅ Customer B: {customer_b.name}")
    click.echo(f"   Data method: {customer_b.data_sharing_method}")
    click.echo(f"   Facilities: {len(customer_b.facilities)}")
    
    facility_b = customer_b.facilities[0]
    click.echo(f"   Facility name: {facility_b.name or '[null]'}")
    click.echo(f"   City: {facility_b.city} ✓")
    click.echo(f"   Country: {facility_b.country} ✓")
    click.echo(f"   Units: {len(facility_b.units)} ✓")
    
    expected_units = [
        ("Deep Freeze 1", 50000, 0),
        ("Chilled Room 1", 10000, 0), 
        ("Chilled Room 2", 5000, 45)
    ]
    
    for i, (expected_name, expected_size, expected_temp) in enumerate(expected_units):
        unit = facility_b.units[i]
        click.echo(f"   Unit {i+1}: {unit.name} ✓")
        click.echo(f"     Size: {unit.size} {unit.size_unit} ✓")
        click.echo(f"     Set temp: {unit.set_temperature}°{unit.temperature_unit} ✓")
        
        # Validate values match assignment
        assert unit.name == expected_name
        assert unit.size == expected_size
        assert unit.set_temperature == expected_temp
        assert unit.size_unit == "sqft"
        assert unit.temperature_unit == "F"
    
    click.echo("\n🎉 All assignment requirements validated successfully!")

@cli.command()
@click.option('--customer', type=click.Choice(['A', 'B']), required=True)
@click.option('--hours', default=1, help='Hours of sample data')
def sample_data(customer, hours):
    """Generate sample data to preview"""
    
    generator = CustomerGenerator()
    
    click.echo(f"🔍 Generating {hours}h sample data for Customer {customer}...")
    
    if customer == 'A':
        customer_obj = generator.generate_assignment_customer('A')
    else:
        customer_obj = generator.generate_assignment_customer('B')
    
    readings = generate_customer_data(customer_obj, hours)
    
    click.echo(f"📊 Generated {len(readings)} readings")
    click.echo("\n📋 Sample readings:")
    
    for i, reading in enumerate(readings[:5]):  # Show first 5
        click.echo(f"   {i+1}. {reading.timestamp.strftime('%H:%M:%S')} - "
                  f"{reading.unit_name or reading.unit_id}: "
                  f"{reading.temperature:.1f}°{reading.temperature_unit} "
                  f"(target: {reading.set_temperature}°{reading.temperature_unit})")
    
    if len(readings) > 5:
        click.echo(f"   ... and {len(readings) - 5} more readings")

# Helper functions
def save_csv_data(readings: List, customer, output_path: Path):
    """Save readings as CSV"""
    import pandas as pd
    from datetime import datetime
    
    data = [reading.to_dict() for reading in readings]
    df = pd.DataFrame(data)
    
    # Handle null values appropriately
    df = df.where(pd.notnull(df), None)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"customer_{customer.id}_{timestamp}.csv"
    filepath = output_path / filename
    
    df.to_csv(filepath, index=False)
    click.echo(f"💾 Saved CSV: {filename}")

def save_json_data(readings: List, customer, output_path: Path):
    """Save readings as JSON"""
    from datetime import datetime
    
    data = {
        'customer_id': customer.id,
        'customer_name': customer.name,
        'data_sharing_method': customer.data_sharing_method,
        'generated_at': datetime.now().isoformat(),
        'readings': [reading.to_dict() for reading in readings]
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"customer_{customer.id}_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    click.echo(f"💾 Saved JSON: {filename}")

# def reconstruct_customer_from_config(customer_id: str, config_data: dict):
#     """Reconstruct customer object from YAML configuration"""
#     from .customer_generator import GeneratedCustomer, GeneratedFacility, GeneratedUnit
    
#     facilities = []
#     for fac_data in config_data['facilities']:
#         units = []
#         for unit_data in fac_data['units']:
#             unit = GeneratedUnit(
#                 id=unit_data['id'],
#                 name=unit_data['name'],
#                 size=unit_data['size'],
#                 size_unit=unit_data['size_unit'],
#                 set_temperature=unit_data['set_temperature'],
#                 temperature_unit=unit_data['temperature_unit'],
#                 data_frequency=unit_data['data_frequency'],
#                 data_quality=unit_data['data_quality'],
#                 facility_id=fac_data['id']
#             )
#             units.append(unit)
        
#         facility = GeneratedFacility(
#             id=fac_data['id'],
#             name=fac_data['name'],
#             city=fac_data['city'],
#             country=fac_data['country'],
#             units=units,
#             customer_id=customer_id
#         )
#         facilities.append(facility)
    
#     return GeneratedCustomer(
#         id=customer_id,
#         name=config_data['name'],
#         data_sharing_method=config_data['data_sharing_method'],
#         facilities=facilities,
#         data_config=config_data['data_config'],
#         data_quality=config_data['data_quality']
#     )

def generate_customer_data_with_offset(customer, hours: int, days_offset: int):
    """Generate customer data with time offset"""
    from datetime import datetime, timedelta
    from .enhanced_data_generator import generate_customer_data
    
    end_time = datetime.now() - timedelta(days=days_offset)
    start_time = end_time - timedelta(hours=hours)
    
    return generate_customer_data(customer, hours, start_time)

if __name__ == '__main__':
    cli()