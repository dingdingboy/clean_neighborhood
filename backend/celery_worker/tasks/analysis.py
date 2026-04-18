from celery_worker.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def analyze_content(self, metadata_result: int):
    """
    Analyze media content using llama.cpp server with Qwen3.5 VL GGUF model.

    This task performs:
    - Content safety checks (ads, adult content, etc.)
    - Geolocation detection from visual elements
    - Severity assessment
    """
    import asyncio
    from app.db.session import SessionLocal
    from app.models import Report
    from sqlalchemy import select
    from ai.vlm_engine import LlamaCppAnalyzer

    async def _analyze():
        report_id = metadata_result if isinstance(metadata_result, int) else metadata_result.get("report_id")

        async with SessionLocal() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise ValueError(f"Report {report_id} not found")

            # Perform actual VLM analysis with llama.cpp
            analysis_result = await run_vlm_analysis(report)

            return {
                "report_id": report_id,
                **analysis_result,
            }

    return asyncio.run(_analyze())


async def run_vlm_analysis(report: "Report") -> dict:
    """
    Run VLM analysis using llama.cpp server with GGUF model.

    This connects to llama-server and performs vision-language inference
    to analyze uploaded media for harmful content and geolocation.
    """
    from ai.vlm_engine import LlamaCppAnalyzer
    from pathlib import Path

    # Gather media paths from the report
    image_paths = report.media_image_paths or []
    video_paths = report.media_video_paths or []
    video_path = video_paths[0] if video_paths else None

    # Filter to only existing files
    image_paths = [p for p in image_paths if Path(p).exists()]
    if video_path and not Path(video_path).exists():
        video_path = None

    # If no media found, return mock result for text-only reports
    if not image_paths and not video_path:
        return {
            "contains_harmful_content": False,
            "harmful_categories": [],
            "geolocation": {
                "confidence": 0.0,
                "country": "Unknown",
                "city": "Unknown",
                "landmarks": [],
                "estimated_lat": None,
                "estimated_lng": None,
                "address": None,
            },
            "violation_severity": 5,
            "recommended_action": "review",
            "raw_analysis": {
                "note": "No media files available for analysis",
                "model": "Qwen3.5-VL-GGUF",
            },
        }

    # Run analysis with llama.cpp
    async with LlamaCppAnalyzer() as analyzer:
        try:
            result = await analyzer.analyze(
                image_paths=image_paths if image_paths else None,
                video_path=video_path,
                text_context=report.text_description,
            )
            return result.to_dict()

        except RuntimeError as e:
            # Server not available - fall back to mock with warning
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"llama-server not available: {e}. Using fallback analysis.")

            # Get geolocation from EXIF if available
            geo = report.extracted_geolocation or {}

            return {
                "contains_harmful_content": False,
                "harmful_categories": [],
                "geolocation": {
                    "confidence": geo.get("confidence", 0.5),
                    "country": geo.get("country", "Unknown"),
                    "city": geo.get("city", "Unknown"),
                    "landmarks": [],
                    "estimated_lat": geo.get("estimated_lat"),
                    "estimated_lng": geo.get("estimated_lng"),
                    "address": geo.get("address"),
                },
                "violation_severity": 5,
                "recommended_action": "review",
                "raw_analysis": {
                    "note": f"llama-server unavailable: {e}. Using EXIF data only.",
                    "model": "Qwen3.5-VL-GGUF (server unavailable)",
                },
            }


async def mock_vlm_analysis(report: "Report") -> dict:
    """
    Mock VLM analysis for development/testing when server is unavailable.

    Deprecated: Use run_vlm_analysis instead for actual inference.
    """
    import random
    import asyncio

    # Simulate processing delay
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
            "note": "This is mock analysis. Use llama-server for actual inference.",
            "model": "Qwen3.5-VL-GGUF (mock)",
        },
    }
