FROM python:3.12-slim

WORKDIR /app

# Install only essential dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    libmariadb-dev-compat \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Expose Gunicorn internal port (Nginx will proxy)
EXPOSE 92

# Use the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

