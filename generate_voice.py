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


async def synth(text: str, dest_path: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(dest_path)


async def generate_voice_for_scenes(scenes: list[dict]) -> list[dict]:
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, scene in enumerate(scenes):
        dest = os.path.join(OUT_DIR, f"scene_{i:02d}.mp3")
        await synth(scene["narration"], dest)
        scene["voice_path"] = dest
    return scenes


if __name__ == "__main__":
    data = json.load(sys.stdin)
    data["scenes"] = asyncio.run(generate_voice_for_scenes(data["scenes"]))
    print(json.dumps(data, indent=2))
