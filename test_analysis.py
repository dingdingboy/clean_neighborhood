#!/usr/bin/env python3
"""Test script to verify report analysis pipeline works."""

import asyncio
import sys
sys.path.insert(0, 'backend')

from app.db.session import SessionLocal
from app.models import Report
from sqlalchemy import select
from celery_worker.tasks.analysis import analyze_content

async def test_analysis():
    """Test the analysis task directly."""
    async with SessionLocal() as session:
        # Get the most recent report
        result = await session.execute(
            select(Report).order_by(Report.created_at.desc()).limit(1)
        )
        report = result.scalar_one_or_none()

        if not report:
            print("No reports found in database")
            return

        print(f"Testing analysis for report {report.id}")
        print(f"  Status: {report.status}")
        print(f"  Images: {report.media_image_paths}")
        print(f"  Description: {report.text_description}")

        # Run analysis task
        print("\nRunning analysis task...")
        try:
            result = analyze_content.apply(args=[report.id])
            print(f"Task result: {result.get(timeout=300)}")
        except Exception as e:
            print(f"Task failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analysis())
