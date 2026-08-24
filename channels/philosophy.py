"""AETHER channel: Philosophy - "Master Your Mind", a serialized 100-part
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
    "Master Your Mind Part 31: Marcus Aurelius on not wasting time arguing about what a good person looks like - just be one",
    "Master Your Mind Part 32: Seneca on the difference between existing and truly living",
    "Master Your Mind Part 33: Epictetus on why blaming others means you haven't started your own progress",
    "Master Your Mind Part 34: Marcus Aurelius on why chasing fame is a trap",
    "Master Your Mind Part 35: Seneca's advice on choosing friends wisely",
    "Master Your Mind Part 36: Epictetus on the dichotomy between what is 'up to us' and what is not",
    "Master Your Mind Part 37: Marcus Aurelius on the shortness of any single human life",
    "Master Your Mind Part 38: Seneca on why anger is a kind of temporary madness",
    "Master Your Mind Part 39: Epictetus on why you never 'lose' something, you only give it back",
    "Master Your Mind Part 40: Marcus Aurelius on treating obstacles as fuel, not blockers",
    "Master Your Mind Part 41: Seneca on premeditatio malorum, rehearsing hardship before it comes",
    "Master Your Mind Part 42: Epictetus on why insults only have the power you give them",
    "Master Your Mind Part 43: Marcus Aurelius on staying humble despite holding real power",
    "Master Your Mind Part 44: Seneca on why busyness is not the same as productivity",
    "Master Your Mind Part 45: Epictetus on training your mind like an athlete trains their body",
    "Master Your Mind Part 46: Marcus Aurelius on the Stoic idea of living according to nature",
    "Master Your Mind Part 47: Seneca on why revenge is beneath a wise person",
    "Master Your Mind Part 48: Epictetus's 'reserve clause' - wanting things to happen, but accepting if they don't",
    "Master Your Mind Part 49: Marcus Aurelius on why other people's opinions of you are none of your business",
    "Master Your Mind Part 50: Seneca on why holding onto anger costs more than the thing that caused it",
    "Master Your Mind Part 51: Epictetus on freedom meaning no false desires, not no constraints",
    "Master Your Mind Part 52: Marcus Aurelius on treating every interaction like it might be your last",
    "Master Your Mind Part 53: Seneca on simplifying your life down to what actually matters",
    "Master Your Mind Part 54: Epictetus on why comparison steals your calm",
    "Master Your Mind Part 55: Marcus Aurelius's reflections on ruling with justice instead of ego",
    "Master Your Mind Part 56: Seneca's letters on true friendship versus convenient friendship",
    "Master Your Mind Part 57: Epictetus on practicing philosophy daily instead of just reading about it",
    "Master Your Mind Part 58: Marcus Aurelius on the idea that the obstacle is the way",
    "Master Your Mind Part 59: Seneca on why wealth without wisdom brings no real peace",
    "Master Your Mind Part 60: Epictetus on accepting your role in life like an actor accepts their part",
    "Master Your Mind Part 61: Marcus Aurelius on why complaining changes nothing about your circumstances",
    "Master Your Mind Part 62: Seneca on the practice of examining your day each night",
    "Master Your Mind Part 63: Epictetus on testing your principles under real difficulty, not just in theory",
    "Master Your Mind Part 64: Marcus Aurelius on gratitude for what you have instead of grief for what you lack",
    "Master Your Mind Part 65: Seneca on why most people postpone living until it's too late",
    "Master Your Mind Part 66: Epictetus on the difference between what's yours and what's merely lent to you",
    "Master Your Mind Part 67: Marcus Aurelius on staying on your own path despite others' judgment",
    "Master Your Mind Part 68: Seneca on why constant travel doesn't fix an unsettled mind",
    "Master Your Mind Part 69: Epictetus on why your judgments, not events, disturb you",
    "Master Your Mind Part 70: Marcus Aurelius on treating setbacks as part of the plan, not exceptions to it",
    "Master Your Mind Part 71: Seneca on why fear of death wastes the life you actually have",
    "Master Your Mind Part 72: Epictetus on not seeking approval from people whose opinion doesn't matter",
    "Master Your Mind Part 73: Marcus Aurelius on kindness as a form of strength, not weakness",
    "Master Your Mind Part 74: Seneca on the value of solitude for a disciplined mind",
    "Master Your Mind Part 75: Epictetus on external events being actors, and your mind being the stage manager",
    "Master Your Mind Part 76: Marcus Aurelius on remembering everyone you meet is fighting their own battle",
    "Master Your Mind Part 77: Seneca on why leisure without purpose is its own kind of poverty",
    "Master Your Mind Part 78: Epictetus on controlling your effort, never the outcome",
    "Master Your Mind Part 79: Marcus Aurelius on the discipline of choosing what to believe about events",
    "Master Your Mind Part 80: Seneca on why some griefs are worse in anticipation than in reality",
    "Master Your Mind Part 81: Epictetus on being undisturbed, not indifferent",
    "Master Your Mind Part 82: Marcus Aurelius on character being built in ordinary moments, not crises",
    "Master Your Mind Part 83: Seneca on why borrowed opinions make a weak foundation for a life",
    "Master Your Mind Part 84: Epictetus on why criticism only wounds you if you agree with it",
    "Master Your Mind Part 85: Marcus Aurelius on choosing to see the world as connected rather than hostile",
    "Master Your Mind Part 86: Seneca on why hurry is usually a sign of poor planning, not real urgency",
    "Master Your Mind Part 87: Epictetus on how wanting what you can't control breeds constant disappointment",
    "Master Your Mind Part 88: Marcus Aurelius on facing criticism the way a rock faces waves",
    "Master Your Mind Part 89: Seneca on why philosophy is lived, not just studied",
    "Master Your Mind Part 90: Epictetus on the freedom that comes from wanting only what's actually yours",
    "Master Your Mind Part 91: Marcus Aurelius on why every morning is a chance to begin again",
    "Master Your Mind Part 92: Seneca on why comparing your progress to others distorts your own",
    "Master Your Mind Part 93: Epictetus on complaining about fate being a refusal to play your role well",
    "Master Your Mind Part 94: Marcus Aurelius on forgiveness being more practical than resentment",
    "Master Your Mind Part 95: Seneca on the discipline of writing your thoughts down daily",
    "Master Your Mind Part 96: Epictetus on real progress feeling uncomfortable before it feels natural",
    "Master Your Mind Part 97: Marcus Aurelius on how feared obstacles rarely arrive as badly as imagined",
    "Master Your Mind Part 98: Seneca on building a character that doesn't need to chase happiness",
    "Master Your Mind Part 99: Epictetus on aiming to be moved by the right things, not to feel nothing",
    "Master Your Mind Part 100: Marcus Aurelius's final lesson - living each day as if it might be enough, because it has to be",
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

Example of the exact FORMAT and VOICE only - it is about a completely different topic, so do not reuse \
any of its facts, story, or wording. Every line you write must be new content specifically about {topic}:
{example}

Rules:
- THE EXAMPLE ABOVE IS A TONE REFERENCE ONLY. It is not about {topic}. If your output shares its story, \
its facts, or close paraphrases of its wording, that is a failure - write entirely new content instead.
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

EXAMPLES = [
    """Marcus Aurelius started every morning the same way: he pictured the hardest parts of his day before they happened.|marcus aurelius statue bust
