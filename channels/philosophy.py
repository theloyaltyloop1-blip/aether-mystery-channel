"""AETHER channel: Philosophy - "Master Your Mind", a serialized 30-part
Stoicism series (Marcus Aurelius, Seneca, Epictetus), 3 parts/day."""
import os

from script_engine import ChannelSpec
from topic_picker import make_topic_picker

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

NAME = "philosophy"
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret_philosophy.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token_philosophy.json")
USED_TOPICS_FILE = os.path.join(BASE_DIR, "assets", "used_topics_philosophy.json")
MADE_FOR_KIDS = False
CATEGORY_ID = "27"  # Education

# Ordered - the topic picker walks this list in order, so this IS the
# "Part 1, Part 2, ... Part 30" release sequence.
SEED_TOPICS = [
    "Master Your Mind Part 1: what you can and cannot control (Epictetus)",
    "Master Your Mind Part 2: Marcus Aurelius on facing a hard day before it starts",
    "Master Your Mind Part 3: Seneca on the shortness of life",
    "Master Your Mind Part 4: the Stoic view on controlling anger",
    "Master Your Mind Part 5: why external things can't actually hurt you (Epictetus)",
    "Master Your Mind Part 6: Marcus Aurelius on dealing with difficult people",
    "Master Your Mind Part 7: Seneca's advice on what true wealth means",
    "Master Your Mind Part 8: the dichotomy of control explained",
    "Master Your Mind Part 9: why the Stoics practiced negative visualization",
    "Master Your Mind Part 10: Marcus Aurelius reflecting on his own mortality",
    "Master Your Mind Part 11: Epictetus on the freedom and slavery of the mind",
    "Master Your Mind Part 12: Seneca on wasting time",
    "Master Your Mind Part 13: the Stoic response to insult",
    "Master Your Mind Part 14: Marcus Aurelius on seeing all people as connected",
    "Master Your Mind Part 15: why the Stoics welcomed obstacles",
    "Master Your Mind Part 16: Epictetus on desire and aversion",
    "Master Your Mind Part 17: Seneca on grief and loss",
    "Master Your Mind Part 18: Marcus Aurelius's daily journaling practice",
    "Master Your Mind Part 19: the four Stoic virtues",
    "Master Your Mind Part 20: why the Stoics did not fear death",
    "Master Your Mind Part 21: Epictetus on the role you are given to play",
    "Master Your Mind Part 22: Seneca on true friendship",
    "Master Your Mind Part 23: Marcus Aurelius on ambition and legacy",
    "Master Your Mind Part 24: the Stoic view that complaining changes nothing",
    "Master Your Mind Part 25: the Stoic practice of Amor Fati, loving your fate",
    "Master Your Mind Part 26: Epictetus on not being ruled by other people's opinions",
    "Master Your Mind Part 27: Seneca's letters on self-improvement",
    "Master Your Mind Part 28: Marcus Aurelius on the obstacle becoming the way",
    "Master Your Mind Part 29: the Stoic definition of a good life",
    "Master Your Mind Part 30: putting it all together, living like a Stoic",
]

INVENT_PROMPT = (
    "Suggest ONE real Stoic philosophy lesson, quote, or teaching from Marcus Aurelius, Seneca, or "
    "Epictetus suitable for a short 'master your mind' self-improvement video. Reply with ONLY the "
    "topic phrase, no extra text."
)

pick_topic, preview_topics = make_topic_picker(USED_TOPICS_FILE, SEED_TOPICS, INVENT_PROMPT)

BANNED_PHRASES = [
    "in this video", "in today's video", "let's dive in", "let's dive into",
    "without further ado", "at the end of the day", "in conclusion", "to sum up",
    "here's the thing", "the truth is", "little did they know", "unlock your potential",
    "level up your life", "game changer", "life hack", "here's a secret",
    "ancient wisdom holds the key", "the secret to happiness", "believe it or not",
]

