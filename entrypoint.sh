#!/bin/sh
set -e

# Ensure Python can see your NAS-mounted util folder
export PYTHONPATH=/app:$PYTHONPATH

# Wait for MariaDB using Python
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-3306}

echo "Waiting for MariaDB at $DB_HOST:$DB_PORT..."
python << END
import os, socket, time
host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", 3306))
while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            break
    except OSError:
        time.sleep(1)
END
echo "MariaDB is up, continuing..."

# Collect static files (no migrations)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn acnet.wsgi:application -c gunicorn.conf.py
