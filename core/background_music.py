import replicate

audio_url = replicate.run(
    "facebookresearch/musicgen",
    input={
        "prompt": "uplifting cinematic background music, no vocals",
        "duration": 30
    }
)
