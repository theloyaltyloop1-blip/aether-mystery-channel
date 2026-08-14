"""AETHER channel: Space/science facts, narrated Wikipedia-grounded Shorts
using NASA's own public-domain image library instead of general stock
search - avoids the "random unrelated result" problem general keyword
search hit on other channels, since NASA's collection is narrowly
space/aeronautics content."""
import os

from script_engine import ChannelSpec
from topic_picker import make_topic_picker

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

NAME = "space"
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret_space.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token_space.json")
USED_TOPICS_FILE = os.path.join(BASE_DIR, "assets", "used_topics_space.json")
MADE_FOR_KIDS = False
CATEGORY_ID = "28"  # Science & Technology
VOICE = "en-US-AriaNeural"  # free edge-tts voice, bright/confident - fits genuine wonder tone
FOOTAGE_SOURCE = "nasa"  # NASA Image and Video Library instead of Openverse

SEED_TOPICS = [
    "the discovery of the Higgs boson",
    "how black holes form",
    "the Voyager 1 golden record",
    "the search for exoplanets",
    "the Apollo 11 moon landing",
    "the James Webb Space Telescope's first images",
    "how neutron stars form",
    "the Great Red Spot on Jupiter",
    "the discovery of water on Mars",
    "the International Space Station",
    "the life cycle of stars",
    "how the Hubble Space Telescope works",
    "the Chicxulub asteroid impact that ended the dinosaurs",
    "the aurora borealis (northern lights)",
    "the possibility of life on Europa",
    "the Perseverance rover on Mars",
    "what happens at a black hole's event horizon",
    "the Big Bang theory",
    "the first detection of gravitational waves",
    "the Cassini mission to Saturn",
    "the asteroid belt between Mars and Jupiter",
    "the Kuiper Belt and Pluto",
    "solar flares and coronal mass ejections",
    "the Fermi paradox",
    "dark matter and dark energy",
    "the Galilean moons of Jupiter",
    "white dwarf stars and the Chandrasekhar limit",
    "the Drake equation",
    "the James Webb Space Telescope's most distant galaxies",
    "the Chelyabinsk meteor",
    "the discovery of Pluto",
]

INVENT_PROMPT = (
    "Suggest ONE real, verifiable space or astronomy fact, discovery, or mission suitable for a short "
    "science documentary. Reply with ONLY the topic phrase, no extra text."
)

pick_topic, preview_topics = make_topic_picker(USED_TOPICS_FILE, SEED_TOPICS, INVENT_PROMPT)

BANNED_PHRASES = [
    "in this video", "in today's video", "let's dive in", "let's dive into",
    "without further ado", "at the end of the day", "in conclusion", "to sum up",
    "here's the thing", "the truth is", "mind-blowing", "believe it or not",
    "did you know that", "buckle up", "get ready for this", "picture this",
    "imagine this", "here's a fact that will blow your mind", "science says",
]

HOOK_OPENERS = [
    "Here's something that sounds impossible but isn't:", "Scientists genuinely didn't expect this:",
    "This is one of the strangest facts in astronomy:", "NASA didn't plan for this to happen:",
    "Here's a number that's almost too big to picture:", "Astronomers still argue about this one:",
    "This is what actually happens when a star dies:", "Here's something most people get wrong about space:",
]

PROMPT_TEMPLATE = """You're a curious friend explaining a real, genuinely fascinating space or science fact - \
plain, direct, full of real wonder but not breathless hype. Under 60 seconds spoken. This is real science, \
not speculation - accuracy matters.

Topic: {topic}

{reference_section}

Write EXACTLY 4 to 5 beats: the hook, what the fact actually is, why it's true/how it works, a concrete \
detail that makes it click. Output EXACTLY one line per beat, narration and keyword on the SAME line, \
separated by a single "|" character.

Example of the exact format and voice (follow the tone precisely, not the topic):
Here's something that sounds impossible but isn't: Voyager 1 is over 15 billion miles away and still transmitting.|voyager spacecraft deep space
It's been flying since 1977, and it's now the most distant human-made object in existence.|voyager spacecraft launch
Its radio signal takes over 22 hours to reach Earth, one way.|deep space network antenna
It's still sending data with less computing power than a modern calculator.|spacecraft instruments panel

Rules:
- THE FIRST LINE IS THE HOOK. Start it with one of these exact lead-ins, pick whichever fits best: \
{hooks}. Immediately after the lead-in, state the actual fact in plain terms. Someone scrolling should \
stop because the fact itself is interesting, not because of vague teasing.
- ACCURACY IS MANDATORY. {accuracy_rule}
- Plain spoken language. Contractions (it's, doesn't, isn't). Vary sentence length. Keep each line under \
22 words. Sound like someone who's genuinely fascinated, not narrating a trailer.
- Never use any of these words or phrases, they're a dead giveaway of generic AI science-content: {banned}
- No scene numbers, no headers, no markdown, no blank lines, no extra commentary, no quotation marks
- footage keyword: 2-4 plain words describing real NASA imagery (a planet, galaxy, spacecraft, telescope, \
astronaut, nebula, etc. - avoid overly specific mission jargon that NASA's image library might not have)
- Do not invent numbers, dates, or specific claims you're not sure are real - keep it general if uncertain
- Output ONLY the pipe-separated lines, nothing before or after
"""

GROUNDED_ACCURACY_RULE = (
    "Every specific claim - numbers, dates, mission names, what was/wasn't discovered - must come from the "
    "REFERENCE TEXT above. Do not add any figure or fact that isn't in that text, even if it sounds plausible."
)
UNGROUNDED_ACCURACY_RULE = (
    "No reference text was available for this topic, so only state facts you are genuinely certain are real "
    "and would appear in a standard encyclopedia summary. Do not invent specific numbers or dates - describe "
    "things in general terms instead of making up a precise figure you're not sure of."
)

SPEC = ChannelSpec(
    prompt_template=PROMPT_TEMPLATE,
    banned_phrases=BANNED_PHRASES,
    hook_openers=HOOK_OPENERS,
    max_scenes=5,
    use_grounding=True,
    grounded_accuracy_rule=GROUNDED_ACCURACY_RULE,
    ungrounded_accuracy_rule=UNGROUNDED_ACCURACY_RULE,
)


def generate_script(topic: str) -> list[dict]:
    from script_engine import generate_script as _generate
    return _generate(SPEC, topic)


def build_youtube_metadata(topic: str, credits: str) -> tuple[str, str, list[str]]:
    title = f"{topic[:80]} #Shorts"
    description = f"{topic} #Shorts #space #science\n\nGenerated by AETHER." + (f"\n\n{credits}" if credits else "")
    tags = ["space", "science", "astronomy", "nasa", "universe", "shorts"]
    return title, description, tags
