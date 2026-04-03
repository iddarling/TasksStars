#!/bin/bash

# Production start script for Render.com

echo "Initializing database..."
python -m app.db.init_db

echo "Starting FastAPI server with gunicorn..."
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT
