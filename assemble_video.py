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
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from moviepy import (
    VideoClip,
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    concatenate_videoclips,
    vfx,
)

W, H = 720, 1280  # vertical, TikTok/YouTube Shorts style - kept modest for fast, cheap rendering
FPS = 24
ZOOM_RANGE = 0.06  # total zoom over the clip's duration
SR = 24000  # ambient bed sample rate - narration quality doesn't need more
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "output")
FALLBACK_IMAGE = os.path.join(os.path.dirname(__file__), "assets", "fallback.jpg")
CROSSFADE = 0.35  # scene-to-scene crossfade, seconds - hard cuts between mismatched
# stock photos are one of the biggest "cheap slop" tells; a soft blend hides it

# each scene's raw stock photo comes from a different source with wildly
# different color/contrast - a light unifying grade (+ vignette) makes them
# read as one graded video instead of a pile of random downloads
_VIGNETTE_CACHE: dict[tuple[int, int], np.ndarray] = {}


def _vignette_mask(w: int, h: int) -> np.ndarray:
    key = (w, h)
    if key not in _VIGNETTE_CACHE:
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt(((xx - cx) / (w / 2)) ** 2 + ((yy - cy) / (h / 2)) ** 2)
        mask = 1 - np.clip((dist - 0.55) / 0.65, 0, 1) * 0.35
        _VIGNETTE_CACHE[key] = mask[..., None]
    return _VIGNETTE_CACHE[key]


def _grade_image(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.10)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Brightness(img).enhance(0.97)
    arr = np.asarray(img).astype(np.float32)
    arr *= _vignette_mask(img.width, img.height)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# this pipeline runs both on Windows (locally) and Ubuntu (GitHub Actions) -
# hardcoding a Windows font path silently breaks every cloud run
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_PATH = next((p for p in _FONT_CANDIDATES if os.path.exists(p)), _FONT_CANDIDATES[-1])


def ken_burns_clip(image_path: str, duration: float) -> VideoClip:
    """Cheap pan effect: resize the source image ONCE to an oversized canvas,
    then produce each frame via plain numpy array slicing (a fixed-size crop
    window sliding across the canvas) - no per-frame resize, which is what
    made rendering slow."""
    src = _grade_image(Image.open(image_path).convert("RGB"))

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


DEFAULT_STYLE = {
    "box_color": (10, 14, 22),
    "box_alpha": 165,
    "text_color": (255, 255, 255),
}


def caption_card(text: str, max_width: int, style: dict = DEFAULT_STYLE) -> Image.Image:
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

    box_r, box_g, box_b = style["box_color"]
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=22, fill=(box_r, box_g, box_b, style["box_alpha"]))

    text_r, text_g, text_b = style["text_color"]
    y = pad_y
    for line in lines:
        line_w = draw.textlength(line, font=font)
        x = (card_w - line_w) / 2
        draw.text((x, y), line, font=font, fill=(text_r, text_g, text_b, 255))
        y += line_h + line_spacing

    return card


HIGHLIGHT_COLOR = (255, 196, 40)  # warm gold - the emphasis word per line

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be", "been",
    "to", "of", "in", "on", "at", "for", "with", "it", "that", "this", "he", "she",
    "they", "you", "i", "we", "his", "her", "their", "your", "my", "its", "as", "by",
    "from", "not", "so", "if", "when", "then", "than", "just", "like", "get", "gets",
    "got", "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "one", "because", "what", "how", "who", "which", "there", "here", "up",
    "down", "out", "all", "some", "more", "most", "own", "only", "also", "even",
    "still", "way", "into", "every", "same",
}


def _pick_highlight_index(word_timings: list[dict]) -> int | None:
    """Picks one standout word per line to render in gold, mirroring how the
    reference video highlights the single word that carries the point of the
    sentence (a plain wall of same-colored words is what reads as cheap)."""
    best_i, best_len = None, 0
    for i, wt in enumerate(word_timings):
        clean = "".join(ch for ch in wt["text"] if ch.isalpha())
        if len(clean) < 5 or clean.lower() in _STOPWORDS:
            continue
        if len(clean) > best_len:
            best_i, best_len = i, len(clean)
    return best_i


def word_pop_image(word: str, style: dict = DEFAULT_STYLE, highlight: bool = False) -> Image.Image:
    """One bold word, centered, with a thin dark stroke for legibility over
    any background - the "TikTok caption" look: a single word pops on
    screen in sync with narration instead of a static subtitle card."""
    font = ImageFont.truetype(FONT_PATH, 64)
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), word, font=font)
    pad = 12
    w, h = bbox[2] - bbox[0] + pad * 2, bbox[3] - bbox[1] + pad * 2

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fill = HIGHLIGHT_COLOR if highlight else style["text_color"]
    draw.text(
        (pad - bbox[0], pad - bbox[1]), word, font=font,
        fill=(*fill, 255), stroke_width=4, stroke_fill=(0, 0, 0, 220),
    )
    return img


def build_scene_clip(scene: dict, style: dict = DEFAULT_STYLE, captions: bool = True) -> CompositeVideoClip:
    image_path = scene.get("image_path") or FALLBACK_IMAGE
    audio = AudioFileClip(scene["voice_path"])
    duration = audio.duration

    visual = ken_burns_clip(image_path, duration)
    layers = [visual]

    word_timings = scene.get("word_timings") if captions else None
    if word_timings:
        highlight_i = _pick_highlight_index(word_timings)
        for i, wt in enumerate(word_timings):
            word_dur = max(wt["end"] - wt["start"], 0.05)
            word_img = np.array(word_pop_image(wt["text"], style=style, highlight=(i == highlight_i)))
            word_clip = (
                ImageClip(word_img)
                .with_start(wt["start"])
                .with_duration(word_dur)
                .with_position(("center", H - word_img.shape[0] - 220))
            )
            layers.append(word_clip)
    elif captions:
        card_img = np.array(caption_card(scene["narration"], max_width=int(W * 0.86), style=style))
        caption = (
            ImageClip(card_img)
            .with_duration(duration)
            .with_position(("center", H - card_img.shape[0] - 170))
        )
        layers.append(caption)

    scene_clip = CompositeVideoClip(layers, size=(W, H)).with_duration(duration)
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


def assemble(data: dict, style: dict = DEFAULT_STYLE, captions: bool = True) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    clips = [build_scene_clip(scene, style=style, captions=captions) for scene in data["scenes"]]
    # crossfade between scenes instead of hard cuts - mismatched stock photos
    # cutting straight into each other is one of the biggest "cheap slop" tells
    fade = min(CROSSFADE, min(c.duration for c in clips) / 2)
    clips = [clips[0]] + [c.with_effects([vfx.CrossFadeIn(fade)]) for c in clips[1:]]
    final = concatenate_videoclips(clips, method="compose", padding=-fade)

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
