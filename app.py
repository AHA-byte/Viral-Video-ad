import os
from pathlib import Path

import streamlit as st

from core.llm_script import generate_video_plan
from core.tts_voice import synthesize_voice
from core.pika_video import generate_pika_video, PikaError
from core.video_renderer import (
    merge_video_and_audio,
    build_slideshow_video,
    list_music_tracks,
)
from core.config import OUTPUT_DIR

st.set_page_config(page_title="ViralVid AI", layout="wide")

st.title("🎬 ViralVid AI - Promo Video Generator")

st.markdown(
    "Turn a **product description** into a **short promo video** with an AI-generated "
    "script, AI voiceover, and either:\n\n"
    "- **Smart Slideshow** (images + motion + music), or\n"
    "- **AI Motion** (Pika via FAL.ai, when you have credits).\n"
)

tab_generate, tab_videos = st.tabs(["Create Video", "My Videos"])


with tab_generate:
    st.header("1. Describe your product or offer")

    prompt = st.text_area(
        "Product pitch / description",
        height=140,
        placeholder="e.g. New wireless earbuds with 48h battery life, active noise cancellation, and a sleek matte-black case...",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        desired_length = st.selectbox(
            "Desired promo length",
            [15, 30, 45, 60],
            index=1,
            help="Used mainly for script pacing. Slideshow adapts to voiceover length.",
        )
    with col2:
        tone = st.selectbox(
            "Tone",
            ["energetic", "luxury", "friendly", "urgent", "minimalist"],
        )
    with col3:
        llm_provider = st.selectbox("Script model", ["openai", "gemini"])

    if st.button("Generate script and plan", type="primary"):
        if not prompt.strip():
            st.error("Please enter a product description.")
        else:
            with st.spinner("Generating script and shot list..."):
                plan = generate_video_plan(
                    prompt=prompt,
                    brand_tone=tone,
                    length_sec=desired_length,
                    provider=llm_provider,
                )
            st.session_state["plan"] = plan
            st.session_state["raw_prompt"] = prompt

            st.subheader("Generated Script")
            st.write(plan.full_script)

            st.subheader("Scene Breakdown")
            for i, s in enumerate(plan.scenes, start=1):
                st.markdown(f"**Scene {i} ({s.duration_sec}s)**: {s.text}")

            st.success("Script and plan ready. Scroll down to generate the video.")

    if "plan" in st.session_state:
        st.markdown("---")
        st.header("2. Choose engine, images, and music")

        # Engine toggle
        engine = st.radio(
            "Video engine",
            [
                "Smart Slideshow (Images + Voice + Music)",
                "AI Motion (Pika via FAL.ai) [beta]",
            ],
        )

        # Image upload (used for slideshow)
        uploaded_images = st.file_uploader(
            "Upload product images (required for Smart Slideshow)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )

        # Music selection
        tracks = list_music_tracks()
        if tracks:
            music_options = ["Random"] + [t.name for t in tracks] + ["No music"]
        else:
            music_options = ["No music"]

        music_choice = st.selectbox(
            "Background music",
            music_options,
            help="Choose a specific track from assets/music, a random one, or no music.",
        )

        if st.button("Create video", type="secondary"):
            plan = st.session_state["plan"]
            raw_prompt = st.session_state.get("raw_prompt", "")

            # 1) Voiceover (always)
            with st.spinner("Generating voiceover..."):
                voice_path = synthesize_voice(plan.full_script)

            # 2) Depending on engine
            if engine.startswith("AI Motion"):
                st.info(
                    "Using AI Motion engine (Pika via FAL.ai). "
                    "If your FAL account has no credits, this will fail."
                )

                # shorter clips to minimize cost when you eventually use credits
                pika_duration = 3

                pika_prompt = (
                    f"Short vertical promo video for social media (9:16) about:\n"
                    f"{raw_prompt}\n\n"
                    f"Tone: {tone}. Dynamic camera moves, product close-ups, smooth lighting, "
                    f"clean background. No text baked into the video, visuals only."
                )

                try:
                    with st.spinner("Generating motion video with Pika (fal.ai)..."):
                        base_video_path = generate_pika_video(
                            prompt=pika_prompt,
                            duration=pika_duration,
                            aspect_ratio="9:16",
                            resolution="720p",
                            filename="pika_base_video.mp4",
                        )

                    with st.spinner("Merging video with voiceover and music..."):
                        final_path = merge_video_and_audio(
                            base_video_path,
                            voice_path,
                            music_choice=music_choice,
                            output_name="viralvid_pika_promo.mp4",
                        )

                except PikaError as e:
                    st.error(
                        "AI Motion engine failed.\n\n"
                        f"Details: {e}\n\n"
                        "You may have no credits on FAL.ai. "
                        "Switch to Smart Slideshow or top up your FAL balance."
                    )
                    st.stop()

            else:
                # Smart Slideshow engine: requires images
                if not uploaded_images:
                    st.error(
                        "Smart Slideshow requires at least one uploaded image. "
                        "Please upload 1+ product images."
                    )
                    st.stop()

                Path(OUTPUT_DIR).mkdir(exist_ok=True)
                image_paths = []
                for i, f in enumerate(uploaded_images, start=1):
                    p = Path(OUTPUT_DIR) / f"upload_{i}.png"
                    with open(p, "wb") as out:
                        out.write(f.read())
                    image_paths.append(str(p))

                with st.spinner("Building slideshow video..."):
                    final_path = build_slideshow_video(
                        image_paths=image_paths,
                        voiceover_path=voice_path,
                        music_choice=music_choice,
                        output_name="viralvid_slideshow_promo.mp4",
                    )

            # Show and download
            st.success("Video ready!")
            st.video(final_path)

            with open(final_path, "rb") as f:
                st.download_button(
                    label="Download MP4",
                    data=f.read(),
                    file_name=Path(final_path).name,
                    mime="video/mp4",
                )


with tab_videos:
    st.header("Your Generated Videos (local)")

    out_dir = Path(OUTPUT_DIR)
    if not out_dir.exists():
        st.info("No videos generated yet.")
    else:
        videos = list(out_dir.glob("*.mp4"))
        if not videos:
            st.info("No videos generated yet.")
        else:
            for v in videos:
                st.write(v.name)
                st.video(str(v))
