import os
import math
import random
from pathlib import Path
from typing import List, Optional

from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx,
)

from PIL import Image as PILImage

from .config import OUTPUT_DIR, MUSIC_DIR

# Pillow 10+ compatibility for MoviePy 1.x
if not hasattr(PILImage, "ANTIALIAS"):
    PILImage.ANTIALIAS = PILImage.LANCZOS


# ----------------------
# Music helpers
# ----------------------

def list_music_tracks() -> List[Path]:
    """
    Return a list of available MP3 tracks in assets/music (no duplicates),
    case-insensitive on the file extension.
    """
    music_dir = Path(MUSIC_DIR)
    if not music_dir.exists():
        return []

    tracks: List[Path] = []
    for p in music_dir.iterdir():
        if p.is_file() and p.suffix.lower() == ".mp3":
            tracks.append(p)

    return sorted(tracks, key=lambda p: p.name.lower())


def _choose_music_path(choice: Optional[str]) -> str:
    """
    choice:
      - None or "No music" => no music
      - "Random"           => random track
      - "<filename>.mp3"   => specific track by name
    """
    tracks = list_music_tracks()
    if not tracks or choice in (None, "No music"):
        return ""

    if choice == "Random":
        return str(random.choice(tracks))

    for t in tracks:
        if t.name == choice:
            return str(t)

    return ""


def _compose_audio(
    voiceover_path: str,
    music_choice: Optional[str],
    target_duration: Optional[float] = None,
) -> CompositeAudioClip:
    """
    Create a CompositeAudioClip from voiceover + optional background music.
    Music is kept low so the voice is always clear.
    """
    voice = AudioFileClip(voiceover_path)
    duration = target_duration or voice.duration

    bg_path = _choose_music_path(music_choice)
    voice_clip = voice.volumex(1.0)  # main focus

    if bg_path:
        bg = AudioFileClip(bg_path).volumex(0.12).set_duration(duration)
        audio = CompositeAudioClip([voice_clip, bg])
    else:
        audio = CompositeAudioClip([voice_clip])

    audio = audio.set_duration(duration)
    return audio


def _choose_music_path(choice: Optional[str]) -> str:
    """
    choice:
      - None or "No music" => no music
      - "Random"           => random track
      - "<filename>.mp3"   => specific track by name
    """
    tracks = list_music_tracks()
    if not tracks or choice in (None, "No music"):
        return ""

    if choice == "Random":
        return str(random.choice(tracks))

    for t in tracks:
        if t.name == choice:
            return str(t)

    return ""

def _compose_audio(
    voiceover_path: str,
    music_choice: Optional[str],
    target_duration: Optional[float] = None,
) -> CompositeAudioClip:
    """
    Create a CompositeAudioClip from voiceover + optional background music.
    Music is kept low so the voice is always clear.
    """
    voice = AudioFileClip(voiceover_path)
    duration = target_duration or voice.duration

    bg_path = _choose_music_path(music_choice)
    voice_clip = voice.volumex(1.0)  # main focus

    if bg_path:
        bg = AudioFileClip(bg_path).volumex(0.12).set_duration(duration)
        audio = CompositeAudioClip([voice_clip, bg])
    else:
        audio = CompositeAudioClip([voice_clip])

    audio = audio.set_duration(duration)
    return audio

# ----------------------
# AI Motion (Pika) mixer
# ----------------------

def merge_video_and_audio(
    base_video_path: str,
    voiceover_path: str,
    music_choice: Optional[str] = "Random",
    output_name: str = "viralvid_pika_promo.mp4",
) -> str:

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    video = VideoFileClip(base_video_path)
    voice = AudioFileClip(voiceover_path)

    target_duration = voice.duration or video.duration

    # Create loop manually
    loops = max(1, math.ceil(target_duration / video.duration))
    video_loop = concatenate_videoclips([video] * loops)

    # MoviePy v2: trim to exact duration
    video_loop = video_loop.time_slice(0, target_duration)

    # Audio
    audio = _compose_audio(voiceover_path, music_choice, target_duration)

    # MoviePy v2: replace set_audio()
    final_clip = video.set_audio(audio)

    # Set frames per second explicitly
    final_clip = final_clip.set_fps(24)

    out_path = Path(OUTPUT_DIR) / output_name
    final_clip.write_videofile(
        str(out_path),
        codec="libx264",
        audio_codec="aac",
        fps=24,
    )

    video.close()
    video_loop.close()
    voice.close()

    return str(out_path)


# ----------------------
# Slideshow engine
# ----------------------

def build_slideshow_video(
    image_paths: List[str],
    voiceover_path: str,
    music_choice: Optional[str] = "Random",
    output_name: str = "viralvid_slideshow_promo.mp4",
    target_resolution: int = 1080,  # vertical height
) -> str:
    """
    Build a Ken-Burns-style slideshow from a list of images and a voiceover MP3.
    Each image:
      - is resized to a consistent vertical resolution
      - slowly zooms in over its duration

    Total slideshow duration matches the voiceover duration.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not image_paths:
        raise ValueError("build_slideshow_video requires at least one image.")

    voice = AudioFileClip(voiceover_path)
    duration = max(voice.duration, 1.0)
    per_scene = duration / len(image_paths)

    clips = []
    for img_path in image_paths:
        base = ImageClip(img_path).set_duration(per_scene)

        # First scale to fixed height so image size is consistent
        w, h = base.size
        if h != target_resolution:
            scale = float(target_resolution) / float(h)
            base = base.resize(scale)

        # Ken Burns style: slight zoom-in over the clip duration
        # Using a factor from 1.0 to about 1.1 across the scene
        def zoom_factor(t, total=per_scene):
            if total <= 0:
                return 1.0
            return 1.0 + 0.1 * (t / total)

        zoomed = base.resize(zoom_factor)

        clips.append(zoomed)

    # Concatenate all scenes
    video = concatenate_videoclips(clips, method="compose")
    video = video.set_duration(duration)

    # Optional global fade-in/out to soften edges (0.5s each)
    video = video.fx(vfx.fadein, 0.5).fx(vfx.fadeout, 0.5)

    # Compose audio (voice + optional music)
    audio = _compose_audio(voiceover_path, music_choice, duration)
    final_clip = video.set_audio(audio)

    # Set frames per second explicitly
    final_clip = final_clip.set_fps(24)

    out_path = Path(OUTPUT_DIR) / output_name
    final_clip.write_videofile(
        str(out_path),
        codec="libx264",
        audio_codec="aac",
        fps=24,
    )


    # Cleanup
    video.close()
    voice.close()
    for c in clips:
        c.close()

    return str(out_path)
