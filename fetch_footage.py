"""
AETHER - footage fetcher
Pulls free, openly-licensed imagery from Openverse (api.openverse.org), which
aggregates public-domain / Creative-Commons images from many sources
(Flickr, Wikimedia, museums, etc). No API key required for basic search,
and it covers any topic - not just space, so it works for the mystery/
aviation channel too.
"""
import json
import os
import random
import sys

import numpy as np
import requests
from PIL import Image

OPENVERSE_URL = "https://api.openverse.org/v1/images/"
NASA_SEARCH_URL = "https://images-api.nasa.gov/search"
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "footage")
BLOCKLIST_FILE = os.path.join(os.path.dirname(__file__), "assets", "image_blocklist.json")

HEADERS = {"User-Agent": "AETHER-pipeline/1.0 (personal project)"}

# A single fixed fallback query always returns the same top result (that's
# how the same generic motel-sign photo ended up on nearly every video that
# didn't get a good keyword match). Rotating through several unrelated
# generic queries, plus picking randomly among the results instead of always
# the first, keeps fallback images actually varied.
FALLBACK_QUERIES = [
    "old newspaper archive", "vintage photograph mystery", "night sky stars",
    "foggy forest", "ocean horizon", "abandoned building", "historical document",
    "radio tower silhouette", "storm clouds", "dark road at night",
]

# NASA's own image library (all public domain, no license ambiguity) -
# narrowly space/aeronautics content, so it doesn't have the "random
# unrelated result" problem Openverse's general aggregation has.
NASA_FALLBACK_QUERIES = [
    "galaxy", "nebula", "planet Earth from space", "astronaut spacewalk",
    "Milky Way", "solar system", "spiral galaxy", "deep space", "solar flare",
    "spacecraft", "moon surface", "Hubble telescope image",
]

# Openverse's "cartoon" tag also covers political caricature art (e.g. a
# "Republican Clown Car Parade" caricature series ranks highly for "cartoon
# farm illustration") - block anything whose title/tags suggest politics,
# violence, or other content that has no business anywhere near any AETHER
# video, checked on every channel by default.
UNSAFE_TERMS = {
    "trump", "biden", "obama", "clinton", "republican", "democrat", "gop", "rnc", "dnc",
    "election", "senator", "congress", "politician", "political", "caricature", "satire",
    "protest", "president", "nazi", "hitler", "isis", "terrorist", "war", "gun", "weapon",
    "shooting", "blood", "gore", "nude", "naked", "sex", "porn", "fetish", "drug", "cocaine",
    "alcohol", "beer", "cigarette", "smoking", "gambling", "casino",
    # not unsafe, just the wrong tone for a cheerful kids/general channel
    "halloween", "haunted", "scary", "horror", "ghost", "skeleton", "witch",
    "zombie", "monster", "nightmare", "creepy", "spooky", "demon", "devil",
    # historical political/satirical engravings slip past the modern-politics
    # terms above - these catch the older "British ministry" / parliamentary
    # caricature genre specifically
    "ministry", "parliament", "monarch", "propaganda",
}


def _is_unsafe(item: dict) -> bool:
    text = (item.get("title") or "").lower()
    text += " " + " ".join(t.get("name", "") for t in (item.get("tags") or []) if isinstance(t, dict)).lower()
    return any(term in text for term in UNSAFE_TERMS)


# Some "free clipart" marketplaces (Vecteezy, PNGTree, Freepik, etc.) index a
# LOW-RES PREVIEW into Openverse with a literal checkerboard pattern baked
# into the pixels to advertise "this has transparency if you pay for it" -
# that checkerboard is what made the farm-animal test video look cheap, not
# an actual transparency bug. Detected by looking for two near-gray/white
# tones covering a large, roughly-equal share of the image (the checker
# squares), which real photos/illustrations essentially never do.
_MARKETPLACE_DOMAINS = ("vecteezy.com", "pngtree.com", "freepik.com", "shutterstock.com",
                         "istockphoto.com", "123rf.com", "depositphotos.com", "dreamstime.com", "alamy.com")


def _is_marketplace_preview(item: dict) -> bool:
    url = (item.get("foreign_landing_url") or "").lower()
    return any(domain in url for domain in _MARKETPLACE_DOMAINS)


def _looks_too_blank(image_path: str, min_content_fraction: float = 0.06) -> bool:
    """Some scanned/sketch pages Openverse returns are 95%+ empty white
    margin with one tiny illegible doodle in a corner - fine as a thumbnail,
    useless once the Ken Burns pan/bounce crops in. Rejects images where too
    little of the frame actually differs from its background color."""
    try:
        img = Image.open(image_path).convert("RGB").resize((128, 128))
    except Exception:
        return False
    arr = np.array(img).astype(int)
    border = np.concatenate([arr[0, :], arr[-1, :], arr[:, 0], arr[:, -1]])
    bg = np.median(border, axis=0)
    diff = np.abs(arr - bg).sum(axis=-1)
    content_fraction = (diff > 40).mean()
    return content_fraction < min_content_fraction


