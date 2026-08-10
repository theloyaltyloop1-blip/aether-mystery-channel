"""
AETHER - topic picker
Maintains a seed pool of mystery/aviation topics and a log of what's already
been made, so autonomous runs never repeat a topic. Once the seed pool is
exhausted, it asks the local LLM to invent a new one, explicitly excluding
everything already used.
"""
import json
import os
import random
import requests

USED_TOPICS_FILE = os.path.join(os.path.dirname(__file__), "assets", "used_topics.json")

SEED_TOPICS = [
    "the disappearance of Amelia Earhart over the Pacific",
    "the mysterious crash of Flight 19 in the Bermuda Triangle",
    "the vanishing of Malaysia Airlines Flight MH370",
    "the Dyatlov Pass incident",
    "the Roanoke colony's disappearance",
    "the Mary Celeste ghost ship",
    "the disappearance of Frederick Valentich over Bass Strait",
    "the crash and disappearance of Glenn Miller's plane",
    "the Sodder children disappearance",
    "the Tunguska event explosion",
    "the disappearance of the SS Cotopaxi",
    "the Lake Michigan Northwest Airlines Flight 2501 disappearance",
    "the Waldo Canyon UFO sightings and radar anomalies",
    "the disappearance of Steve Fossett",
    "the crash of Star Dust flight over the Andes",
    "the Kinross Incident jet disappearance over Lake Superior",
    "the Zanzibar radar ghost plane incident",
    "the disappearance of the British airship R101",
    "the crash of the Ourang Medan ghost ship",
    "the Bermuda Triangle disappearance of the USS Cyclops",
    "the unsolved 1971 D.B. Cooper hijacking",
    "the disappearance of the schooner Carroll A. Deering crew",
    "the vanishing of the Flannan Isles lighthouse keepers",
    "the mysterious explosion of the airship Hindenburg",
    "the disappearance of pilot Jean Batten's rival aviators",
    "the crash of Helios Airways Flight 522 ghost plane",
    "the unexplained radar loss of Varig Flight 967",
    "the disappearance of adventurer Percy Fawcett's expedition",
    "the strange case of the Taos Hum",
    "the disappearance of the crew of the Baychimo ghost ship",
]


def _load_used() -> list[str]:
    if not os.path.exists(USED_TOPICS_FILE):
        return []
    with open(USED_TOPICS_FILE, "r") as f:
        return json.load(f)


def _save_used(used: list[str]) -> None:
    os.makedirs(os.path.dirname(USED_TOPICS_FILE), exist_ok=True)
    with open(USED_TOPICS_FILE, "w") as f:
        json.dump(used, f, indent=2)


def _invent_topic(used: list[str]) -> str:
    prompt = (
        "Suggest ONE real unsolved mystery, aviation disappearance, or strange unexplained historical "
        "event suitable for a short mystery documentary. Reply with ONLY the topic phrase, no extra text.\n"
        "Do not suggest any of these already-covered topics:\n- " + "\n- ".join(used[-40:])
    )
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3.2:3b", "prompt": prompt, "stream": False, "options": {"temperature": 1.0}},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip().strip('"').split("\n")[0]


def pick_topic() -> str:
    used = _load_used()
    remaining = [t for t in SEED_TOPICS if t not in used]

    if remaining:
        topic = random.choice(remaining)
    else:
        topic = _invent_topic(used)

    used.append(topic)
    _save_used(used)
    return topic


if __name__ == "__main__":
    print(pick_topic())
