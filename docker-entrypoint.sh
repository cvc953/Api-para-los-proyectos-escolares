#!/bin/sh
set -e

# Wait for MySQL to be available (if using MySQL)
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-3306}

echo "Checking database availability at ${DB_HOST}:${DB_PORT}..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
  sleep 1
done

echo "Database is reachable, starting application"

# Start the app via uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
