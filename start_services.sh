#!/bin/bash
#
# Start all services for the Violation Reporter application
#

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

echo "=========================================="
echo "Starting Violation Reporter Services"
echo "=========================================="

# Kill any existing processes first
echo "Cleaning up existing processes..."
pkill -f "llama-server" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "celery" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 2

# Check Redis
echo "Checking Redis..."
if ! (redis-cli ping >/dev/null 2>&1 || nc -z localhost 6379 >/dev/null 2>&1); then
    echo "  Warning: Redis is not available at localhost:6379"
    echo "  Please start Redis:"
    echo "    docker run -d -p 6379:6379 --name redis redis:7-alpine"
    exit 1
fi
echo "  Redis is available"

cd backend

# Activate virtual environment
echo "Activating Python virtual environment..."
source venv/bin/activate

# Start the backend (which auto-starts the model server)
echo ""
echo "Starting Backend (port 8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "  Waiting for backend to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "  Backend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 60 ]; then
        echo "  Backend failed to start! Check /tmp/backend.log"
        exit 1
    fi
done

# Verify model server is running (started by backend)
echo "  Checking model server..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        echo "  Model server is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "  Warning: Model server may not be fully ready yet"
    fi
done

# Start Celery worker
echo ""
echo "Starting Celery Worker..."
PYTHONPATH="$APP_DIR/backend:$PYTHONPATH" celery -A celery_worker.celery_app worker -l info -c 2 -Q media,analysis,submission > /tmp/celery.log 2>&1 &
CELERY_PID=$!
echo "  Celery PID: $CELERY_PID"

cd ../frontend

# Start the frontend
echo ""
echo "Starting Frontend (port 3000)..."
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# Wait for frontend to be ready
echo "  Waiting for frontend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "  Frontend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "  Frontend failed to start! Check /tmp/frontend.log"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "All services started successfully!"
echo "=========================================="
echo ""
echo "Service URLs:"
echo "  Frontend:    http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo ""
echo "Process PIDs:"
echo "  Backend:     $BACKEND_PID"
echo "  Celery:      $CELERY_PID"
echo "  Frontend:    $FRONTEND_PID"
echo ""
echo "Log files:"
echo "  Backend:     /tmp/backend.log"
echo "  Celery:      /tmp/celery.log"
echo "  Frontend:    /tmp/frontend.log"
echo ""
echo "To stop all services:"
echo "  ./stop_services.sh"
echo ""
echo "=========================================="

# Save PIDs for stop script
echo "$BACKEND_PID" > /tmp/violation_reporter_pids.txt
echo "$CELERY_PID" >> /tmp/violation_reporter_pids.txt
echo "$FRONTEND_PID" >> /tmp/violation_reporter_pids.txt
