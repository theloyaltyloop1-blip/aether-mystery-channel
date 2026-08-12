"""
AETHER - Wikipedia grounding
Free, no API key. Fetches a plain-text extract for a topic so the script
generator can be forced to only use real, verifiable facts instead of
inventing plausible-sounding details - a local 3b model asked to "be
accurate" from memory alone will still fabricate specifics.
"""
import requests

API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "AETHER-pipeline/1.0 (personal project)"}
MAX_CHARS = 2500  # keeps the grounding text short enough for a 3b model's context


def _search_title(topic: str) -> str | None:
    resp = requests.get(
        API_URL,
        params={"action": "query", "list": "search", "srsearch": topic, "format": "json", "srlimit": 1},
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()
    results = resp.json().get("query", {}).get("search", [])
    return results[0]["title"] if results else None


def get_grounding_text(topic: str) -> str | None:
    """Returns a trimmed plain-text Wikipedia extract for the topic, or None
    if no matching article was found."""
    try:
        title = _search_title(topic)
        if not title:
            return None
        resp = requests.get(
            API_URL,
            params={
                "action": "query", "prop": "extracts", "explaintext": 1,
                "titles": title, "format": "json",
            },
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "").strip()
            if extract:
                return extract[:MAX_CHARS]
        return None
    except requests.RequestException:
        return None


if __name__ == "__main__":
    import sys
    text = get_grounding_text(" ".join(sys.argv[1:]) or "the Mary Celeste")
    print(text or "No article found.")
