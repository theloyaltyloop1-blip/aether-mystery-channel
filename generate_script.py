"""
AETHER - script generator
Calls a local Ollama model (free, runs on your machine) to turn a topic into a
scene-by-scene documentary narration script. Each scene has narration text and
a short footage search keyword (used later to pull matching NASA imagery).
"""
import json
import re
import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

MAX_SCENES = 5  # keeps total narration under ~55s for YouTube Shorts

# Phrases the local model leans on constantly - they're the #1 tell that a
# script is AI-written. Called out explicitly because "don't sound like AI"
# alone doesn't work on a 3b model; it needs the exact crutches named.
BANNED_PHRASES = [
    "to this day", "remains a mystery", "remains unsolved", "eerie", "chilling",
    "little did", "small town", "delve into", "dive into", "in the annals of",
    "shrouded in mystery", "the truth is out there", "conspiracy theories abound",
    "against all odds", "in a shocking turn of events", "as fate would have it",
    "one thing is certain", "the rest is history", "and it changed everything",
]

PROMPT_TEMPLATE = """You're a friend telling someone a genuinely unsettling true story you read about, in a \
voice memo, not narrating a documentary. Talk like a person, not a script. Under 60 seconds spoken.

Topic: {topic}

Write EXACTLY 4 to 5 beats that tell the story fast: what happened, the strange part, what people found \
(or didn't), how it was left. Output EXACTLY one line per beat, narration and keyword on the SAME line, \
separated by a single "|" character.

Example of the exact format and voice (follow the tone precisely, not the topic):
So this pilot takes off from a small airfield and just never checks back in, no mayday, nothing.|small plane airfield runway
Radar has him flying dead straight for another forty minutes with no response to calls.|radar screen tracking line
Then the signal just stops. No crash site, no debris field, nothing.|search plane over water
They still don't know what he was flying toward.|old newspaper clipping headline

Rules:
- Plain spoken language. Contractions (didn't, wasn't, couldn't). Vary sentence length - mix a short punch \
with a longer one, don't make every line the same shape. Keep each line under 22 words.
- Never use any of these words or phrases, they're a dead giveaway of AI writing: {banned}
- No scene numbers, no headers, no markdown, no blank lines, no extra commentary, no quotation marks
- footage keyword: 2-4 plain words for real archival-style imagery (aircraft, radar, maps, search boats, \
old newspapers, etc.)
- Do not invent specific names, dates, or numbers you're not sure are real - keep it general instead of \
fabricating a fact
- Output ONLY the pipe-separated lines, nothing before or after
"""


def _call_model(topic: str, temperature: float) -> str:
    prompt = PROMPT_TEMPLATE.format(topic=topic, banned=", ".join(BANNED_PHRASES))
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": temperature}},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def _contains_banned_phrase(narration: str) -> bool:
    lowered = narration.lower()
    return any(phrase in lowered for phrase in BANNED_PHRASES)


def _parse_scenes(text: str) -> list[dict]:
    scenes = []
    pending_narration = None
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("-* ").strip()
        if not line:
            continue
        line = re.sub(r"^\d+[\.\)]\s*", "", line)  # strip leading "1. " numbering

        if "|" in line:
            narration, keyword = line.split("|", 1)
            narration = narration.strip().strip('"').lstrip("|").strip()
            keyword = keyword.strip().strip('"').strip("|").strip()
            keyword = re.sub(r"^footage:?\s*", "", keyword, flags=re.IGNORECASE)
            if not narration and pending_narration:
                narration = pending_narration
                pending_narration = None
            if narration and keyword:
                scenes.append({"narration": narration, "keyword": keyword})
            else:
                pending_narration = narration or pending_narration
        else:
            # narration and keyword landed on separate lines - stash narration, wait for keyword
            pending_narration = line

    return scenes


def generate_script(topic: str) -> list[dict]:
    text = _call_model(topic, temperature=0.85)
    scenes = [s for s in _parse_scenes(text) if not _contains_banned_phrase(s["narration"])]

    if len(scenes) < 3:
        # either parsing came up short or too many lines got filtered for
        # cliche AI phrasing - one retry at higher temperature usually clears it
        text2 = _call_model(topic, temperature=1.0)
        more = [s for s in _parse_scenes(text2) if not _contains_banned_phrase(s["narration"])]
        seen = {s["narration"] for s in scenes}
        scenes += [s for s in more if s["narration"] not in seen]

    return scenes[:MAX_SCENES]


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "black holes"
    scenes = generate_script(topic)
    if not scenes:
        print("No scenes parsed - check Ollama is running and model is pulled.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"topic": topic, "scenes": scenes}, indent=2))
