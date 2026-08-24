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
    # must have {topic} {reference_section} {accuracy_rule} {banned} {hooks} {example} placeholders
    prompt_template: str
    banned_phrases: list[str]
    hook_openers: list[str]
    examples: list[str] = field(default_factory=list)  # rotated per call, see note below
    max_scenes: int = 5
    use_grounding: bool = True  # False for fiction/curated content - no real-world facts to check
    grounded_accuracy_rule: str = ""
    ungrounded_accuracy_rule: str = ""
    temperature: float = 0.85
    retry_temperature: float = 1.0
    # appended as a guaranteed extra final scene, not left to the model -
    # retention is already strong (72-80% avg view %) but nothing was ever
    # asking viewers to subscribe, so it was pure wasted attention
    subscribe_ctas: list[str] = field(default_factory=list)
    cta_keyword: str = ""  # footage keyword for the CTA scene; falls back to the last real scene's keyword


def _call_model(spec: ChannelSpec, topic: str, temperature: float, reference: str | None) -> str:
    # a weak model tends to just default to whichever hook is listed first -
    # shuffling the order each call spreads picks across all of them instead
    # of one opener dominating every video
    shuffled_hooks = spec.hook_openers[:]
    random.shuffle(shuffled_hooks)
    hooks = ", ".join(f'"{h}"' for h in shuffled_hooks)
    if reference:
        reference_section = f"REFERENCE TEXT (the only source of facts you're allowed to use):\n{reference}"
        accuracy_rule = spec.grounded_accuracy_rule
    else:
        reference_section = ""
        accuracy_rule = spec.ungrounded_accuracy_rule

    # llama3.2:3b is small enough that a single fixed worked example becomes
    # an "attractor" - it was observed reproducing the SAME example's story
    # almost every generation regardless of the actual topic requested.
    # Rotating between several examples (plus the copy-detection retry below)
    # stops any one story from dominating every video.
    example = random.choice(spec.examples) if spec.examples else ""

    prompt = spec.prompt_template.format(
        topic=topic, banned=", ".join(spec.banned_phrases), hooks=hooks,
        reference_section=reference_section, accuracy_rule=accuracy_rule, example=example,
    )
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": temperature}},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip(), example


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


_WORD_RE = re.compile(r"[a-z0-9']+")


def _copied_from_example(raw_scenes: list[dict], example: str) -> bool:
    """A small local model can fall back to reproducing the worked example's
    actual story instead of writing about the requested topic - this was
    observed happening almost every generation with a single fixed example.
    Flags it by looking for a long run of shared words between the output
    and the example, which a genuinely new script about a different topic
    won't have even after paraphrasing word choice slightly."""
    if not example or not raw_scenes:
        return False
    example_words = _WORD_RE.findall(example.lower())
    for scene in raw_scenes:
        scene_words = _WORD_RE.findall(scene["narration"].lower())
        for i in range(len(scene_words) - 4):
            window = " ".join(scene_words[i : i + 5])
            if window in " ".join(example_words):
                return True
    return False


def _too_short(raw_scenes: list[dict]) -> bool:
    """A generation hiccup can produce a technically-valid but near-empty
    script (one real video ended up 6 seconds long) - a normal script runs
    well over 60 words across its beats, so anything under 20 is broken,
    not just terse."""
    total_words = sum(len(s["narration"].split()) for s in raw_scenes)
    return total_words < 20


def _is_bad(spec: ChannelSpec, raw_scenes: list[dict], example: str) -> bool:
    return (
        _weak_hook(spec, raw_scenes)
        or len(raw_scenes) < 3
        or _too_short(raw_scenes)
        or _copied_from_example(raw_scenes, example)
    )


def generate_script(spec: ChannelSpec, topic: str) -> list[dict]:
    reference = get_grounding_text(topic) if spec.use_grounding else None
    text, example = _call_model(spec, topic, spec.temperature, reference)
    raw = _parse_scenes(text)

    if _is_bad(spec, raw, example):
        text2, example2 = _call_model(spec, topic, spec.retry_temperature, reference)
        raw2 = _parse_scenes(text2)
        if not _is_bad(spec, raw2, example2) or _is_bad(spec, raw, example):
            raw = raw2

    if raw and not _has_approved_opener(spec, raw[0]["narration"]):
        opener = random.choice(spec.hook_openers)
        raw[0] = {**raw[0], "narration": f"{opener} {raw[0]['narration']}"}

    scenes = [s for s in raw if not _contains_banned_phrase(spec, s["narration"])]
    scenes = scenes[: spec.max_scenes]

    if scenes and spec.subscribe_ctas:
        cta_keyword = spec.cta_keyword or scenes[-1]["keyword"]
        scenes.append({"narration": random.choice(spec.subscribe_ctas), "keyword": cta_keyword})

    return scenes
