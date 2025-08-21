FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 92

ENTRYPOINT ["/app/entrypoint.sh"]

