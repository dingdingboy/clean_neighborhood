#!/bin/bash
#
# Stop the running llama-server.
#

set -e

PID_FILE="/tmp/llama-server.pid"

if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping llama-server (PID: $PID)..."
        kill "$PID"
        rm -f "$PID_FILE"
        echo "Server stopped"
    else
        echo "Server not running (PID file exists but process not found)"
        rm -f "$PID_FILE"
    fi
else
    echo "No PID file found. Checking for llama-server processes..."
    PIDS=$(pgrep -f "llama-server" || true)
    if [[ -n "$PIDS" ]]; then
        echo "Found llama-server processes: $PIDS"
        echo "Killing processes..."
        echo "$PIDS" | xargs kill
        echo "Server stopped"
    else
        echo "No llama-server processes found"
    fi
fi
