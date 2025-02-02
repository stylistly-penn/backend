#!/bin/sh
# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Wait for the database to be ready
until pg_isready -h "$POSTGRES_HOST" -p 5432; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Make migrations for each app
python manage.py makemigrations items
python manage.py makemigrations relationships
python manage.py makemigrations season
python manage.py makemigrations color
python manage.py makemigrations brands
python manage.py makemigrations accounts

# Run migrations
python manage.py migrate

# Create test user
python manage.py create_test_user

# Start the server with hot reloading
exec poetry run watchmedo auto-restart --directory=api --pattern=*.py --recursive -- python manage.py runserver 0.0.0.0:8000
