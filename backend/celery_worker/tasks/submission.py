from celery_worker.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def submit_complaint(self, decision_result: dict):
    """
    Submit complaint via hotline or web service endpoint.

    This task:
    1. Determines the best submission channel
    2. Submits via hotline (mock) or web service
    3. Logs the submission attempt
    """
    import asyncio
    from app.db.session import SessionLocal
    from app.models import Report, ConfigOffice, ConfigEndpoint
    from app.services.complaint_service import ComplaintService
    from sqlalchemy import select

    async def _submit():
        # Handle both dict and int (report_id) as input
        if isinstance(decision_result, dict):
            report_id = decision_result.get("report_id")
        else:
            report_id = decision_result

        async with SessionLocal() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()

            if not report:
                raise ValueError(f"Report {report_id} not found")

            # Skip if not approved
            if report.status != "approved":
                return {"report_id": report_id, "submitted": False, "reason": "not_approved"}

            # Get office configuration
            office_result = await session.execute(
                select(ConfigOffice).where(ConfigOffice.id == report.office_id)
            )
            office = office_result.scalar_one_or_none()

            if not office:
                raise ValueError(f"Office {report.office_id} not found")

            service = ComplaintService(session)

            # Try web service endpoints first
            endpoint_result = await session.execute(
                select(ConfigEndpoint)
                .where(ConfigEndpoint.office_id == office.id)
                .where(ConfigEndpoint.is_active == True)
                .where(ConfigEndpoint.endpoint_type.in_(["web_service", "api"]))
            )
            endpoints = endpoint_result.scalars().all()

            submission_success = False

            # Try each endpoint
            for endpoint in endpoints:
                log = await service.submit_via_endpoint(report, endpoint)
                if log.status == "success":
                    submission_success = True
                    report.complaint_ref = f"web-{log.id}"
                    break

            # Fallback to hotline if no web endpoints or all failed
            if not submission_success and office.hotline_number:
                log = await service.submit_via_hotline(report, office)
                if log.status == "success":
                    submission_success = True
                    report.complaint_ref = f"hotline-{log.id}"

            # Update report status
            if submission_success:
                report.status = "completed"
            else:
                report.status = "failed"

            await session.commit()

            return {
                "report_id": report_id,
                "submitted": submission_success,
                "complaint_ref": report.complaint_ref,
            }

    return asyncio.run(_submit())
