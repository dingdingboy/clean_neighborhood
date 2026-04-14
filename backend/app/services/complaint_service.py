import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConfigEndpoint, ConfigOffice, Report, ComplaintLog
from app.schemas.config import EndpointTestResponse


class ComplaintService:
    """Service for submitting complaints via hotline or web service endpoints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_via_hotline(
        self,
        report: Report,
        office: ConfigOffice,
    ) -> ComplaintLog:
        """
        Submit a complaint via hotline (mock implementation that logs the call).

        In a real implementation, this would integrate with a telephony service
        like Twilio to make actual phone calls with TTS.
        """
        # Create complaint log entry
        log = ComplaintLog(
            report_id=report.id,
            channel_type="hotline",
            channel_id=office.id,
            status="in_progress",
        )
        self.db.add(log)
        await self.db.flush()

        # Generate call script
        call_script = self._generate_hotline_script(report, office)

        # Mock: Log the call details instead of making actual call
        log.call_session_id = f"mock-call-{int(time.time())}"
        log.call_duration_seconds = 0  # Would be set after actual call

        # Simulate call logging
        print(f"[HOTLINE CALL] To: {office.hotline_number}")
        print(f"[HOTLINE CALL] Script: {call_script}")

        # Update log as successful (in real impl, would wait for call completion)
        log.status = "success"
        log.completed_at = datetime.utcnow()
        await self.db.flush()

        return log

    async def submit_via_endpoint(
        self,
        report: Report,
        endpoint: ConfigEndpoint,
    ) -> ComplaintLog:
        """Submit a complaint via a web service endpoint."""
        # Create complaint log entry
        log = ComplaintLog(
            report_id=report.id,
            channel_type="web_service",
            channel_id=endpoint.id,
            status="in_progress",
        )
        self.db.add(log)
        await self.db.flush()

        try:
            # Build request
            headers = self._build_headers(endpoint)
            payload = self._build_payload(endpoint, report)

            # Store request payload
            log.request_payload = json.dumps(payload)
            log.sent_at = datetime.utcnow()
            await self.db.flush()

            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=endpoint.http_method,
                    url=endpoint.url,
                    headers=headers,
                    json=payload if endpoint.http_method != "GET" else None,
                    params=payload if endpoint.http_method == "GET" else None,
                    timeout=30.0,
                )

            # Log response
            log.response_status_code = response.status_code
            log.response_body = response.text

            # Check success criteria
            if self._is_success(response, endpoint):
                log.status = "success"
            else:
                log.status = "failed"
                log.error_message = f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)

        log.completed_at = datetime.utcnow()
        await self.db.flush()

        return log

    async def test_endpoint(
        self,
        endpoint: ConfigEndpoint,
        test_payload: Optional[Dict[str, Any]] = None,
    ) -> EndpointTestResponse:
        """Test an endpoint connectivity and configuration."""
        start_time = time.time()

        try:
            headers = self._build_headers(endpoint)

            # Use test payload or create a minimal one
            payload = test_payload or {"test": True}

            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=endpoint.http_method,
                    url=endpoint.url,
                    headers=headers,
                    json=payload if endpoint.http_method != "GET" else None,
                    params=payload if endpoint.http_method == "GET" else None,
                    timeout=10.0,
                )

            response_time_ms = int((time.time() - start_time) * 1000)

            return EndpointTestResponse(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                response_body=response.text[:1000],  # Limit response size
                response_time_ms=response_time_ms,
            )

        except httpx.RequestError as e:
            return EndpointTestResponse(
                success=False,
                error_message=f"Request failed: {str(e)}",
                response_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return EndpointTestResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_time_ms=int((time.time() - start_time) * 1000),
            )

    def _build_headers(self, endpoint: ConfigEndpoint) -> Dict[str, str]:
        """Build HTTP headers for endpoint request."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Add custom headers
        if endpoint.headers_json:
            headers.update(endpoint.headers_json)

        # Add authentication
        if endpoint.auth_type == "bearer" and endpoint.auth_config:
            token = endpoint.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif endpoint.auth_type == "api_key" and endpoint.auth_config:
            key_name = endpoint.auth_config.get("key_name", "X-API-Key")
            key_value = endpoint.auth_config.get("key_value")
            if key_value:
                headers[key_name] = key_value

        return headers

    def _build_payload(
        self,
        endpoint: ConfigEndpoint,
        report: Report,
    ) -> Dict[str, Any]:
        """Build request payload for endpoint."""
        # Extract geolocation data
        geo = report.extracted_geolocation or {}

        # Build context for template
        context = {
            "report_id": report.id,
            "text_description": report.text_description or "",
            "detected_categories": report.detected_categories or [],
            "geolocation": geo,
            "confidence_scores": report.confidence_scores or {},
            "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None,
        }

        # If template is provided, use it
        if endpoint.payload_template:
            template = Template(endpoint.payload_template)
            rendered = template.render(**context)
            return json.loads(rendered)

        # Default payload
        return {
            "report_id": report.id,
            "description": report.text_description,
            "categories": report.detected_categories,
            "location": {
                "lat": geo.get("estimated_lat"),
                "lng": geo.get("estimated_lng"),
                "address": geo.get("address"),
                "city": geo.get("city"),
                "country": geo.get("country"),
            },
            "timestamp": report.submitted_at.isoformat() if report.submitted_at else None,
        }

    def _is_success(
        self,
        response: httpx.Response,
        endpoint: ConfigEndpoint,
    ) -> bool:
        """Check if response indicates success based on criteria."""
        # Basic HTTP success
        if 200 <= response.status_code < 300:
            return True

        # TODO: Implement custom success criteria based on endpoint.success_criteria
        # This could check response body for specific fields or patterns

        return False

    def _generate_hotline_script(
        self,
        report: Report,
        office: ConfigOffice,
    ) -> str:
        """Generate a script for the hotline call."""
        geo = report.extracted_geolocation or {}

        script_parts = [
            f"Hello, I would like to report a public interest violation.",
            f"",
            f"Location details:",
        ]

        if geo.get("address"):
            script_parts.append(f"Address: {geo['address']}")
        if geo.get("city"):
            script_parts.append(f"City: {geo['city']}")
        if geo.get("country"):
            script_parts.append(f"Country: {geo['country']}")

        if report.detected_categories:
            script_parts.append(f"")
            script_parts.append(f"Detected issues: {', '.join(report.detected_categories)}")

        if report.text_description:
            script_parts.append(f"")
            script_parts.append(f"Additional details: {report.text_description}")

        script_parts.append(f"")
        script_parts.append(f"This report was generated automatically by the Violation Reporter system.")
        script_parts.append(f"Report reference: {report.id}")

        return "\n".join(script_parts)