HOOK_OPENERS = [
    "Marcus Aurelius said this to himself every single morning:", "Here's what the Stoics knew that most people don't:",
    "This one idea will change how you see everything:", "2,000 years ago, someone already figured this out:",
    "If you remember nothing else today, remember this:", "This is the exact thought that got Marcus Aurelius through ruling an empire:",
    "Seneca wrote this to a friend who was falling apart:", "Epictetus was a slave who taught emperors this lesson:",
]

PROMPT_TEMPLATE = """You're a warm, encouraging self-improvement coach sharing a real Stoic idea with someone \
who wants to build a better, calmer, stronger life - upbeat and motivating, not heavy, not doom-and-gloom, \
not lecturing. Frame everything around the concrete upside: what the person gains by living this way (calm, \
confidence, better relationships, resilience, focus, self-respect). Under 60 seconds spoken. This is real \
philosophy, not made-up fluff - accuracy still matters even though the tone is upbeat.

Topic: {topic}

{reference_section}

Write EXACTLY 4 to 5 beats: the hook, what the idea actually is, why it works, a concrete positive way to \
use it today. Output EXACTLY one line per beat, narration and keyword on the SAME line, separated by a \
single "|" character.

Example of the exact format and voice (follow the tone precisely, not the topic):
Marcus Aurelius started every morning the same way: he pictured the hardest parts of his day before they happened.|marcus aurelius statue bust
That's not pessimism, it's preparation - and it's why nothing could throw him off balance.|roman forum ruins
When you expect friction, you respond instead of react, and that alone makes you calmer all day.|ancient roman scroll manuscript
Try it tomorrow: picture one hard moment before it happens, and watch how much easier it feels.|sunrise ancient architecture

Rules:
- THE FIRST LINE IS THE HOOK. Start it with one of these exact lead-ins, pick whichever fits best: \
{hooks}. Immediately after the lead-in, state the actual idea in plain, positive terms. Someone scrolling \
should stop because the idea itself sounds genuinely useful, not because of vague teasing or fear.
- KEEP IT UPBEAT. Lead with what the person gains, not what they're doing wrong or what they should fear. \
Avoid dwelling on suffering, death, or how hard/short life is - even where the source material touches on \
those themes, pull out the encouraging, empowering angle instead.
- ACCURACY IS MANDATORY. {accuracy_rule}
- Plain spoken language. Contractions (didn't, wasn't, isn't). Vary sentence length. Keep each line under \
22 words. Sound like a coach who genuinely believes this helps, not a lecture.
- Never use any of these words or phrases, they're a dead giveaway of generic AI self-help content: {banned}
- No scene numbers, no headers, no markdown, no blank lines, no extra commentary, no quotation marks
- footage keyword: 2-4 plain words for real imagery that fits (classical statues, Roman/Greek ruins, \
ancient manuscripts, nature, historical art, philosophers' busts, etc.)
- Do not invent quotes, dates, or specific claims you're not sure are real - keep it general if uncertain
- Output ONLY the pipe-separated lines, nothing before or after
"""

GROUNDED_ACCURACY_RULE = (
    "Every specific claim - quotes, events, what a philosopher actually said or did - must come from the "
    "REFERENCE TEXT above. Do not invent or paraphrase a direct quote that isn't clearly supported by that "
    "text. If unsure, describe the idea in your own words instead of attributing an invented quote."
)
UNGROUNDED_ACCURACY_RULE = (
    "No reference text was available, so only state ideas widely known to be core Stoic teachings from "
    "Marcus Aurelius, Seneca, or Epictetus. Do not invent specific quotes or attribute claims to a "
    "philosopher unless you're genuinely confident it's accurate - describe the idea generally instead."
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
    description = f"{topic} #Shorts #stoicism #philosophy\n\nGenerated by AETHER." + (f"\n\n{credits}" if credits else "")
    tags = ["stoicism", "philosophy", "marcus aurelius", "seneca", "epictetus", "selfimprovement", "shorts"]
    return title, description, tags
