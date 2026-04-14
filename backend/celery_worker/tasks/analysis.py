from celery_worker.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def analyze_content(self, metadata_result: int):
    """
    Analyze media content using Qwen3.5 VL via OpenVINO.

    This task performs:
    - Content safety checks (ads, adult content, etc.)
    - Geolocation detection from visual elements
    - Severity assessment
    """
    import asyncio
    from app.db.session import SessionLocal
    from app.models import Report
    from sqlalchemy import select

    async def _analyze():
        report_id = metadata_result if isinstance(metadata_result, int) else metadata_result.get("report_id")

        async with SessionLocal() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise ValueError(f"Report {report_id} not found")

            # TODO: Implement actual VLM analysis with OpenVINO
            # For now, return mock analysis
            analysis_result = await mock_vlm_analysis(report)

            return {
                "report_id": report_id,
                **analysis_result,
            }

    return asyncio.run(_analyze())


async def mock_vlm_analysis(report: "Report") -> dict:
    """
    Mock VLM analysis for development/testing.

    In production, this would:
    1. Load Qwen3.5 VL model via OpenVINO
    2. Process images/videos
    3. Extract structured information
    """
    import random

    # Simulate processing delay
    import asyncio
    await asyncio.sleep(2)

    # Get geolocation from EXIF if available
    geo = report.extracted_geolocation or {}

    # Mock analysis result
    categories = []
    if random.random() > 0.5:
        categories.append("advertisement")
    if random.random() > 0.7:
        categories.append("illegal_parking")

    return {
        "contains_harmful_content": len(categories) > 0,
        "harmful_categories": categories,
        "geolocation": {
            "confidence": geo.get("confidence", 0.5),
            "country": geo.get("country", "Unknown"),
            "city": geo.get("city", "Unknown"),
            "landmarks": [],
            "estimated_lat": geo.get("estimated_lat"),
            "estimated_lng": geo.get("estimated_lng"),
            "address": geo.get("address"),
        },
        "violation_severity": random.randint(3, 8),
        "recommended_action": "auto_submit" if categories else "review",
        "raw_analysis": {
            "note": "This is mock analysis. Replace with actual VLM integration.",
            "model": "Qwen3.5 VL (mock)",
            "device": "OpenVINO",
        },
    }
