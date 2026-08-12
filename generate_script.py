"""
AETHER - script generator
Calls a local Ollama model (free, runs on your machine) to turn a topic into a
scene-by-scene documentary narration script. Each scene has narration text and
a short footage search keyword (used later to pull matching NASA imagery).
"""
import json
import random
import re
import sys
import requests

from wiki_lookup import get_grounding_text

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
    "we were reading", "so this crazy story", "picture this", "let me tell you",
    "you won't believe", "so basically", "so this is the story of", "imagine this",
    "here's a story", "have you ever heard", "so i was reading", "check this out",
]

HOOK_OPENERS = [
    "Listen to this:", "You need to hear this one:", "This is one of the strangest cases on record:",
    "Okay, this one's genuinely unsettling:", "Here's a case that still doesn't add up:",
    "This story is disturbing, and it's real:", "Wait until you hear how this one ends:",
    "This one's stuck with investigators for years:",
]

PROMPT_TEMPLATE = """You're a friend telling someone a genuinely unsettling TRUE story in a voice memo, not \
narrating a documentary. Talk like a person, not a script. Under 60 seconds spoken. Accuracy matters - this \
is a real case, not creative fiction.

Topic: {topic}

{reference_section}

Write EXACTLY 4 to 5 beats that tell the story fast: the hook, the strange part, what people found \
(or didn't), how it was left. Output EXACTLY one line per beat, narration and keyword on the SAME line, \
separated by a single "|" character.

Example of the exact format and voice (follow the tone precisely, not the topic):
Listen to this: a pilot took off from a small airfield and never checked in again - no mayday, nothing.|small plane airfield runway
Radar had him flying dead straight for another forty minutes with no response to calls.|radar screen tracking line
Then the signal just stopped. No crash site, no debris field, nothing.|search plane over water
They still don't know what he was flying toward.|old newspaper clipping headline

Rules:
- THE FIRST LINE IS THE HOOK. Start it with one of these exact lead-ins, pick whichever fits best: \
{hooks}. Immediately after the lead-in, in the SAME sentence or the one right after, state the single \
strangest, most well-documented fact of the real case. Someone scrolling should stop because of what you \
said, not because of vague teasing.
- ACCURACY IS MANDATORY. {accuracy_rule}
- Plain spoken language. Contractions (didn't, wasn't, couldn't). Vary sentence length - mix a short punch \
with a longer one, don't make every line the same shape. Keep each line under 22 words.
- Never use any of these words or phrases, they're a dead giveaway of AI writing: {banned}
- No scene numbers, no headers, no markdown, no blank lines, no extra commentary, no quotation marks
- footage keyword: 2-4 plain words for real archival-style imagery (aircraft, radar, maps, search boats, \
old newspapers, etc.)
- Do not invent specific names, dates, numbers, or any other fact you're not sure is real - keep it general \
if uncertain rather than fabricating
- Output ONLY the pipe-separated lines, nothing before or after
"""

GROUNDED_ACCURACY_RULE = (
    "Every specific fact you state - injuries, what was/wasn't found, causes, outcomes - must come from "
    "the REFERENCE TEXT above. Do not add any detail, cause, or outcome that isn't in that text, even if "
    "it sounds plausible. If the reference text doesn't mention something, don't claim it happened."
)
UNGROUNDED_ACCURACY_RULE = (
    "No reference text was available for this topic, so only state details you are genuinely certain are "
    "real and would appear in a standard encyclopedia summary. Do not invent injuries, causes, dialogue, or "
    "sensory specifics. When unsure of a precise detail, describe it in general terms instead of making "
    'something up (say "unexplained injuries" not a specific invented injury; say "was never found" not an '
    "invented detail about how)."
)


def _call_model(topic: str, temperature: float, reference: str | None) -> str:
    hooks = ", ".join(f'"{h}"' for h in HOOK_OPENERS)
    if reference:
        reference_section = f"REFERENCE TEXT (the only source of facts you're allowed to use):\n{reference}"
        accuracy_rule = GROUNDED_ACCURACY_RULE
    else:
        reference_section = ""
        accuracy_rule = UNGROUNDED_ACCURACY_RULE

    prompt = PROMPT_TEMPLATE.format(
        topic=topic, banned=", ".join(BANNED_PHRASES), hooks=hooks,
        reference_section=reference_section, accuracy_rule=accuracy_rule,
    )
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


def _has_approved_opener(narration: str) -> bool:
    lowered = narration.lower().strip()
    return any(lowered.startswith(opener.lower()) for opener in HOOK_OPENERS)


def _weak_hook(raw_scenes: list[dict]) -> bool:
    """A weak hook (banned meta-framing opener, missing the required
    lead-in, or nothing parsed at all) means the whole script should be
    regenerated, not just have that one line dropped - a good beat 2
    promoted to beat 1 was never written to work as an opener."""
    if not raw_scenes:
        return True
    first = raw_scenes[0]["narration"]
    return _contains_banned_phrase(first) or not _has_approved_opener(first)


def generate_script(topic: str) -> list[dict]:
    reference = get_grounding_text(topic)
    raw = _parse_scenes(_call_model(topic, temperature=0.85, reference=reference))

    if _weak_hook(raw) or len(raw) < 3:
        # weak/missing hook or a short parse - one retry at higher temperature
        raw2 = _parse_scenes(_call_model(topic, temperature=1.0, reference=reference))
        if not _weak_hook(raw2) or _weak_hook(raw):
            raw = raw2

    if raw and not _has_approved_opener(raw[0]["narration"]):
        # model still skipped the lead-in after a retry - force one on
        # rather than publishing a weak hook
        opener = random.choice(HOOK_OPENERS)
        raw[0] = {**raw[0], "narration": f"{opener} {raw[0]['narration']}"}

    scenes = [s for s in raw if not _contains_banned_phrase(s["narration"])]
    return scenes[:MAX_SCENES]


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "black holes"
    scenes = generate_script(topic)
    if not scenes:
        print("No scenes parsed - check Ollama is running and model is pulled.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"topic": topic, "scenes": scenes}, indent=2))
