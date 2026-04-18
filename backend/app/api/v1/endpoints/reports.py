import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models import Report, ConfigOffice
from celery_worker.tasks.media_pipeline import process_media_pipeline
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportStatusResponse,
    UploadUrlResponse,
    UploadUrlInfo,
)

router = APIRouter()


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    office_id: int = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all reports, optionally filtered by office or status."""
    query = select(Report)
    if office_id:
        query = query.where(Report.office_id == office_id)
    if status:
        query = query.where(Report.status == status)
    query = query.order_by(Report.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()
    return reports


@router.post("", response_model=UploadUrlResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new report and return upload URLs."""
    # Verify office exists
    office_result = await db.execute(
        select(ConfigOffice).where(ConfigOffice.id == report.office_id)
    )
    office = office_result.scalar_one_or_none()
    if not office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Office {report.office_id} not found",
        )

    # Create report record
    db_report = Report(
        office_id=report.office_id,
        status="pending",
        text_description=report.text_description,
        media_image_paths=[],
        media_video_paths=[],
    )
    db.add(db_report)
    await db.flush()
    await db.refresh(db_report)

    # Generate upload URLs
    upload_urls = []
    expires_at = datetime.utcnow() + timedelta(hours=1)

    if report.media_summary:
        # Image upload URLs
        for i in range(report.media_summary.image_count):
            upload_urls.append(
                UploadUrlInfo(
                    field_name=f"image_{i}",
                    url=f"/api/v1/reports/{db_report.id}/upload?type=image&index={i}",
                    method="POST",
                    max_size=settings.MAX_UPLOAD_SIZE,
                    expires_at=expires_at,
                )
            )
        # Video upload URLs
        for i in range(report.media_summary.video_count):
            upload_urls.append(
                UploadUrlInfo(
                    field_name=f"video_{i}",
                    url=f"/api/v1/reports/{db_report.id}/upload?type=video&index={i}",
                    method="POST",
                    max_size=settings.MAX_UPLOAD_SIZE,
                    expires_at=expires_at,
                )
            )
        # Audio upload URL
        if report.media_summary.has_audio:
            upload_urls.append(
                UploadUrlInfo(
                    field_name="audio",
                    url=f"/api/v1/reports/{db_report.id}/upload?type=audio",
                    method="POST",
                    max_size=settings.MAX_UPLOAD_SIZE,
                    expires_at=expires_at,
                )
            )

    return UploadUrlResponse(
        report_id=db_report.id,
        upload_urls=upload_urls,
        websocket_url=f"/ws/reports/{db_report.id}",
    )


@router.post("/{report_id}/upload")
async def upload_media(
    report_id: int,
    type: str,  # image, video, audio
    file: UploadFile = File(...),
    index: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Upload a media file for a report."""
    # Get report
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    # Update status to uploading
    if report.status == "pending":
        report.status = "uploading"

    # Validate file type
    allowed_types = {
        "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
        "video": ["video/mp4", "video/avi", "video/quicktime", "video/webm"],
        "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/webm"],
    }

    if type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid type: {type}",
        )

    if file.content_type not in allowed_types[type]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {file.content_type}",
        )

    # Generate unique filename
    ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4()}{ext}"
    storage_dir = Path(settings.STORAGE_PATH) / type / str(report_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / unique_name

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Update report with file path
    if type == "image":
        if not report.media_image_paths:
            report.media_image_paths = []
        report.media_image_paths.append(str(file_path))
    elif type == "video":
        if not report.media_video_paths:
            report.media_video_paths = []
        report.media_video_paths.append(str(file_path))
    elif type == "audio":
        report.media_audio_path = str(file_path)

    await db.flush()

    return {
        "success": True,
        "filename": unique_name,
        "path": str(file_path),
        "size": len(content),
    }


@router.post("/{report_id}/submit")
async def submit_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Submit a report for processing after all uploads are complete."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    if report.status not in ["pending", "uploading"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit report with status: {report.status}",
        )

    # Update status and trigger processing
    report.status = "analyzing"
    report.submitted_at = datetime.utcnow()
    await db.flush()

    # Trigger Celery task for processing
    process_media_pipeline.delay(report_id)

    return {"success": True, "report_id": report_id, "status": "analyzing"}


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the current status of a report."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    # Calculate progress based on status
    status_progress = {
        "pending": 0,
        "uploading": 10,
        "analyzing": 40,
        "review_required": 70,
        "approved": 80,
        "rejected": 100,
        "submitting": 90,
        "completed": 100,
        "failed": 100,
    }

    return ReportStatusResponse(
        id=report.id,
        status=report.status,
        progress_percent=status_progress.get(report.status, 0),
        current_step=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a report."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a report (only if pending)."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    if report.status not in ["pending", "uploading", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete report with status: {report.status}",
        )

    await db.delete(report)
    return None
