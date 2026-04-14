from fastapi import APIRouter

from app.api.v1.endpoints import config, reports
from app.api.v1.websockets import status

api_router = APIRouter()

api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# WebSocket router
api_router.include_router(status.router, prefix="/ws", tags=["websocket"])
