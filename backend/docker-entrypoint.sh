#!/bin/sh

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Running tests
# echo "Running Tests"
# python manage.py test

# Start server
echo "Starting server"
# python manage.py runserver 0.0.0.0:8000
gunicorn --bind 0.0.0.0:8000 core.wsgi:application -w 6
