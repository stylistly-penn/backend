#!/bin/sh
# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Change to the app directory where pyproject.toml is located
cd /app

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

# Create season objects
python manage.py create_seasons

# Start the server with hot reloading
exec watchmedo auto-restart --directory=api --pattern=*.py --recursive -- python manage.py runserver 0.0.0.0:8000
