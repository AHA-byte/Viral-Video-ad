import os
from pathlib import Path
from typing import Dict, Any

import requests
import fal_client

from .config import FAL_KEY, OUTPUT_DIR


class PikaError(Exception):
    """Custom exception for Pika / fal.ai errors."""
    pass


def generate_pika_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    resolution: str = "720p",
    filename: str = "pika_base_video.mp4",
) -> str:
    """
    Generate a motion video using Pika v2 Turbo on fal.ai via the official
    fal-client SDK. Returns the local path to the downloaded MP4.
    """

    if not FAL_KEY:
        raise PikaError("FAL_KEY is not set in your environment (.env).")

    # Configure fal-client with your key
    fal_client.api_key = FAL_KEY

    # Arguments must match the model schema
    arguments: Dict[str, Any] = {
        "prompt": prompt,
        "resolution": resolution,      # "720p" or "1080p"
        "aspect_ratio": aspect_ratio,  # e.g. "9:16"
        "duration": duration,          # seconds
    }

    try:
        print("[Pika] Calling fal-ai/pika/v2/turbo/text-to-video...")
        result = fal_client.run(
            "fal-ai/pika/v2/turbo/text-to-video",
            arguments=arguments,
        )
        print("[Pika] Result received")
    except Exception as e:
        raise PikaError(f"Error calling fal-client: {e}") from e

    # Expected shape:
    # { "video": { "url": "https://...mp4", ... } }
    video_obj = None
    if isinstance(result, dict):
        video_obj = result.get("video") or result.get("data", {}).get("video")

    if not video_obj or "url" not in video_obj:
        raise PikaError(f"Pika result did not contain a video url: {result}")

    video_url = video_obj["url"]
    print(f"[Pika] Downloading video from {video_url}")

    # Download MP4
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = Path(OUTPUT_DIR) / filename

    try:
        resp = requests.get(video_url, timeout=300)
        resp.raise_for_status()
    except Exception as e:
        raise PikaError(f"Failed to download video from {video_url}: {e}") from e

    with open(out_path, "wb") as f:
        f.write(resp.content)

    print(f"[Pika] Saved video to {out_path}")
    return str(out_path)
