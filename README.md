# Public Interest Violation Reporter

A full-stack application for reporting public interest violations using AI-powered image and video analysis. The system automatically detects harmful content, extracts geolocation, and files complaints with configured authorities.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   React     │────▶│   FastAPI    │────▶│     SQLite      │
│  Frontend   │◀────│   Backend    │◀────│   Database      │
└─────────────┘     └──────┬───────┘     └─────────────────┘
      │                    │
      │ WebSocket          │ Celery + Redis
      │                    ▼
      │            ┌─────────────────┐
      │            │  Celery Worker  │
      │            │  (Async Tasks)  │
      │            └────────┬────────┘
      │                     │
      │                     ▼
      │            ┌─────────────────┐
      │            │  llama-server   │
      │            │  Qwen3.5-VL     │
      │            │  (GGUF Model)   │
      │            └─────────────────┘
```

## Features

- **Multi-modal Media Upload**: Support for images, videos, audio, and text descriptions
- **AI-Powered Analysis**: Uses Qwen3.5 VL via llama.cpp with GGUF models to analyze content
- **Geolocation Extraction**: Extracts location from EXIF data and visual landmarks
- **Automated Complaint Filing**: Submits reports via hotline (mock) or web service endpoints
- **Real-time Status Updates**: WebSocket notifications for report progress
- **Configurable Offices**: Manage multiple offices and submission endpoints

## Prerequisites

- Python 3.11+
- Node.js 20+ (with npm)
- Redis 7+
- llama.cpp binaries with Qwen3.5-VL support
- GGUF model files (Qwen3.5-9B + mmproj)

## Quick Start

### Option 1: Using Start/Stop Scripts (Recommended for Local Development)

```bash
# Navigate to project directory
cd /home/aiguru/repo/clean_neighborhood

# Start all services
./start_services.sh

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# Stop all services
./stop_services.sh
```

### Option 2: Using Docker Compose

```bash
# Start all services including llama-server
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 3: Manual Setup (Full Control)

#### Step 1: Start Redis

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Or ensure Redis is running locally
redis-cli ping  # Should return PONG
```

#### Step 2: Model Server Setup

Ensure you have the GGUF model files:
- Model: `/home/aiguru/models/Qwen3.5-9B/Qwen3.5-9B-UD-Q4_K_XL.gguf`
- MMProj: `/home/aiguru/models/Qwen3.5-9B/mmproj-BF16.gguf`

And llama.cpp binaries at:
- `~/repo/llama.cpp/build/bin/llama-server`

#### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -e .

# Create storage directories
mkdir -p storage/uploads storage/processed

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

#### Step 4: Start Backend Services

**Terminal 1 - API Server (auto-starts model server):**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
source venv/bin/activate
PYTHONPATH="/path/to/backend:$PYTHONPATH" celery -A celery_worker.celery_app worker -l info -c 2 -Q media,analysis,submission
```

#### Step 5: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Step 6: Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Model Server | http://localhost:8080 |
| Health Check | http://localhost:8000/health |

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Database
DATABASE_URL=sqlite:///storage/db.sqlite

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Model - llama.cpp GGUF
LLAMA_MODEL_PATH=/home/aiguru/models/Qwen3.5-9B/Qwen3.5-9B-UD-Q4_K_XL.gguf
LLAMA_MMPROJ_PATH=/home/aiguru/models/Qwen3.5-9B/mmproj-BF16.gguf
LLAMA_CLI_PATH=~/repo/llama.cpp/build/bin

# llama-server connection
LLAMA_SERVER_HOST=localhost
LLAMA_SERVER_PORT=8080
LLAMA_SERVER_URL=http://localhost:8080

# Model inference parameters
LLAMA_CONTEXT_SIZE=32768
LLAMA_THREADS=-1
LLAMA_GPU_LAYERS=0

# Storage
STORAGE_PATH=./storage/uploads
MAX_UPLOAD_SIZE=104857600

