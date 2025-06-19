
# Test if setup up and running
pytest simulation/tests/ -v

# Test availabel features
python -m simulation.cli --help

# Test customer generation
python -m simulation.cli generate-customers --count 5

# Test showing available templates
python -m simulation.cli list-templates