#!/bin/bash

# Wait for database to be ready
echo "Waiting for postgres..."

# Using python to check connection since nc might be missing or different
python -c "
import socket
import time

while True:
    try:
        with socket.create_connection(('db', 5432), timeout=1):
            break
    except OSError:
        time.sleep(0.1)
"

echo "PostgreSQL started"

# Initialize database tables
echo "Initializing database..."
python -m app.db.init_db

# Start FastAPI server with reload
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
