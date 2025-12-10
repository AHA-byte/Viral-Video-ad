import os
from pathlib import Path
from typing import List
from .config import OPENAI_API_KEY, OUTPUT_DIR
import openai

openai.api_key = OPENAI_API_KEY

def generate_scene_images(scenes_text: List[str]) -> List[str]:
    """
    For each scene text, create an AI image. Uses OpenAI images.
    Returns list of image file paths.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    paths = []

    for idx, text in enumerate(scenes_text):
        prompt = f"High-quality marketing photo for: {text}"
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        b64_data = resp.data[0].b64_json

        import base64
        img_bytes = base64.b64decode(b64_data)
        out_path = Path(OUTPUT_DIR) / f"scene_{idx+1}.png"
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        paths.append(str(out_path))

    return paths

