"""
Geolocation extraction utilities.

Provides functions for extracting and processing geolocation data
from various sources (EXIF, visual analysis, text context).
"""

from typing import Dict, Any, Optional
from pathlib import Path


def extract_exif_geolocation(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract GPS coordinates from image EXIF data.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with lat, lng, and confidence, or None if no GPS data
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

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

        return _parse_gps_info(gps_info)

    except Exception as e:
        print(f"Error extracting EXIF geolocation: {e}")
        return None


def _parse_gps_info(gps_info: Dict[int, Any]) -> Optional[Dict[str, Any]]:
    """Parse GPSInfo dict from EXIF."""
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

    altitude = gps_info.get(6)

    return {
        "confidence": 0.95,  # EXIF GPS is usually accurate
        "estimated_lat": round(lat, 6),
        "estimated_lng": round(lon, 6),
        "altitude": altitude,
        "source": "exif",
    }


def merge_geolocation_sources(
    exif_geo: Optional[Dict],
    visual_geo: Optional[Dict],
    text_geo: Optional[Dict],
) -> Optional[Dict[str, Any]]:
    """
    Merge geolocation data from multiple sources.

    Priority: EXIF > Visual > Text
    """
    if exif_geo:
        return {**exif_geo, "source": "exif"}
    if visual_geo:
        return {**visual_geo, "source": "visual_landmarks"}
    if text_geo:
        return {**text_geo, "source": "text_context"}
    return None
