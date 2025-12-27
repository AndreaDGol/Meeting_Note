#!/usr/bin/env bash
set -e

# Railway deployment trigger - Dec 27 2025
# Railway PORT handling - explicit variable expansion
if [ -z "$PORT" ]; then
    export PORT=8000
    echo "⚠️  PORT not set, using default: 8000"
else
    echo "✅ PORT detected: $PORT"
fi

echo "🚀 Starting uvicorn on 0.0.0.0:$PORT..."

# Start uvicorn with explicit port
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"

