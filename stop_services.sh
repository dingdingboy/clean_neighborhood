#!/bin/bash
#
# Stop all Violation Reporter services
#

echo "=========================================="
echo "Stopping Violation Reporter Services"
echo "=========================================="

# Kill by PID files if available
if [ -f /tmp/violation_reporter_pids.txt ]; then
    echo "Stopping services by PID..."
    while read pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Stopping PID $pid..."
            kill "$pid" 2>/dev/null || true
        fi
    done < /tmp/violation_reporter_pids.txt
    rm -f /tmp/violation_reporter_pids.txt
fi

# Also kill by process name to be sure
echo "Cleaning up any remaining processes..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "celery" 2>/dev/null || true
pkill -f "llama-server" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

sleep 2

# Verify all services are stopped
RUNNING_COUNT=0
pgrep -f "uvicorn" >/dev/null 2>&1 && ((RUNNING_COUNT++))
pgrep -f "celery" >/dev/null 2>&1 && ((RUNNING_COUNT++))
pgrep -f "llama-server" >/dev/null 2>&1 && ((RUNNING_COUNT++))
pgrep -f "vite" >/dev/null 2>&1 && ((RUNNING_COUNT++))

if [ $RUNNING_COUNT -eq 0 ]; then
    echo "All services stopped successfully."
else
    echo "Warning: $RUNNING_COUNT service(s) may still be running."
    echo "You can force kill with: pkill -9 -f 'uvicorn|celery|llama-server|vite'"
fi

echo "=========================================="
