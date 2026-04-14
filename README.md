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
      │            │  Qwen3.5 VL     │
      │            │  (OpenVINO)     │
      │            └─────────────────┘
```

## Features

- **Multi-modal Media Upload**: Support for images, videos, audio, and text descriptions
- **AI-Powered Analysis**: Uses Qwen3.5 VL via OpenVINO to analyze content
- **Geolocation Extraction**: Extracts location from EXIF data and visual landmarks
- **Automated Complaint Filing**: Submits reports via hotline (mock) or web service endpoints
- **Real-time Status Updates**: WebSocket notifications for report progress
- **Configurable Offices**: Manage multiple offices and submission endpoints

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (with nvm recommended)
- Redis 7+

### Using Docker Compose (Recommended)

```bash
# Clone and navigate to the project
cd /home/aiguru/repo/clean_neighborhood

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup (Local Development)

#### Step 1: Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 --name violation-redis redis:7-alpine

# Or install Redis locally and run:
# redis-server
```

#### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Linux/Mac)
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create storage directories
mkdir -p storage/uploads storage/processed

# Create and configure .env file
cp .env.example .env
```

**Important**: Edit `.env` file and ensure `CORS_ORIGINS` is in valid JSON format:
```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

**For users in China (PRC)**, configure pip mirror for faster downloads:
```bash
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.trusted-host mirrors.aliyun.com
```

#### Step 3: Start Backend Services (Two Terminals)

**Terminal 1 - API Server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
source venv/bin/activate
celery -A celery_worker.celery_app worker -l info -c 2
```

#### Step 4: Frontend Setup

```bash
cd frontend

# Use nvm (recommended)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# For users in China (PRC), configure npm mirror
npm config set registry https://registry.npmmirror.com

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Step 5: Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

#### Stopping Services

```bash
# Stop backend API (Ctrl+C in Terminal 1)
# Stop Celery worker (Ctrl+C in Terminal 2)
# Stop frontend (Ctrl+C in Terminal 3)

# Stop Redis
docker stop violation-redis
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Database
DATABASE_URL=sqlite:///storage/db.sqlite

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Model
MODEL_PATH=./models/qwen3_5_vl_openvino
OPENVINO_DEVICE=CPU

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

### AI Model Setup

Place your Qwen3.5 VL OpenVINO model files in the `models/` directory:

```
models/
└── qwen3_5_vl_openvino/
    ├── openvino_model.xml
    ├── openvino_model.bin
    └── tokenizer/
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
│   ├── pyproject.toml       # Dependencies
│   ├── requirements.txt     # Pip dependencies
│   ├── Dockerfile
│   └── .env.example         # Environment template
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
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

## Troubleshooting

### Backend won't start
- Check `.env` file exists and `CORS_ORIGINS` is valid JSON
- Ensure Redis is running: `redis-cli ping` should return `PONG`
- Verify virtual environment is activated

### Celery worker won't start
- Ensure Redis is accessible at `redis://localhost:6379/0`
- Check you're in the backend directory with venv activated

### Frontend build fails
- Ensure Node.js 20+ is installed: `node --version`
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### Slow package downloads in China
- Backend: Use pip mirror as shown in setup steps
- Frontend: Use npm mirror as shown in setup steps

## Development

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

## License

MIT
