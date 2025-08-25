#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h ${DB_HOST:-postgres} -p ${DB_PORT:-5432} -U ${DB_USER:-media_user} -d ${DB_NAME:-media_analyzer}; do
    echo "Database is unavailable - sleeping"
    sleep 1
done
echo "Database is up - continuing"

# Start Celery worker
echo "Starting Celery worker..."
exec celery -A media_analyzer worker -l info "$@"