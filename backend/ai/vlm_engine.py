"""
VLM Engine for analyzing media content using llama.cpp with GGUF models.

This module provides the interface for running vision-language model inference
via llama-server to analyze images for harmful content and geolocation.
"""

import json
import asyncio
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import httpx
from PIL import Image

from app.config import settings


@dataclass
class GeolocationResult:
    """Geolocation detection result."""
    confidence: float
    country: Optional[str] = None
    city: Optional[str] = None
    landmarks: List[str] = None
    estimated_lat: Optional[float] = None
    estimated_lng: Optional[float] = None
    address: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence,
            "country": self.country or "Unknown",
            "city": self.city or "Unknown",
            "landmarks": self.landmarks or [],
            "estimated_lat": self.estimated_lat,
            "estimated_lng": self.estimated_lng,
            "address": self.address,
        }


@dataclass
class AnalysisResult:
    """Content analysis result."""
    contains_harmful_content: bool
    harmful_categories: List[str]
    geolocation: GeolocationResult
    violation_severity: int
    recommended_action: str
    raw_analysis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contains_harmful_content": self.contains_harmful_content,
            "harmful_categories": self.harmful_categories,
            "geolocation": self.geolocation.to_dict(),
            "violation_severity": self.violation_severity,
            "recommended_action": self.recommended_action,
            "raw_analysis": self.raw_analysis,
        }


