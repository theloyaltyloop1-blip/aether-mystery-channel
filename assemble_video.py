"""
AETHER - video assembler
Combines each scene's footage (with a Ken Burns pan/zoom), voiceover, a
procedurally generated ambient music bed, and a caption card into clips,
then concatenates into the final mp4.
Free/local: moviepy + ffmpeg + numpy only, no paid services, no stock music
licensing to worry about since the bed is synthesized from scratch.
"""
import json
import os
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoClip,
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

W, H = 720, 1280  # vertical, TikTok/YouTube Shorts style - kept modest for fast, cheap rendering
FPS = 24
ZOOM_RANGE = 0.06  # total zoom over the clip's duration
SR = 24000  # ambient bed sample rate - narration quality doesn't need more
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "output")
FALLBACK_IMAGE = os.path.join(os.path.dirname(__file__), "assets", "fallback.jpg")
FONT_PATH = "C:/Windows/Fonts/segoeuib.ttf"


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


def caption_card(text: str, max_width: int) -> Image.Image:
    """Renders caption text with a soft rounded semi-transparent card behind
    it instead of a hard black stroke outline - the thick-stroke-on-white
    look is one of the most obvious "AI slop" tells, a subtitle card reads
    more like an edited-by-a-human video."""
    font = ImageFont.truetype(FONT_PATH, 40)
    pad_x, pad_y = 28, 20
    line_spacing = 10

    # wrap text to max_width
    words = text.split()
    lines, current = [], ""
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width - 2 * pad_x:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    line_h = max(line_heights) if line_heights else 40
    text_h = line_h * len(lines) + line_spacing * (len(lines) - 1)
    card_w = max_width
    card_h = text_h + 2 * pad_y

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=22, fill=(10, 14, 22, 165))

    y = pad_y
    for line in lines:
        line_w = draw.textlength(line, font=font)
        x = (card_w - line_w) / 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h + line_spacing

    return card


def build_scene_clip(scene: dict) -> CompositeVideoClip:
    image_path = scene.get("image_path") or FALLBACK_IMAGE
    audio = AudioFileClip(scene["voice_path"])
    duration = audio.duration

    visual = ken_burns_clip(image_path, duration)

    card_img = np.array(caption_card(scene["narration"], max_width=int(W * 0.86)))
    caption = (
        ImageClip(card_img)
        .with_duration(duration)
        .with_position(("center", H - card_img.shape[0] - 170))
    )

    scene_clip = CompositeVideoClip([visual, caption], size=(W, H)).with_duration(duration)
    scene_clip = scene_clip.with_audio(audio)
    return scene_clip


def _write_wav(path: str, samples: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(pcm.tobytes())


def generate_ambient_bed(duration: float, out_path: str) -> str:
    """Soft evolving drone: a few detuned low sine waves plus a slow
    amplitude wobble and a whisper of filtered noise for texture. Entirely
    synthesized, so there's no royalty-free-music licensing to track."""
    n = int(duration * SR)
    t = np.linspace(0, duration, n, endpoint=False)

    base_freqs = [55.0, 82.5, 110.0]  # A1, E2, A2 - a quiet open fifth/octave drone
    bed = np.zeros(n)
    for i, f in enumerate(base_freqs):
        detune = 1 + (0.002 * (-1) ** i)
        bed += np.sin(2 * np.pi * f * detune * t) * (0.5 / len(base_freqs))

    wobble = 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t)  # ~20s slow swell
    bed *= wobble

    noise = np.random.normal(0, 1, n)
    kernel = np.ones(200) / 200  # crude low-pass to turn white noise into a soft hiss
    noise = np.convolve(noise, kernel, mode="same")
    bed += noise * 0.03

    fade_len = min(int(2 * SR), n // 2)
    fade = np.linspace(0, 1, fade_len)
    bed[:fade_len] *= fade
    bed[-fade_len:] *= fade[::-1]

    peak = np.max(np.abs(bed)) or 1.0
    bed = bed / peak * 0.18  # quiet bed, sits well under narration

    _write_wav(out_path, bed, SR)
    return out_path


def assemble(data: dict) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    clips = [build_scene_clip(scene) for scene in data["scenes"]]
    final = concatenate_videoclips(clips, method="compose")

    ambient_path = os.path.join(OUT_DIR, "_ambient_tmp.wav")
    generate_ambient_bed(final.duration, ambient_path)
    ambient = AudioFileClip(ambient_path).with_duration(final.duration)
    final = final.with_audio(CompositeAudioClip([final.audio, ambient]))

    safe_topic = "".join(c if c.isalnum() else "_" for c in data["topic"])[:40]
    out_path = os.path.join(OUT_DIR, f"{safe_topic}.mp4")
    final.write_videofile(out_path, fps=FPS, codec="libx264", audio_codec="aac", preset="ultrafast", threads=4)

    os.remove(ambient_path)
    return out_path


if __name__ == "__main__":
    data = json.load(sys.stdin)
    path = assemble(data)
    print(json.dumps({"video_path": path, "topic": data["topic"]}, indent=2))
