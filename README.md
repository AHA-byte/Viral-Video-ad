First check the demo video in demo folder, outputs mp4 and voiceover in output folder, made an ad for cocacola. 

moviepy v2 was a beotch to deal with and removed too much(moviepy.editor import error, ImageClip, resize, fx, vfx, crossfadein, CompositeVideoClip time_slice ) 
Pillow removed Image.ANTIALIAS

so I am using moviepy==1.0.3
base.resize(scale) and zoomed = base.resize(zoom_factor)
Ken Burns zoom-in per image
LANCZOS

recomended to use with gpt-image-1, they wanted to look at my face for organization verification so I skipped that.

add your keys
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
FAL_KEY=your_fal_ai_key   # optional

run with
pipenv run streamlit run app.py

Step 1 — User enters product description

→ LLM creates:

Full script

Scene list

Tone and pacing

Step 2 — Voiceover is generated

→ OpenAI TTS creates natural-sounding narration

Step 3 — Choose engine

Smart Slideshow (free, images required)

AI Motion (Pika) (requires FAL credits)

Step 4 — Choose background music

Random track

Specific track

No music

Step 5 — Video is assembled

Scenes → Image animations

Motion (if Pika enabled)

Voiceover

Music

Export to MP4