"""
AETHER - shared topic picker
Same "walk a seed list in order, log what's used, invent more once
exhausted" logic every channel needs - only the seed list and the invent
prompt differ per channel.
"""
import json
import os
import re
import requests

# once a channel exhausts its seed list, invented topics come from a small
# local model that turned out to have a narrow "favorites list" - it kept
# re-suggesting the same handful of famous cases (the Dyatlov Pass incident
# alone was invented and published 11 times) with just enough wording
# variation to slip past an exact-string duplicate check. This normalizes
# and compares by shared significant words instead, so "the SS Central
# America disappearance" and "disappearance of SS Central America." are
# caught as the same topic.
_TOPIC_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "over", "and", "or", "to",
    "for", "with", "by", "why", "how", "what", "is", "are", "was", "were",
}


def _normalize_topic(topic: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", topic.lower())
    return {w for w in words if w not in _TOPIC_STOPWORDS}


def _too_similar(a: set[str], b: set[str]) -> bool:
    if not a or not b:
        return False
    overlap = len(a & b) / min(len(a), len(b))
    return overlap > 0.6


def make_topic_picker(used_topics_file: str, seed_topics: list[str], invent_prompt: str):
    def _load_used() -> list[str]:
        if not os.path.exists(used_topics_file):
            return []
        with open(used_topics_file, "r") as f:
            return json.load(f)

    def _save_used(used: list[str]) -> None:
        os.makedirs(os.path.dirname(used_topics_file), exist_ok=True)
        with open(used_topics_file, "w") as f:
            json.dump(used, f, indent=2)

    def _ask_model(used: list[str]) -> str:
        prompt = invent_prompt + "\nDo not suggest any of these already-covered topics:\n- " + "\n- ".join(used[-40:])
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2:3b", "prompt": prompt, "stream": False, "options": {"temperature": 1.0}},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip().strip('"').split("\n")[0]

    def _invent_topic(used: list[str]) -> str:
        used_word_sets = [_normalize_topic(t) for t in used]
        candidate = ""
        for _ in range(5):
            candidate = _ask_model(used)
            candidate_words = _normalize_topic(candidate)
            if not any(_too_similar(candidate_words, uw) for uw in used_word_sets):
                return candidate
        # gave up finding something distinct after 5 tries - use the last
        # attempt anyway rather than looping forever or failing the run
        return candidate

    def pick_topic() -> str:
        used = _load_used()
        remaining = [t for t in seed_topics if t not in used]

        if remaining:
            # stable ordering: keeps a serialized series (e.g. "Part 1, 2, 3...")
            # in order, and keeps the dashboard preview aligned with reality
            topic = remaining[0]
        else:
            topic = _invent_topic(used)

        used.append(topic)
        _save_used(used)
        return topic

    def preview_topics(count: int = 8) -> list[str]:
        used = _load_used()
        remaining = [t for t in seed_topics if t not in used]
        preview = remaining[:count]
        preview.extend(["AETHER discovery topic"] * (count - len(preview)))
        return preview

    return pick_topic, preview_topics