def _looks_like_checkerboard(image_path: str) -> bool:
    try:
        img = Image.open(image_path).convert("RGB").resize((64, 64))
    except Exception:
        return False
    arr = np.array(img)
    # bucket into coarse gray levels; a checkerboard preview is dominated by
    # two near-white/light-gray buckets in close to a 50/50 split
    is_grayish = np.abs(arr[..., 0].astype(int) - arr[..., 1].astype(int)) < 8
    is_grayish &= np.abs(arr[..., 1].astype(int) - arr[..., 2].astype(int)) < 8
    brightness = arr.mean(axis=-1)
    light = is_grayish & (brightness > 190) & (brightness < 245)
    white = is_grayish & (brightness >= 245)
    light_frac, white_frac = light.mean(), white.mean()
    total = light_frac + white_frac
    if total < 0.35:
        return False
    ratio = min(light_frac, white_frac) / max(light_frac, white_frac, 1e-6)
    return ratio > 0.3


def _load_blocklist() -> set[str]:
    if not os.path.exists(BLOCKLIST_FILE):
        return set()
    with open(BLOCKLIST_FILE) as f:
        return set(json.load(f))


def block_image(image_id: str) -> None:
    blocked = _load_blocklist()
    blocked.add(image_id)
    os.makedirs(os.path.dirname(BLOCKLIST_FILE), exist_ok=True)
    with open(BLOCKLIST_FILE, "w") as f:
        json.dump(sorted(blocked), f, indent=2)


def search_candidates(keyword: str, blocked: set[str], limit: int = 6) -> list[dict]:
    resp = requests.get(
        OPENVERSE_URL,
        params={
            "q": keyword,
            "license_type": "commercial,modification",
            "page_size": 20,
            "mature": "false",
        },
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    results = [
        r for r in resp.json().get("results", [])
        if r.get("url") and r.get("id") not in blocked and not _is_unsafe(r) and not _is_marketplace_preview(r)
    ]
    # shuffle rather than always taking the top hit - avoids the same
    # "best match" recurring across unrelated videos
    random.shuffle(results)
    candidates = []
    for item in results[:limit]:
        candidates.append({
            "id": item["id"],
            "url": item["url"],
            "title": item.get("title") or "Untitled",
            "creator": item.get("creator") or "Unknown",
            "license": (item.get("license") or "").upper(),
            "license_version": item.get("license_version") or "",
            "license_url": item.get("license_url") or "",
            "source_url": item.get("foreign_landing_url") or item.get("url"),
        })
    return candidates


def search_nasa_candidates(keyword: str, blocked: set[str], limit: int = 6) -> list[dict]:
    resp = requests.get(
        NASA_SEARCH_URL,
        params={"q": keyword, "media_type": "image"},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    items = resp.json().get("collection", {}).get("items", [])
    candidates = []
    for item in items:
        data = (item.get("data") or [{}])[0]
        nasa_id = data.get("nasa_id")
        if not nasa_id or nasa_id in blocked:
            continue
        preview = next((l["href"] for l in (item.get("links") or []) if l.get("rel") == "preview"), None)
        if not preview:
            continue
        candidates.append({
            "id": nasa_id,
            "url": preview,
            "title": data.get("title") or "Untitled",
            "creator": data.get("center") or "NASA",
            "license": "PUBLIC DOMAIN",
            "license_version": "",
            "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
            "source_url": f"https://images.nasa.gov/details/{nasa_id}",
        })
    random.shuffle(candidates)
    return candidates[:limit]


def download(url: str, dest_path: str) -> None:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)


def _download_first_good(candidates: list[dict], dest: str) -> dict | None:
    for item in candidates:
        try:
            download(item["url"], dest)
        except requests.RequestException:
            continue
        if _looks_like_checkerboard(dest) or _looks_too_blank(dest):
            os.remove(dest)
            continue
        return item
    return None


def fetch_footage_for_scenes(scenes: list[dict], source: str = "openverse") -> list[dict]:
    os.makedirs(OUT_DIR, exist_ok=True)
    blocked = _load_blocklist()
    search_fn = search_nasa_candidates if source == "nasa" else search_candidates
    fallback_queries = NASA_FALLBACK_QUERIES if source == "nasa" else FALLBACK_QUERIES

    for i, scene in enumerate(scenes):
        keyword = scene["keyword"]
        candidates = []
        is_fallback = False
        try:
            candidates = search_fn(keyword, blocked)
        except requests.RequestException as e:
            print(f"scene {i}: search failed for '{keyword}': {e}", file=sys.stderr)

        dest = os.path.join(OUT_DIR, f"scene_{i:02d}.jpg")
        result = _download_first_good(candidates, dest) if candidates else None

        if not result:
            is_fallback = True
            fallback_query = random.choice(fallback_queries)
            print(f"scene {i}: no good image for '{keyword}', trying fallback '{fallback_query}'", file=sys.stderr)
            try:
                fallback_candidates = search_fn(fallback_query, blocked)
                result = _download_first_good(fallback_candidates, dest)
            except requests.RequestException:
                result = None

        if result:
            scene["image_path"] = dest
            scene["is_fallback"] = is_fallback
            scene["attribution"] = {k: v for k, v in result.items() if k not in ("url", "id")}
            scene["_image_id"] = result["id"]
        else:
            scene["image_path"] = None
            scene["attribution"] = None
    return scenes


if __name__ == "__main__":
    data = json.load(sys.stdin)
    scenes = fetch_footage_for_scenes(data["scenes"])
    data["scenes"] = scenes
    print(json.dumps(data, indent=2))
