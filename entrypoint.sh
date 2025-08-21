#!/bin/sh

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn on port 92
exec gunicorn acnet.wsgi:application -c gunicorn.conf.py