class LlamaCppAnalyzer:
    """
    Analyzer using llama.cpp server with GGUF multimodal models.

    This client communicates with llama-server via HTTP API to perform
    vision-language inference on images for content analysis.
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        timeout: float = 300.0,
    ):
        """
        Initialize the llama.cpp analyzer.

        Args:
            server_url: URL of the llama-server (default from settings)
            timeout: HTTP request timeout in seconds
        """
        self.server_url = server_url or settings.LLAMA_SERVER_URL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def health_check(self) -> bool:
        """Check if llama-server is healthy and responding."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.server_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _resize_image_if_needed(self, image_path: str, max_size: int = 1024) -> str:
        """
        Resize image if dimensions exceed max_size while maintaining aspect ratio.
        Returns path to resized image (temporary) or original if no resize needed.
        """
        with Image.open(image_path) as img:
            width, height = img.size
            if width <= max_size and height <= max_size:
                return image_path

            # Calculate new dimensions
            ratio = min(max_size / width, max_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # Resize and save to temp
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            temp_path = Path(image_path).parent / f"resized_{Path(image_path).name}"
            resized.save(temp_path, quality=90)
            return str(temp_path)

    def _build_analysis_prompt(self, text_context: Optional[str] = None) -> str:
        """Build the analysis prompt for the VLM."""
        prompt = """Analyze this image for public interest violations.

Detect the following:
1. Harmful or inappropriate content (advertisements, adult content, violence, etc.)
2. Geolocation clues (landmarks, street signs, license plates, store names, architecture style)
3. Severity of any public interest issues found (1-10 scale)

You must respond with ONLY a valid JSON object in this exact format:
{
    "contains_harmful_content": true/false,
    "harmful_categories": ["category1", "category2"],
    "geolocation": {
        "confidence": 0.0-1.0,
        "country": "country name or null",
        "city": "city name or null",
        "landmarks": ["landmark1", "landmark2"],
        "estimated_lat": latitude or null,
        "estimated_lng": longitude or null
    },
    "violation_severity": 1-10,
    "recommended_action": "auto_submit|review|reject",
    "description": "brief description of what you see"
}

Be precise and thorough in your analysis."""

        if text_context:
            prompt += f"\n\nAdditional context provided by user: {text_context}"

        return prompt

    async def analyze(
        self,
        image_paths: Optional[List[str]] = None,
        video_path: Optional[str] = None,
        audio_transcript: Optional[str] = None,
        text_context: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze media content using llama.cpp server.

        Args:
            image_paths: List of image file paths to analyze
            video_path: Path to video file (frames will be extracted)
            audio_transcript: Transcribed audio text (not used for image analysis)
            text_context: Additional text context from the user

        Returns:
            AnalysisResult with structured analysis data

        Raises:
            RuntimeError: If server is not available or analysis fails
        """
        if not image_paths and not video_path:
            raise ValueError("At least one image or video path must be provided")

        # Check server health
        if not await self.health_check():
            raise RuntimeError(
                f"llama-server not available at {self.server_url}. "
                "Please ensure the server is running."
            )

        # Handle video - extract frames if needed
        images_to_analyze = image_paths or []
        temp_frames = []
        if video_path:
            from ai.utils.image_processing import extract_frames_from_video
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                frames = extract_frames_from_video(video_path, tmpdir, num_frames=3)
                temp_frames.extend(frames)
                images_to_analyze.extend(frames)

        if not images_to_analyze:
            raise ValueError("No images available for analysis")

        # Process the first image (primary analysis)
        # For multiple images, we could batch them, but let's start with primary image
        primary_image = images_to_analyze[0]

        try:
            result = await self._analyze_single_image(
                primary_image, text_context, audio_transcript
            )

            # If we have multiple images, add note about additional context
            if len(images_to_analyze) > 1:
                result.raw_analysis["additional_images"] = len(images_to_analyze) - 1

            return result

        except Exception as e:
            raise RuntimeError(f"Analysis failed: {e}") from e

    async def _analyze_single_image(
        self,
        image_path: str,
        text_context: Optional[str] = None,
        audio_transcript: Optional[str] = None,
    ) -> AnalysisResult:
        """Analyze a single image via llama-server API."""
        # Prepare image
        processed_path = self._resize_image_if_needed(image_path, max_size=1024)
        image_b64 = self._encode_image(processed_path)

        # Build prompt
        prompt = self._build_analysis_prompt(text_context)
        if audio_transcript:
            prompt += f"\n\nAudio from video: {audio_transcript}"

        # Build the chat completion request
        messages = [
            {
                "role": "system",
                "content": "You are a vision-language model specialized in analyzing images for public safety and content moderation. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    }
                ]
            }
        ]

        # Make request to llama-server
        client = await self._get_client()

        payload = {
            "messages": messages,
            "temperature": 0.1,  # Low temperature for consistent JSON output
            "max_tokens": 1024,
            "stream": False,
        }

        response = await client.post(
            f"{self.server_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Parse JSON response
        parsed = self._parse_json_response(content)

        return self._create_result_from_parsed(parsed, content)

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from model response, handling common formatting issues."""
        # Try direct parsing first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        import re

        # Look for JSON in ```json ... ``` blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Look for any JSON object in the response
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # If all parsing fails, return a default structure
        return {
            "contains_harmful_content": False,
            "harmful_categories": [],
            "geolocation": {"confidence": 0.0},
            "violation_severity": 5,
            "recommended_action": "review",
            "description": "Failed to parse model response",
            "raw_response": content[:500]  # First 500 chars
        }

    def _create_result_from_parsed(
        self, parsed: Dict[str, Any], raw_content: str
    ) -> AnalysisResult:
        """Create AnalysisResult from parsed JSON."""
        geo_data = parsed.get("geolocation", {})

        geolocation = GeolocationResult(
            confidence=geo_data.get("confidence", 0.0),
            country=geo_data.get("country"),
            city=geo_data.get("city"),
            landmarks=geo_data.get("landmarks", []),
            estimated_lat=geo_data.get("estimated_lat"),
            estimated_lng=geo_data.get("estimated_lng"),
            address=geo_data.get("address"),
        )

        return AnalysisResult(
            contains_harmful_content=parsed.get("contains_harmful_content", False),
            harmful_categories=parsed.get("harmful_categories", []),
            geolocation=geolocation,
            violation_severity=parsed.get("violation_severity", 5),
            recommended_action=parsed.get("recommended_action", "review"),
            raw_analysis={
                "model": "Qwen3.5-VL-GGUF",
                "description": parsed.get("description", ""),
                "full_response": raw_content[:1000],
            }
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
