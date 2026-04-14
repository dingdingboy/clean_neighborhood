from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MediaSummary(BaseModel):
    """Summary of media files in a report."""

    image_count: int = 0
    video_count: int = 0
    has_audio: bool = False
    has_text: bool = False


class ReportCreate(BaseModel):
    """Schema for creating a new report."""

    office_id: int
    text_description: Optional[str] = None
    media_summary: Optional[MediaSummary] = None


class ReportUpdate(BaseModel):
    """Schema for updating a report."""

    status: Optional[str] = Field(
        None,
        pattern=r"^(pending|uploading|analyzing|review_required|approved|rejected|submitting|completed|failed)$"
    )
    text_description: Optional[str] = None


class GeolocationData(BaseModel):
    """Geolocation extraction result."""

    confidence: float = Field(..., ge=0.0, le=1.0)
    country: Optional[str] = None
    city: Optional[str] = None
    landmarks: Optional[List[str]] = None
    estimated_lat: Optional[float] = None
    estimated_lng: Optional[float] = None
    address: Optional[str] = None


class AnalysisResult(BaseModel):
    """AI analysis result schema."""

    contains_harmful_content: bool
    harmful_categories: List[str] = []
    geolocation: Optional[GeolocationData] = None
    violation_severity: int = Field(..., ge=1, le=10)
    recommended_action: str = Field(..., pattern=r"^(auto_submit|review|reject)$")
    raw_analysis: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """Schema for report response."""

    id: int
    office_id: int
    status: str
    media_image_paths: Optional[List[str]] = None
    media_video_paths: Optional[List[str]] = None
    media_audio_path: Optional[str] = None
    text_description: Optional[str] = None
    analysis_result: Optional[AnalysisResult] = None
    detected_categories: Optional[List[str]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    extracted_geolocation: Optional[GeolocationData] = None
    geolocation_source: Optional[str] = None
    complaint_ref: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportStatusResponse(BaseModel):
    """Schema for report status response."""

    id: int
    status: str
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UploadUrlInfo(BaseModel):
    """Information for uploading a file."""

    field_name: str
    url: str
    method: str = "POST"
    max_size: int
    expires_at: datetime


class UploadUrlResponse(BaseModel):
    """Schema for upload URL response."""

    report_id: int
    upload_urls: List[UploadUrlInfo]
    websocket_url: str
