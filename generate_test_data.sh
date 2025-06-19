#!/bin/bash
echo "🌡️ Temperature Monitoring System - Data Generation"
echo "================================================="

# Generate assignment customers A & B
echo -e "\n📋 Generating assignment customers A & B..."
python -m simulation.cli generate-assignment-data --customer both --hours 48

# Validate assignment requirements
echo -e "\n✅ Validating assignment requirements..."
python -m simulation.cli validate-assignment

# Generate CSV files for CSV customers
echo -e "\n📄 Generating CSV files (Customer A behavior)..."
python -m simulation.cli generate-csv --hours 24 --files 5

# Generate diverse sample data
echo -e "\n📊 Generating sample data for database design..."
python -m simulation.cli generate-data --customer-id PHARMA --template pharmaceutical --hours 12 --format csv
python -m simulation.cli generate-data --customer-id FOOD --template food_storage --hours 12 --format csv  
python -m simulation.cli generate-data --customer-id SMALL --template small_business --hours 12 --format csv
python -m simulation.cli generate-data --customer-id INDUST --template industrial --hours 12 --format csv

# Show what we generated
echo -e "\n🏢 Generated customers:"
python -m simulation.cli show-customers

# Examine the data
echo -e "\n📁 Generated files:"
find data/ -name "*.csv" -o -name "*.json" | wc -l | xargs echo "Total files:"
find data/ -name "*.csv" -o -name "*.json" | head -5

# Show sample CSV data
echo -e "\n📋 Sample CSV content (Customer A format):"
if ls data/assignment/csv_files/*.csv 1> /dev/null 2>&1; then
    echo "Assignment Customer A data:"
    head -3 $(ls data/assignment/csv_files/*.csv | head -1)
    echo "..."
    echo "Shows null values in unit_name and city columns ✓"
fi

if ls data/csv_files/*.csv 1> /dev/null 2>&1; then
    echo -e "\nGeneral CSV data:"
    head -3 $(ls data/csv_files/*.csv | head -1)
fi

# Check for edge cases
echo -e "\n🔍 Checking for realistic edge cases:"
if ls data/csv_files/*.csv 1> /dev/null 2>&1; then
    csv_file=$(ls data/csv_files/*.csv | head -1)
    echo "Null temperatures (equipment failures):"
    grep -c ",," "$csv_file" || echo "None found in this sample"
    
    echo "Temperature units used:"
    cut -d',' -f6 "$csv_file" | sort | uniq -c | head -3
    
    echo "Size units used:"
    cut -d',' -f11 "$csv_file" | sort | uniq -c
fi

echo -e "\n✅ Data generation complete!"
echo "📊 Ready for database design (Exercise 1)"
echo ""
echo "Next steps:"
echo "1. Design database schema for this diverse data"
echo "2. Handle different temperature units (C/F)"
echo "3. Handle different size units (sqm/sqft)"
echo "4. Handle null values in names and locations"
echo "5. Design for scalability with many customers"
