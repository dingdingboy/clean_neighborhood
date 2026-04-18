#!/bin/bash
#
# Start llama-server with Qwen3.5-VL GGUF model for vision-language inference.
#
# Usage:
#   ./start_llama_server.sh [options]
#
# Options:
#   -d, --daemon    Run in background (daemon mode)
#   -p, --port      Port to listen on (default: 8080)
#   --cpu-only      Force CPU-only mode (no GPU offloading)
#
# Environment variables:
#   LLAMA_MODEL_PATH    - Path to GGUF model file
#   LLAMA_MMPROJ_PATH   - Path to multimodal projector file
#   LLAMA_CLI_PATH      - Path to llama.cpp binaries
#

set -e

# Default configuration
DEFAULT_MODEL_PATH="/home/aiguru/models/Qwen3.5-9B/Qwen3.5-9B-UD-Q4_K_XL.gguf"
DEFAULT_MMPROJ_PATH="/home/aiguru/models/Qwen3.5-9B/mmproj-BF16.gguf"
DEFAULT_CLI_PATH="$HOME/repo/llama.cpp/build/bin"
DEFAULT_PORT=8080

# Use environment variables if set, otherwise use defaults
MODEL_PATH="${LLAMA_MODEL_PATH:-$DEFAULT_MODEL_PATH}"
MMPROJ_PATH="${LLAMA_MMPROJ_PATH:-$DEFAULT_MMPROJ_PATH}"
CLI_PATH="${LLAMA_CLI_PATH:-$DEFAULT_CLI_PATH}"
PORT="${LLAMA_SERVER_PORT:-$DEFAULT_PORT}"

# Parse arguments
DAEMON_MODE=false
CPU_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --cpu-only)
            CPU_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -d, --daemon    Run in background (daemon mode)"
            echo "  -p, --port      Port to listen on (default: 8080)"
            echo "  --cpu-only      Force CPU-only mode (no GPU offloading)"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  LLAMA_MODEL_PATH    - Path to GGUF model file"
            echo "  LLAMA_MMPROJ_PATH   - Path to multimodal projector file"
            echo "  LLAMA_CLI_PATH      - Path to llama.cpp binaries"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Expand tilde in path
CLI_PATH="${CLI_PATH/#\~/$HOME}"

# Find the server binary
SERVER_BIN="$CLI_PATH/llama-server"

if [[ ! -f "$SERVER_BIN" ]]; then
    echo "Error: llama-server not found at $SERVER_BIN"
    echo "Please build llama.cpp or set LLAMA_CLI_PATH correctly"
    exit 1
fi

# Check model files exist
if [[ ! -f "$MODEL_PATH" ]]; then
    echo "Error: Model file not found: $MODEL_PATH"
    echo "Set LLAMA_MODEL_PATH to the correct GGUF file"
    exit 1
fi

if [[ ! -f "$MMPROJ_PATH" ]]; then
    echo "Error: Multimodal projector file not found: $MMPROJ_PATH"
    echo "Set LLAMA_MMPROJ_PATH to the correct mmproj file"
    exit 1
fi

# GPU layers - 0 for CPU only, more for GPU offloading
if [[ "$CPU_ONLY" == true ]]; then
    NGL=0
    echo "Running in CPU-only mode"
else
    # Auto-detect GPU availability
    if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
        NGL=999  # Offload all layers to GPU
        echo "GPU detected - using GPU acceleration"
    else
        NGL=0
        echo "No GPU detected - running on CPU"
    fi
fi

echo "Starting llama-server..."
echo "  Model: $MODEL_PATH"
echo "  MMProj: $MMPROJ_PATH"
echo "  Port: $PORT"
echo "  GPU Layers: $NGL"
echo ""

# Build server arguments
SERVER_ARGS=(
    --model "$MODEL_PATH"
    --mmproj "$MMPROJ_PATH"
    --port "$PORT"
    --host "0.0.0.0"
    -ngl "$NGL"
    --ctx-size 32768
    --threads -1
    --batch-size 2048
    --ubatch-size 512
    --timeout 300
    -np 4
    --metrics
)

# Run server
if [[ "$DAEMON_MODE" == true ]]; then
    echo "Running in daemon mode..."
    nohup "$SERVER_BIN" "${SERVER_ARGS[@]}" > /tmp/llama-server.log 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > /tmp/llama-server.pid
    echo "Server started with PID: $SERVER_PID"
    echo "Logs: /tmp/llama-server.log"
    echo ""
    echo "To stop the server:"
    echo "  kill \$(cat /tmp/llama-server.pid)"
else
    echo "Press Ctrl+C to stop the server"
    echo ""
    exec "$SERVER_BIN" "${SERVER_ARGS[@]}"
fi
