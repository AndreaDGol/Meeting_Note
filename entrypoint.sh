#!/bin/bash
set -e

# Get PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "🚀 Starting application on port $PORT..."

# Start uvicorn with the configured port
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"

