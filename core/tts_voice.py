from pathlib import Path
import os

from openai import OpenAI
from .config import OPENAI_API_KEY, OUTPUT_DIR

client = OpenAI(api_key=OPENAI_API_KEY)


def synthesize_voice(
    script: str,
    voice: str = "alloy",
    filename: str = "voiceover.mp3",
) -> str:
    """
    Generate voiceover MP3 from the given script using OpenAI TTS.
    Returns the absolute path to the MP3 file.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = Path(OUTPUT_DIR) / filename

    # Streaming response style from OpenAI docs
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=script,
    ) as response:
        response.stream_to_file(out_path)

    return str(out_path)
