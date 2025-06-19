# simulation/setup_dev.py
#!/usr/bin/env python3
"""
Development setup script for simulation module
"""
import os
import sys
from pathlib import Path

def setup_simulation_dev():
    """Setup development environment for simulation module"""
    
    # Create necessary directories
    directories = [
        'data/csv_files',
        'data/simulated', 
        'data/assignment',
        'simulation/config',
        'simulation/tests/__pycache__'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create empty __init__.py files if they don't exist
    init_files = [
        'simulation/__init__.py',
        'simulation/tests/__init__.py'
    ]
    
    for init_file in init_files:
        init_path = Path(init_file)
        if not init_path.exists():
            init_path.touch()
            print(f"✅ Created file: {init_file}")
    
    # Create sample configuration if it doesn't exist
    config_file = Path('simulation/config/templates.yaml')
    if not config_file.exists():
        print(f"⚠️  Please create {config_file} with template configurations")
    
    print("\n🎉 Simulation module development environment setup complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r simulation/requirements.txt")
    print("2. Run tests: pytest simulation/tests/")
    print("3. Generate sample data: python -m simulation.cli generate-customers --count 5")

if __name__ == '__main__':
    setup_simulation_dev()