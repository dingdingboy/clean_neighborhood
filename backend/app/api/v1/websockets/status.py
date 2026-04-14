import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models import Report

router = APIRouter()

# Store active websocket connections
active_connections: Dict[int, Set[WebSocket]] = {}


@router.websocket("/reports/{report_id}")
async def report_status_websocket(websocket: WebSocket, report_id: int):
    """WebSocket endpoint for real-time report status updates."""
    await websocket.accept()

    # Add to active connections
    if report_id not in active_connections:
        active_connections[report_id] = set()
    active_connections[report_id].add(websocket)

    try:
        # Send initial status
        async with SessionLocal() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()

            if report:
                await websocket.send_json({
                    "type": "status",
                    "report_id": report_id,
                    "status": report.status,
                    "updated_at": report.updated_at.isoformat() if report.updated_at else None,
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Report {report_id} not found",
                })

        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle client messages if needed
                if message.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        # Remove from active connections
        if report_id in active_connections:
            active_connections[report_id].discard(websocket)
            if not active_connections[report_id]:
                del active_connections[report_id]


async def broadcast_status_update(report_id: int, status: str, extra_data: dict = None):
    """Broadcast status update to all connected clients for a report."""
    if report_id not in active_connections:
        return

    message = {
        "type": "status_update",
        "report_id": report_id,
        "status": status,
    }
    if extra_data:
        message.update(extra_data)

    disconnected = set()
    for connection in active_connections[report_id]:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.add(connection)

    # Clean up disconnected clients
    for conn in disconnected:
        active_connections[report_id].discard(conn)

    if not active_connections[report_id]:
        del active_connections[report_id]
