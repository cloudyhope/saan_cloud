#!/bin/sh
set -e

# Apply database migrations (idempotent), then replace the shell with the server so signals reach it.
echo "Apply database migrations"
python manage.py migrate --noinput

echo "Starting server"
exec gunicorn --bind 0.0.0.0:8000 core.wsgi:application \
    -w "${GUNICORN_WORKERS:-3}" --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - --error-logfile -
