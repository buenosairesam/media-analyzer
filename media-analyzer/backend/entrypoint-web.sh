#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h ${DB_HOST:-postgres} -p ${DB_PORT:-5432} -U ${DB_USER:-media_user} -d ${DB_NAME:-media_analyzer}; do
    echo "Database is unavailable - sleeping"
    sleep 1
done
echo "Database is up - continuing"

# Run migrations if needed (readiness check pattern)
echo "Checking migrations..."
python manage.py migrate --check || {
    echo "Running database migrations..."
    python manage.py migrate --noinput
}

# Load initial data if needed
echo "Loading initial data..."
python manage.py loaddata ai_processing/fixtures/initial_data.json || echo "No fixtures to load"

# Start Django web server with uvicorn
echo "Starting Django web server with uvicorn..."
if [ "${DEBUG:-True}" = "1" ] || [ "${DEBUG:-True}" = "True" ] || [ "${DEBUG:-True}" = "true" ]; then
    echo "Development mode: enabling auto-reload"
    exec uvicorn media_analyzer.asgi:application --host 0.0.0.0 --port 8000 --reload
else
    echo "Production mode: no auto-reload"
    exec uvicorn media_analyzer.asgi:application --host 0.0.0.0 --port 8000
fi