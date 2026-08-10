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
import sys
import requests

OPENVERSE_URL = "https://api.openverse.org/v1/images/"
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "footage")

HEADERS = {"User-Agent": "AETHER-pipeline/1.0 (personal project)"}


def search_image(keyword: str) -> dict | None:
    resp = requests.get(
        OPENVERSE_URL,
        params={
            "q": keyword,
            "license_type": "commercial,modification",
            "page_size": 5,
            "mature": "false",
        },
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    for item in results:
        if item.get("url"):
            return {
                "url": item["url"],
                "title": item.get("title") or "Untitled",
                "creator": item.get("creator") or "Unknown",
                "license": (item.get("license") or "").upper(),
                "license_version": item.get("license_version") or "",
                "license_url": item.get("license_url") or "",
                "source_url": item.get("foreign_landing_url") or item.get("url"),
            }
    return None


def download(url: str, dest_path: str) -> None:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)


def fetch_footage_for_scenes(scenes: list[dict]) -> list[dict]:
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, scene in enumerate(scenes):
        keyword = scene["keyword"]
        result = None
        try:
            result = search_image(keyword)
        except requests.RequestException as e:
            print(f"scene {i}: search failed for '{keyword}': {e}", file=sys.stderr)

        if not result:
            print(f"scene {i}: no image found for '{keyword}', trying fallback keyword", file=sys.stderr)
            try:
                result = search_image("mystery archive photo")
            except requests.RequestException:
                result = None

        dest = os.path.join(OUT_DIR, f"scene_{i:02d}.jpg")
        if result:
            try:
                download(result["url"], dest)
                scene["image_path"] = dest
                scene["attribution"] = {k: v for k, v in result.items() if k != "url"}
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
