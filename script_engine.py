"""
AETHER - shared script generation engine
The actual LLM call, output parsing, and hook/quality retry logic is the
same regardless of channel/niche - what differs per channel is the prompt
template, banned phrases, hook lead-ins, and whether facts need Wikipedia
grounding at all (fiction and curated-content channels don't). Each channel
module builds a ChannelSpec and calls generate_script(spec, topic).
"""
import random
import re
from dataclasses import dataclass, field

import requests

from wiki_lookup import get_grounding_text

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


@dataclass
class ChannelSpec:
    prompt_template: str  # must have {topic} {reference_section} {accuracy_rule} {banned} {hooks} placeholders
    banned_phrases: list[str]
    hook_openers: list[str]
    max_scenes: int = 5
    use_grounding: bool = True  # False for fiction/curated content - no real-world facts to check
    grounded_accuracy_rule: str = ""
    ungrounded_accuracy_rule: str = ""
    temperature: float = 0.85
    retry_temperature: float = 1.0


def _call_model(spec: ChannelSpec, topic: str, temperature: float, reference: str | None) -> str:
    hooks = ", ".join(f'"{h}"' for h in spec.hook_openers)
    if reference:
        reference_section = f"REFERENCE TEXT (the only source of facts you're allowed to use):\n{reference}"
        accuracy_rule = spec.grounded_accuracy_rule
    else:
        reference_section = ""
        accuracy_rule = spec.ungrounded_accuracy_rule

    prompt = spec.prompt_template.format(
        topic=topic, banned=", ".join(spec.banned_phrases), hooks=hooks,
        reference_section=reference_section, accuracy_rule=accuracy_rule,
    )
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": temperature}},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def _contains_banned_phrase(spec: ChannelSpec, narration: str) -> bool:
    lowered = narration.lower()
    return any(phrase in lowered for phrase in spec.banned_phrases)


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
            pending_narration = line

    return scenes


def _has_approved_opener(spec: ChannelSpec, narration: str) -> bool:
    lowered = narration.lower().strip()
    return any(lowered.startswith(opener.lower()) for opener in spec.hook_openers)


def _weak_hook(spec: ChannelSpec, raw_scenes: list[dict]) -> bool:
    if not raw_scenes:
        return True
    first = raw_scenes[0]["narration"]
    return _contains_banned_phrase(spec, first) or not _has_approved_opener(spec, first)


def generate_script(spec: ChannelSpec, topic: str) -> list[dict]:
    reference = get_grounding_text(topic) if spec.use_grounding else None
    raw = _parse_scenes(_call_model(spec, topic, spec.temperature, reference))

    if _weak_hook(spec, raw) or len(raw) < 3:
        raw2 = _parse_scenes(_call_model(spec, topic, spec.retry_temperature, reference))
        if not _weak_hook(spec, raw2) or _weak_hook(spec, raw):
            raw = raw2

    if raw and not _has_approved_opener(spec, raw[0]["narration"]):
        opener = random.choice(spec.hook_openers)
        raw[0] = {**raw[0], "narration": f"{opener} {raw[0]['narration']}"}

    scenes = [s for s in raw if not _contains_banned_phrase(spec, s["narration"])]
    return scenes[: spec.max_scenes]
