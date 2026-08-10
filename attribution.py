"""Builds the required Creative Commons attribution block for a video
description from each scene's Openverse metadata."""
import re
import unicodedata


def _clean(text: str, max_len: int = 120) -> str:
    """Strip control/formatting characters (YouTube rejects descriptions
    containing them) and cap length - free-text titles from Flickr/Wikimedia
    can contain stray unicode that breaks the API."""
    text = "".join(ch for ch in text if unicodedata.category(ch) not in ("Cc", "Cf", "Co", "Cs"))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def build_attribution_block(scenes: list[dict]) -> str:
    lines = []
    seen = set()
    for scene in scenes:
        attr = scene.get("attribution")
        if not attr:
            continue
        title = _clean(attr["title"])
        creator = _clean(attr["creator"], max_len=60)
        source_url = _clean(attr["source_url"], max_len=200)
        key = (title, creator, source_url)
        if key in seen or not source_url:
            continue
        seen.add(key)
        license_label = _clean(attr["license"], max_len=20)
        if attr["license_version"]:
            license_label += f" {_clean(attr['license_version'], max_len=10)}"
        lines.append(f'"{title}" by {creator}, licensed under {license_label}. Source: {source_url}')
    if not lines:
        return ""
    return "Image credits:\n" + "\n".join(lines[:8])
