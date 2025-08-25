#!/bin/bash
set -e

# Wait for database to be ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    while ! pg_isready -h ${DB_HOST:-postgres-service} -p ${DB_PORT:-5432} -U ${DB_USER:-media_user}; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is up - continuing"
}

# Run database migrations
run_migrations() {
    echo "Running database migrations..."
    python manage.py migrate --noinput
}

# Collect static files (for production)
collect_static() {
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
}

# Load initial data if needed
load_fixtures() {
    echo "Loading initial data..."
    python manage.py loaddata ai_processing/fixtures/initial_data.json || echo "No fixtures to load"
}

case "$1" in
    web)
        echo "Starting Django web server..."
        wait_for_db
        collect_static
        load_fixtures
        exec uvicorn media_analyzer.asgi:application --host 0.0.0.0 --port 8000 --reload
        ;;
    celery-worker)
        echo "Starting Celery worker..."
        wait_for_db
        # Pass through additional arguments (queues, hostname, etc.)
        shift  # Remove 'celery-worker' from $@
        exec celery -A media_analyzer worker -l info "$@"
        ;;
    celery-beat)
        echo "Starting Celery beat scheduler..."
        wait_for_db
        exec celery -A media_analyzer beat -l info
        ;;
    migrate)
        echo "Running migrations only..."
        wait_for_db
        run_migrations
        load_fixtures
        ;;
    shell)
        echo "Starting Django shell..."
        wait_for_db
        exec python manage.py shell
        ;;
    *)
        echo "Available commands: web, celery-worker, celery-beat, migrate, shell"
        echo "Usage: $0 {web|celery-worker|celery-beat|migrate|shell}"
        exit 1
        ;;
esac