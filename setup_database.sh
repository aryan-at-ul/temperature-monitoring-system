# #!/bin/bash
# echo "🗄️ Setting up Temperature Monitoring Database"
# echo "=============================================="

# # Create database directory structure
# mkdir -p database/{models,migrations,repositories,tests}

# # Setup PostgreSQL (assuming it's installed)
# echo "📊 Creating database..."
# createdb temperature_monitoring 2>/dev/null || echo "Database may already exist"

# # Apply schema
# echo "🏗️ Applying database schema..."
# psql temperature_monitoring < database/schema.sql

# # Test basic queries
# echo "🧪 Testing database..."
# psql temperature_monitoring -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

# echo "✅ Database setup complete!"
# echo "📊 Ready to import simulated data"


#!/bin/bash
echo "🗄️ Setting up Temperature Monitoring Database"
echo "=============================================="

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found! Aborting."
    exit 1
fi

# Create folder structure (if needed)
mkdir -p database/{models,migrations,repositories,tests}

# Wait for DB to be ready (if using Docker)
echo "⏳ Checking if PostgreSQL is available..."
until psql "host=$DB_HOST port=$DB_PORT user=$POSTGRES_USER password=$POSTGRES_PASSWORD dbname=postgres" -c '\q' 2>/dev/null; do
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  sleep 2
done

# Create the database if it doesn't exist
echo "📊 Creating database..."
psql "host=$DB_HOST port=$DB_PORT user=$POSTGRES_USER password=$POSTGRES_PASSWORD dbname=postgres" \
  -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
  psql "host=$DB_HOST port=$DB_PORT user=$POSTGRES_USER password=$POSTGRES_PASSWORD dbname=postgres" \
  -c "CREATE DATABASE $POSTGRES_DB"

# Apply schema
echo "🏗️ Applying database schema..."
psql "host=$DB_HOST port=$DB_PORT user=$POSTGRES_USER password=$POSTGRES_PASSWORD dbname=$POSTGRES_DB" \
  -f database/schema.sql

# Test tables
echo "🧪 Testing database..."
psql "host=$DB_HOST port=$DB_PORT user=$POSTGRES_USER password=$POSTGRES_PASSWORD dbname=$POSTGRES_DB" \
  -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

echo "✅ Database setup complete!"
echo "📊 Ready to import simulated data"
