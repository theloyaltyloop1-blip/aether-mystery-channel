"""AETHER channel: mystery/aviation Shorts (the original channel)."""
import os

from script_engine import ChannelSpec
from topic_picker import make_topic_picker

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

NAME = "mystery"
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
USED_TOPICS_FILE = os.path.join(BASE_DIR, "assets", "used_topics.json")
MADE_FOR_KIDS = False
CATEGORY_ID = "27"  # Education

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

INVENT_PROMPT = (
    "Suggest ONE real unsolved mystery, aviation disappearance, or strange unexplained historical "
    "event suitable for a short mystery documentary. Reply with ONLY the topic phrase, no extra text."
)

pick_topic, preview_topics = make_topic_picker(USED_TOPICS_FILE, SEED_TOPICS, INVENT_PROMPT)

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

Example of the exact FORMAT and VOICE only - it is about a completely different case, so do not reuse \
any of its facts, story, or wording. Every line you write must be new content specifically about {topic}:
{example}

Rules:
- THE EXAMPLE ABOVE IS A TONE REFERENCE ONLY. It is not about {topic}. If your output shares its story, \
its facts, or close paraphrases of its wording, that is a failure - write entirely new content instead.
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

EXAMPLES = [
    """Listen to this: a pilot took off from a small airfield and never checked in again - no mayday, nothing.|small plane airfield runway
Radar had him flying dead straight for another forty minutes with no response to calls.|radar screen tracking line
Then the signal just stopped. No crash site, no debris field, nothing.|search plane over water
Nobody has ever explained what he was flying toward.|old newspaper clipping headline""",
    """You need to hear this one: a fully-stocked ship was found drifting with the entire crew gone.|abandoned ship deck
No lifeboats missing, no signs of struggle, food still on the table.|old ship interior
Whatever happened, it happened fast enough that nobody grabbed anything on the way out.|ocean horizon empty
The crew was never found, not one body, not one clue.|search boats ocean""",
    """Here's a case that still doesn't add up: three lighthouse keepers vanished without a trace.|lighthouse cliff coast
The light was still running, the table was set for dinner, but the men were gone.|lighthouse interior table
One oilskin coat was left behind, like whoever wore it left in the middle of something.|old coat weathered
Nobody has ever explained what took them off that rock.|stormy sea cliffs""",
]

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

SPEC = ChannelSpec(
    prompt_template=PROMPT_TEMPLATE,
    banned_phrases=BANNED_PHRASES,
    hook_openers=HOOK_OPENERS,
    examples=EXAMPLES,
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
    description = f"{topic} #Shorts #mystery\n\nGenerated by AETHER." + (f"\n\n{credits}" if credits else "")
    tags = ["mystery", "unsolved", "aviation", "documentary", "shorts"]
    return title, description, tags
