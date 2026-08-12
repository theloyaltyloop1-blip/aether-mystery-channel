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
import requests

OPENVERSE_URL = "https://api.openverse.org/v1/images/"
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


def search_image(keyword: str, blocked: set[str]) -> dict | None:
    resp = requests.get(
        OPENVERSE_URL,
        params={
            "q": keyword,
            "license_type": "commercial,modification",
            "page_size": 10,
            "mature": "false",
        },
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    results = [r for r in resp.json().get("results", []) if r.get("url") and r.get("id") not in blocked]
    if not results:
        return None

    # pick randomly among the top few rather than always the first hit -
    # avoids the same "best match" recurring across unrelated videos
    item = random.choice(results[:5])
    return {
        "id": item["id"],
        "url": item["url"],
        "title": item.get("title") or "Untitled",
        "creator": item.get("creator") or "Unknown",
        "license": (item.get("license") or "").upper(),
        "license_version": item.get("license_version") or "",
        "license_url": item.get("license_url") or "",
        "source_url": item.get("foreign_landing_url") or item.get("url"),
    }


def download(url: str, dest_path: str) -> None:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)


def fetch_footage_for_scenes(scenes: list[dict]) -> list[dict]:
    os.makedirs(OUT_DIR, exist_ok=True)
    blocked = _load_blocklist()

    for i, scene in enumerate(scenes):
        keyword = scene["keyword"]
        result = None
        is_fallback = False
        try:
            result = search_image(keyword, blocked)
        except requests.RequestException as e:
            print(f"scene {i}: search failed for '{keyword}': {e}", file=sys.stderr)

        if not result:
            is_fallback = True
            fallback_query = random.choice(FALLBACK_QUERIES)
            print(f"scene {i}: no image found for '{keyword}', trying fallback '{fallback_query}'", file=sys.stderr)
            try:
                result = search_image(fallback_query, blocked)
            except requests.RequestException:
                result = None

        dest = os.path.join(OUT_DIR, f"scene_{i:02d}.jpg")
        if result:
            try:
                download(result["url"], dest)
                scene["image_path"] = dest
                scene["is_fallback"] = is_fallback
                scene["attribution"] = {k: v for k, v in result.items() if k not in ("url", "id")}
                scene["_image_id"] = result["id"]
            except requests.RequestException as e:
                print(f"scene {i}: download failed: {e}", file=sys.stderr)
                scene["image_path"] = None
                scene["attribution"] = None
        else:
            scene["image_path"] = None
            scene["attribution"] = None
    return scenes


if __name__ == "__main__":
    data = json.load(sys.stdin)
    scenes = fetch_footage_for_scenes(data["scenes"])
    data["scenes"] = scenes
    print(json.dumps(data, indent=2))
