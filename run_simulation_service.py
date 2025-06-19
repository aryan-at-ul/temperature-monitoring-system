#!/usr/bin/env python3
# run_simulation_service.py

import asyncio
import yaml
from pathlib import Path
import click

import sys
sys.path.append(str(Path(__file__).resolve().parent))

from simulation.customer_generator import reconstruct_customer_from_config
from simulation.manager import SimulationManager

def load_customers_from_config(config_path: str) -> list:
    """Loads and reconstructs customer objects from the YAML config."""
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"❌ Configuration file not found at {config_path}")
        print("   Please run 'python -m simulation.cli generate-customers' first.")
        return []

    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    customers_data = config_data.get('customers', {})
    if not customers_data:
        print("❌ No customers found in the configuration file.")
        return []
    
    customers = [reconstruct_customer_from_config(cid, cdata) for cid, cdata in customers_data.items()]
    return customers

@click.command()
@click.option('--config', '-c', default='simulation/config/generated_customers.yaml', help='Path to the customer configuration file.')
@click.option('--port-start', default=8001, help='Starting port number for the first customer API.')
def main(config, port_start):
    """
    Runs the full Temperature Monitoring Simulation Service.

    This master service launches a dedicated API server for every customer defined
    in the configuration file. API-type customers will serve JSON, and CSV-type
    customers will serve downloadable CSV files.

    This service runs continuously until you stop it with CTRL+C.
    """
    customers = load_customers_from_config(config)
    if not customers:
        return

    manager = SimulationManager(customers, port_start)
    
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(manager.start())
    except KeyboardInterrupt:
        print("\nCaught interrupt signal, shutting down.")
    finally:
        manager.stop()
        loop.close()
        print("Service shut down successfully.")

if __name__ == '__main__':
    main()