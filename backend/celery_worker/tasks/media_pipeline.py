from celery import chain
from celery_worker.celery_app import celery_app
from celery_worker.tasks.analysis import analyze_content
from celery_worker.tasks.submission import submit_complaint


@celery_app.task(bind=True, max_retries=3)
def process_media_pipeline(self, report_id: int):
    """
    Main pipeline orchestrator for processing a report.

    This chains together all the processing steps:
    1. Extract metadata (EXIF, video frames, audio transcription)
    2. Analyze content with VLM
    3. Make decision (auto-approve or flag for review)
    4. Submit complaint
    """
    # Create task chain
    task_chain = chain(
        extract_metadata.s(report_id),
        analyze_content.s(),
        make_decision.s(),
        submit_complaint.s(),
    )

    # Execute chain
    return task_chain.apply_async()


@celery_app.task(bind=True, max_retries=2)
def extract_metadata(self, report_id: int):
    """
    Extract metadata from uploaded media files.

    - Extract EXIF data from images
    - Extract frames from videos
    - Transcribe audio files
    """
    import asyncio
    from app.db.session import SessionLocal
    from app.models import Report
    from sqlalchemy import select

    async def _extract():
        async with SessionLocal() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise ValueError(f"Report {report_id} not found")

            # Update status
            report.status = "analyzing"
            await session.commit()

            # TODO: Implement actual metadata extraction
            # - EXIF extraction from images
            # - Video frame extraction
            # - Audio transcription

            # Extract geolocation from EXIF if available
            geolocation = None
            if report.media_image_paths:
                geolocation = extract_geolocation_from_exif(report.media_image_paths[0])

            if geolocation:
                report.extracted_geolocation = geolocation
                report.geolocation_source = "exif"
                await session.commit()

            return report_id

    return asyncio.run(_extract())


def extract_geolocation_from_exif(image_path: str) -> dict:
    """Extract GPS coordinates from image EXIF data."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS

        image = Image.open(image_path)
        exif = image._getexif()

        if not exif:
            return None

        # Find GPS info
        gps_info = None
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                gps_info = value
                break

        if not gps_info:
            return None

        # Decode GPS coordinates
        def convert_dms(dms):
            """Convert degrees, minutes, seconds to decimal degrees."""
            degrees = float(dms[0])
            minutes = float(dms[1]) / 60.0
            seconds = float(dms[2]) / 3600.0
            return degrees + minutes + seconds

        lat_ref = gps_info.get(1)
        lat_dms = gps_info.get(2)
        lon_ref = gps_info.get(3)
        lon_dms = gps_info.get(4)

        if not all([lat_ref, lat_dms, lon_ref, lon_dms]):
            return None

        lat = convert_dms(lat_dms)
        if lat_ref == "S":
            lat = -lat

        lon = convert_dms(lon_dms)
        if lon_ref == "W":
            lon = -lon

        return {
            "confidence": 0.9,
            "estimated_lat": lat,
            "estimated_lng": lon,
        }

    except Exception as e:
        print(f"Error extracting EXIF geolocation: {e}")
        return None


@celery_app.task(bind=True)
def make_decision(self, analysis_result: dict, report_id: int = None):
    """
    Make a decision based on the AI analysis.

    - Auto-approve if confidence is high and no review flags
    - Flag for review if uncertain or sensitive
    """
    import asyncio
    from app.db.session import SessionLocal
    from app.models import Report
    from sqlalchemy import select

    async def _decide():
        async with SessionLocal() as session:
            # Get report_id from analysis result or argument
            rid = report_id or analysis_result.get("report_id")

            result = await session.execute(
                select(Report).where(Report.id == rid)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise ValueError(f"Report {rid} not found")

            # Store analysis result
            report.analysis_result = analysis_result

            # Determine action based on analysis
            recommended_action = analysis_result.get("recommended_action", "review")

            if recommended_action == "auto_submit":
                report.status = "approved"
            elif recommended_action == "reject":
                report.status = "rejected"
            else:
                report.status = "review_required"

            # Store categories and geolocation
            report.detected_categories = analysis_result.get("harmful_categories", [])
            if analysis_result.get("geolocation"):
                report.extracted_geolocation = analysis_result["geolocation"]

            await session.commit()

            return rid

    return asyncio.run(_decide())
