# AI Backend - llama.cpp GGUF Integration

This backend uses llama.cpp with GGUF format models for vision-language inference.

## Architecture

```
┌─────────────────┐     HTTP API      ┌──────────────────┐
│  FastAPI App    │ ─────────────────>│  llama-server    │
│  Celery Worker  │   OpenAI-compatible│  (Qwen3.5-VL)    │
└─────────────────┘                   └──────────────────┘
                                              │
                                              │ GGUF Model
                                              ▼
                                    ┌──────────────────────┐
                                    │  Qwen3.5-9B-UD-Q4_K  │
                                    │  mmproj-BF16.gguf    │
                                    └──────────────────────┘
```

## Model Files

- **Base Model**: `/home/aiguru/models/Qwen3.5-9B/Qwen3.5-9B-UD-Q4_K_XL.gguf`
- **MMProj**: `/home/aiguru/models/Qwen3.5-9B/mmproj-BF16.gguf`

The MMProj file is the multimodal projector that enables vision understanding.

## Running llama-server

### Option 1: Using the startup script (recommended for local development)

```bash
# Start the server
./scripts/start_llama_server.sh

# Start in background (daemon mode)
./scripts/start_llama_server.sh --daemon

# Use specific port
./scripts/start_llama_server.sh --port 8081

# CPU-only mode
./scripts/start_llama_server.sh --cpu-only
```

### Option 2: Using Docker Compose

```bash
# Start all services including llama-server
docker-compose up -d

# View llama-server logs
docker-compose logs -f llama-server
```

### Option 3: Direct execution

```bash
cd ~/repo/llama.cpp/build/bin

./llama-server \
  --model /home/aiguru/models/Qwen3.5-9B/Qwen3.5-9B-UD-Q4_K_XL.gguf \
  --mmproj /home/aiguru/models/Qwen3.5-9B/mmproj-BF16.gguf \
  --port 8080 \
  --ctx-size 8192 \
  -ngl 0
```

## Configuration

Environment variables in `app/config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLAMA_MODEL_PATH` | `/home/aiguru/models/Qwen3.5-9B/...` | Path to GGUF model |
| `LLAMA_MMPROJ_PATH` | `/home/aiguru/models/Qwen3.5-9B/...` | Path to mmproj file |
| `LLAMA_CLI_PATH` | `~/repo/llama.cpp/build/bin` | llama.cpp binaries |
| `LLAMA_SERVER_URL` | `http://localhost:8080` | Server endpoint |
| `LLAMA_CONTEXT_SIZE` | `8192` | Context window size |
| `LLAMA_THREADS` | `-1` | CPU threads (-1 = auto) |

## API Usage

The `LlamaCppAnalyzer` class communicates with llama-server using the OpenAI-compatible API:

```python
from ai.vlm_engine import LlamaCppAnalyzer

async with LlamaCppAnalyzer() as analyzer:
    result = await analyzer.analyze(
        image_paths=["photo.jpg"],
        text_context="User description here"
    )
    print(result.to_dict())
```

## Health Check

```bash
# Check if server is running
curl http://localhost:8080/health

# View server metrics
curl http://localhost:8080/metrics
```

## Performance Tuning

### CPU Optimization
- Increase `--threads` to match CPU cores
- Use `--batch-size 2048` for higher throughput
- Consider quantization: Q4_K_XL is a good balance

### GPU Acceleration (if available)
```bash
# Offload all layers to GPU
./llama-server ... -ngl 999

# Or set in docker-compose.yml
environment:
  - LLAMA_ARG_N_GPU_LAYERS=999
```

### Memory Usage
- Q4_K_XL ~6GB RAM for 9B model
- Add ~500MB for mmproj
- Add context buffer (ctx-size * 2MB per 1K tokens)

## Troubleshooting

### Server won't start
- Check model files exist: `ls -la /home/aiguru/models/Qwen3.5-9B/`
- Verify binaries: `~/repo/llama.cpp/build/bin/llama-server --version`
- Check port availability: `lsof -i :8080`

### Out of memory
- Reduce `--ctx-size` (e.g., 4096 instead of 8192)
- Use smaller quantization (Q4_K_M instead of Q4_K_XL)
- Reduce `--batch-size`

### Analysis timeouts
- Increase timeout in `vlm_engine.py` (default 120s)
- Check server logs for errors
- Verify image files aren't too large (resizing is automatic)
