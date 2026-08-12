"""
AETHER - custom YouTube thumbnail generator
YouTube auto-picks a random frame from the video as the thumbnail if none is
set, which always includes the mid-video caption card since captions are on
screen the whole time - every video ends up looking like the same template.
This builds a real thumbnail instead: the first scene's clean source image
(no caption box) with a short bold headline, in the 1280x720 YouTube wants.
"""
import os
import re
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720

# Impact isn't available on the Ubuntu GitHub Actions runner - fall back to
# a bold sans that's preinstalled there so cloud runs don't crash.
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/impact.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_PATH = next((p for p in _FONT_CANDIDATES if os.path.exists(p)), _FONT_CANDIDATES[-1])
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "thumbnails")


def _crop_to_fill(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_h = img.height
        new_w = int(new_h * target_ratio)
    else:
        new_w = img.width
        new_h = int(new_w / target_ratio)
    left = (img.width - new_w) // 2
    top = (img.height - new_h) // 2
    return img.crop((left, top, left + new_w, top + new_h)).resize((target_w, target_h), Image.LANCZOS)


def _headline_from_topic(topic: str) -> str:
    # keep it short and punchy - thumbnails need to read at a glance
    text = re.sub(r"^(the|a|an)\s+", "", topic.strip(), flags=re.IGNORECASE)
    words = text.split()
    return " ".join(words[:6]).upper()


def generate_thumbnail(topic: str, scenes: list[dict]) -> str | None:
    image_path = None
    # prefer a scene whose image actually matched its keyword over a generic
    # fallback photo - a thumbnail built from filler footage is exactly the
    # "same recycled image everywhere" problem this is meant to avoid
    for scene in scenes:
        if scene.get("image_path") and os.path.exists(scene["image_path"]) and not scene.get("is_fallback"):
            image_path = scene["image_path"]
            break
    if not image_path:
        for scene in scenes:
            if scene.get("image_path") and os.path.exists(scene["image_path"]):
                image_path = scene["image_path"]
                break
    if not image_path:
        return None

    os.makedirs(OUT_DIR, exist_ok=True)
    src = Image.open(image_path).convert("RGB")
    canvas = _crop_to_fill(src, W, H)

    # darken the bottom third so white text stays readable over any image
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, int(H * 0.62), W, H], fill=(0, 0, 0, 150))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    headline = _headline_from_topic(topic)
    lines = textwrap.wrap(headline, width=18)[:3]

    draw = ImageDraw.Draw(canvas)
    font_size = 92 if len(lines) <= 2 else 72
    font = ImageFont.truetype(FONT_PATH, font_size)
    line_gap = 10

    # DejaVu Bold (the Linux fallback) is noticeably wider than Impact -
    # shrink to fit rather than letting long lines run off the edges
    max_line_w = max(draw.textlength(line, font=font) for line in lines)
    while max_line_w > W - 80 and font_size > 40:
        font_size -= 4
        font = ImageFont.truetype(FONT_PATH, font_size)
        max_line_w = max(draw.textlength(line, font=font) for line in lines)

    line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    total_h = sum(line_heights) + line_gap * (len(lines) - 1)
    y = H - 30 - total_h

    for line, lh in zip(lines, line_heights):
        w = draw.textlength(line, font=font)
        x = (W - w) / 2
        draw.text((x, y), line, font=font, fill="white", stroke_width=4, stroke_fill="black")
        y += lh + line_gap

    safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:40]
    out_path = os.path.join(OUT_DIR, f"{safe_topic}.jpg")
    canvas.save(out_path, quality=90)
    return out_path
