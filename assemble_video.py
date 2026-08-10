"""
AETHER - video assembler
Combines each scene's NASA image (with a Ken Burns pan/zoom) and voiceover
into clips, adds a simple caption, and concatenates into the final mp4.
Free/local: moviepy + ffmpeg only, no paid services.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from moviepy import (
    VideoClip,
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)

W, H = 720, 1280  # vertical, TikTok/YouTube Shorts style - kept modest for fast, cheap rendering
FPS = 24
ZOOM_RANGE = 0.06  # total zoom over the clip's duration
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "output")
FALLBACK_IMAGE = os.path.join(os.path.dirname(__file__), "assets", "fallback.jpg")


def ken_burns_clip(image_path: str, duration: float) -> VideoClip:
    """Cheap pan effect: resize the source image ONCE to an oversized canvas,
    then produce each frame via plain numpy array slicing (a fixed-size crop
    window sliding across the canvas) - no per-frame resize, which is what
    made rendering slow."""
    src = Image.open(image_path).convert("RGB")

    margin_scale = 1 + ZOOM_RANGE
    canvas_w, canvas_h = int(W * margin_scale), int(H * margin_scale)
    src_ratio = src.width / src.height
    canvas_ratio = canvas_w / canvas_h
    if src_ratio > canvas_ratio:
        new_h = canvas_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = canvas_w
        new_h = int(new_w / src_ratio)
    big = np.array(src.resize((new_w, new_h), Image.LANCZOS))

    max_x0 = big.shape[1] - W
    max_y0 = big.shape[0] - H

    def make_frame(t):
        progress = t / duration if duration > 0 else 0
        x0 = int(max_x0 * progress)
        y0 = max_y0 // 2
        return big[y0 : y0 + H, x0 : x0 + W]

    return VideoClip(make_frame, duration=duration)


def build_scene_clip(scene: dict) -> CompositeVideoClip:
    image_path = scene.get("image_path") or FALLBACK_IMAGE
    audio = AudioFileClip(scene["voice_path"])
    duration = audio.duration

    visual = ken_burns_clip(image_path, duration)

    caption = (
        TextClip(
            text=scene["narration"],
            font_size=32,
            color="white",
            size=(int(W * 0.85), None),
            method="caption",
            stroke_color="black",
            stroke_width=2,
        )
        .with_duration(duration)
        .with_position(("center", H - 260))
    )

    scene_clip = CompositeVideoClip([visual, caption], size=(W, H)).with_duration(duration)
    scene_clip = scene_clip.with_audio(audio)
    return scene_clip


def assemble(data: dict) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    clips = [build_scene_clip(scene) for scene in data["scenes"]]
    final = concatenate_videoclips(clips, method="compose")

    safe_topic = "".join(c if c.isalnum() else "_" for c in data["topic"])[:40]
    out_path = os.path.join(OUT_DIR, f"{safe_topic}.mp4")
    final.write_videofile(out_path, fps=FPS, codec="libx264", audio_codec="aac", preset="ultrafast", threads=4)
    return out_path


if __name__ == "__main__":
    data = json.load(sys.stdin)
    path = assemble(data)
    print(json.dumps({"video_path": path, "topic": data["topic"]}, indent=2))
