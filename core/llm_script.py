from dataclasses import dataclass
from typing import List
import json

from .config import OPENAI_API_KEY, GEMINI_API_KEY

from openai import OpenAI
import google.generativeai as genai

client = OpenAI(api_key=OPENAI_API_KEY)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass
class Scene:
    text: str
    duration_sec: int


@dataclass
class VideoPlan:
    full_script: str
    scenes: List[Scene]


def generate_video_plan(
    prompt: str,
    brand_tone: str = "energetic",
    length_sec: int = 30,
    provider: str = "openai",
) -> VideoPlan:
    """
    Creates a short promo script plus per-scene breakdown.
    """

    target_scenes = max(3, min(8, length_sec // 5))

    sys_prompt = (
        "You are a creative director for short viral promo videos. "
        "Output a JSON object with: "
        "`full_script` (full voiceover text) and `scenes` "
        "(array of {text, duration_sec}). "
        f"Total duration approx {length_sec} seconds and {target_scenes} scenes."
    )
    user_prompt = (
        f"Product / offer: {prompt}\n"
        f"Brand tone: {brand_tone}\n"
        "Audience: TikTok / Reels viewers.\n"
        "Include call to action at the end."
    )

    if provider == "gemini" and GEMINI_API_KEY:
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(
            [{"role": "user", "parts": [sys_prompt + "\n\n" + user_prompt]}],
            generation_config={"response_mime_type": "application/json"},
        )
        data = resp.candidates[0].content.parts[0].text
    else:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        data = resp.choices[0].message.content

    obj = json.loads(data)

    scenes = [
        Scene(text=s["text"], duration_sec=int(s["duration_sec"]))
        for s in obj["scenes"]
    ]

    return VideoPlan(full_script=obj["full_script"], scenes=scenes)
