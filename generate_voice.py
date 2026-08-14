"""
AETHER - voiceover generator
Uses edge-tts (free, no API key, Microsoft neural voices) to turn each
scene's narration into an mp3 file.
"""
import asyncio
import json
import os
import sys
import edge_tts

VOICE = "en-US-EricNeural"  # free neural voice, calm/rational documentary tone
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "voice")


async def synth(text: str, dest_path: str, voice: str = VOICE) -> list[dict]:
    """Synthesizes speech and returns per-word timing (seconds) alongside it,
    so captions can highlight the word being spoken instead of showing the
    whole line for the full scene duration."""
    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    word_timings = []
    with open(dest_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timings.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })
    return word_timings


async def generate_voice_for_scenes(scenes: list[dict], voice: str = VOICE) -> list[dict]:
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, scene in enumerate(scenes):
        dest = os.path.join(OUT_DIR, f"scene_{i:02d}.mp3")
        scene["word_timings"] = await synth(scene["narration"], dest, voice)
        scene["voice_path"] = dest
    return scenes


if __name__ == "__main__":
    data = json.load(sys.stdin)
    data["scenes"] = asyncio.run(generate_voice_for_scenes(data["scenes"]))
    print(json.dumps(data, indent=2))