That's not pessimism, it's preparation - and it's why nothing could throw him off balance.|roman forum ruins
When you expect friction, you respond instead of react, and that alone makes you calmer all day.|ancient roman scroll manuscript
Try it tomorrow: picture one hard moment before it happens, and watch how much easier it feels.|sunrise ancient architecture""",
    """Seneca once told a friend that most people aren't poor, they just spend badly.|ancient roman coins
He wasn't talking about money - he meant time, the one thing you can never earn back.|hourglass ancient ruins
Once you start treating your hours like your money, you get pickier about who gets them.|sundial stone carving
Try it today: notice one hour you handed away for free, and decide if it was worth it.|roman villa garden""",
    """Epictetus spent years as a slave before he ever taught a single lesson.|epictetus bust statue
He said the one thing no one could ever take from him was his own judgment.|ancient greek philosopher scroll
That's the whole idea: control your reaction, and nothing external can actually touch you.|greek temple ruins
Try it today: pick one thing bothering you, and ask whether it's the event itself or just your reaction to it.|ancient agora ruins""",
]

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

SUBSCRIBE_CTAS = [
    "Follow for the next part of this series - one Stoic idea a day.",
    "There are 100 parts to this series - follow so you don't miss the next one.",
    "If this helped, follow along - a new part drops every day.",
]

SPEC = ChannelSpec(
    prompt_template=PROMPT_TEMPLATE,
    banned_phrases=BANNED_PHRASES,
    hook_openers=HOOK_OPENERS,
    examples=EXAMPLES,
    max_scenes=5,
    use_grounding=True,
    grounded_accuracy_rule=GROUNDED_ACCURACY_RULE,
    ungrounded_accuracy_rule=UNGROUNDED_ACCURACY_RULE,
    subscribe_ctas=SUBSCRIBE_CTAS,
    cta_keyword="ancient greek statue calm sunrise",
)


def generate_script(topic: str) -> list[dict]:
    from script_engine import generate_script as _generate
    return _generate(SPEC, topic)


def build_youtube_metadata(topic: str, credits: str) -> tuple[str, str, list[str]]:
    title = f"{topic[:80]} #Shorts"
    description = f"{topic} #Shorts #stoicism #philosophy\n\nGenerated by AETHER." + (f"\n\n{credits}" if credits else "")
    tags = ["stoicism", "philosophy", "marcus aurelius", "seneca", "epictetus", "selfimprovement", "shorts"]
    return title, description, tags
