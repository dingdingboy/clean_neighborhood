"""Image processing utilities."""

from pathlib import Path
from typing import List, Tuple

def extract_frames_from_video(
    video_path: str,
    output_dir: str,
    num_frames: int = 5,
) -> List[str]:
    """
    Extract frames from a video file.

    Args:
        video_path: Path to video file
        output_dir: Directory to save frames
        num_frames: Number of frames to extract

    Returns:
        List of extracted frame file paths
    """
    import cv2

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_indices = [
        int(i * total_frames / (num_frames + 1))
        for i in range(1, num_frames + 1)
    ]

    extracted = []
    for idx, frame_num in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()

        if ret:
            frame_path = output_path / f"frame_{idx:03d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            extracted.append(str(frame_path))

    cap.release()
    return extracted


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get image width and height."""
    from PIL import Image

    with Image.open(image_path) as img:
        return img.size