# Security
API_KEY=
API_KEY_HEADER=X-API-Key
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Application
DEBUG=false
```

**Note**: `CORS_ORIGINS` must be valid JSON array format.

### Model Server Configuration

The backend automatically starts the llama-server with these defaults:
- Context size: 32k tokens (configurable via `LLAMA_CONTEXT_SIZE`)
- CPU threads: Auto (-1)
- GPU layers: 0 (CPU only, increase for GPU offloading)
- Parallel slots: 4

You can also start the model server manually:
```bash
./scripts/start_llama_server.sh --port 8080
```

## API Endpoints

### Configuration
- `GET/POST /api/v1/config/offices` - Manage offices
- `GET/POST /api/v1/config/endpoints` - Manage endpoints
- `POST /api/v1/config/endpoints/{id}/test` - Test endpoint

### Reports
- `POST /api/v1/reports` - Create report
- `POST /api/v1/reports/{id}/upload` - Upload media
- `POST /api/v1/reports/{id}/submit` - Submit for processing
- `GET /api/v1/reports/{id}/status` - Get status
- `GET /api/v1/reports/{id}` - Get full report
- `WS /ws/reports/{id}` - Real-time updates

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed status including model server

## Project Structure

```
clean_neighborhood/
├── backend/
│   ├── app/                 # FastAPI application
│   │   ├── api/v1/          # API endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── db/              # Database layer
│   ├── celery_worker/       # Celery tasks
│   ├── ai/                  # AI/ML components
│   │   ├── vlm_engine.py    # VLM analyzer client
│   │   └── model_server.py  # Model server manager
│   ├── pyproject.toml       # Dependencies
│   ├── Dockerfile
│   ├── .env.example         # Environment template
│   └── venv/                # Virtual environment
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── scripts/
│   ├── start_llama_server.sh   # Manual model server start
│   ├── stop_llama_server.sh    # Manual model server stop
│   └── test_llama_server.py    # Model server test
├── start_services.sh        # Start all services
├── stop_services.sh         # Stop all services
├── docker-compose.yml
└── README.md
```

## Usage

1. **Configure an Office**: Go to Configuration → Add Office with hotline number
2. **Add an Endpoint** (optional): Configure web service endpoints for automated submission
3. **Submit a Report**:
   - Select the office
   - Upload images/videos of the violation
   - Add description (optional)
   - Submit
4. **Monitor Progress**: The report will go through analysis and automatically file a complaint if approved

## Report Processing Pipeline

When a report is submitted, it goes through these stages:

1. **Upload** - Media files are uploaded and stored
2. **Analysis** (40% progress) - VLM analyzes content for:
   - Harmful content detection
   - Geolocation extraction
   - Severity assessment
3. **Decision** (70% progress) - Based on analysis:
   - Auto-approve (severity < threshold)
   - Flag for review (uncertain or sensitive)
   - Reject (harmful/invalid)
4. **Submission** (90% progress) - Files complaint via:
   - Web service endpoint (if configured)
   - Hotline (fallback)
5. **Completed** (100% progress) - Report finalized

## Troubleshooting

### Services won't start
- Check Redis is running: `redis-cli ping` should return `PONG`
- Ensure model files exist at configured paths
- Verify llama.cpp binaries are built and accessible
- Check log files: `/tmp/backend.log`, `/tmp/celery.log`, `/tmp/frontend.log`

### Analysis is slow or timing out
- The Qwen3.5 9B model on CPU can take 2-3 minutes per image
- Increase timeout in `backend/ai/vlm_engine.py` (default: 300s)
- Consider using GPU offloading by setting `LLAMA_GPU_LAYERS` > 0
- Reduce context size if memory is limited

### Model server errors
- Check model server health: `curl http://localhost:8080/health`
- Verify GGUF files are not corrupted
- Check available RAM (model needs ~6GB + context buffer)
- Try starting model server manually: `./scripts/start_llama_server.sh`

### Celery worker can't find 'ai' module
- Ensure `PYTHONPATH` includes the backend directory
- The start script sets this automatically: `PYTHONPATH="/path/to/backend:$PYTHONPATH"`

### Database errors
- Ensure database is initialized: `cd backend && python -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"`
- Check `DATABASE_URL` in `.env` points to correct location

## Development

### Testing the Model Server

```bash
# Test model server connectivity
curl http://localhost:8080/health

# Run the test script
cd /home/aiguru/repo/clean_neighborhood
python scripts/test_llama_server.py
```

### Backend Testing

```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Testing

```bash
cd frontend
npm run lint
npm run build
```

## Performance Tuning

### CPU Optimization
- Use all available cores: `LLAMA_THREADS=-1`
- Adjust batch size for your hardware
- Consider smaller quantization (Q4_K_M vs Q4_K_XL) for faster inference

### GPU Acceleration
If you have a CUDA-capable GPU:
```env
LLAMA_GPU_LAYERS=999  # Offload all layers to GPU
```

### Memory Usage
- Q4_K_XL model: ~6GB RAM
- mmproj file: ~1GB RAM
- Context buffer: ~2MB per 1K tokens
- Total for 32k context: ~10-12GB RAM recommended

## License

MIT
