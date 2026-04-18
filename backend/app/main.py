import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import init_db
from app.api.v1.router import api_router
from ai.model_server import start_model_server, stop_model_server

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting model server...")
    try:
        await start_model_server()
        logger.info("Model server started successfully")
    except Exception as e:
        logger.error(f"Failed to start model server: {e}")
        # Continue anyway - analysis tasks will fall back to EXIF data

    yield

    # Shutdown
    logger.info("Shutting down model server...")
    await stop_model_server()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with service status."""
    from ai.model_server import get_server_manager

    manager = get_server_manager()
    model_server_healthy = await manager.health_check()

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "services": {
            "database": "connected",
            "redis": "connected",  # TODO: Add actual Redis check
            "celery": "connected",  # TODO: Add actual Celery check
            "model_server": "healthy" if model_server_healthy else "unavailable",
        },
    }
