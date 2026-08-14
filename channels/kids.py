"""
AETHER channel: Kids - classic public-domain nursery rhymes and simple
counting/alphabet content for toddlers (1-5). Deliberately NOT LLM-generated
content: these are the actual traditional rhymes (public domain, centuries
old), word for word - safer and more correct than letting a small model
invent "nursery rhyme style" text. No hook/banned-phrase engine needed since
there's no AI writing to filter.
"""
import os

from topic_picker import make_topic_picker

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

NAME = "kids"
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret_kids.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token_kids.json")
USED_TOPICS_FILE = os.path.join(BASE_DIR, "assets", "used_topics_kids.json")
MADE_FOR_KIDS = True  # COPPA: this content is genuinely made for children
CATEGORY_ID = "27"  # Education
VOICE = "en-US-AnaNeural"  # free edge-tts voice, described as "Cute" - fits kids content

# bright, high-contrast, friendly style instead of the mystery channel's
# dark moody caption cards
STYLE = {
    "box_color": (255, 214, 51),   # warm yellow
    "box_alpha": 235,
    "text_color": (30, 20, 60),     # dark plum, reads clearly on yellow
}

# topic name -> list of (narration line, footage search keyword)
RHYMES: dict[str, list[tuple[str, str]]] = {
    "Twinkle Twinkle Little Star": [
        ("Twinkle, twinkle, little star, how I wonder what you are.", "twinkle star night sky cartoon"),
        ("Up above the world so high, like a diamond in the sky.", "diamond sparkle sky illustration"),
        ("When the blazing sun is gone, when he nothing shines upon.", "sunset cartoon illustration"),
        ("Then you show your little light, twinkle twinkle all the night.", "stars night sky cartoon"),
    ],
    "Itsy Bitsy Spider": [
        ("The itsy bitsy spider climbed up the water spout.", "cartoon spider illustration"),
        ("Down came the rain and washed the spider out.", "rain cartoon illustration"),
        ("Out came the sun and dried up all the rain.", "sun cartoon illustration"),
        ("And the itsy bitsy spider climbed up the spout again.", "cartoon spider climbing"),
    ],
    "Row Row Row Your Boat": [
        ("Row, row, row your boat, gently down the stream.", "cartoon boat river illustration"),
        ("Merrily, merrily, merrily, merrily, life is but a dream.", "river cartoon illustration"),
    ],
    "Baa Baa Black Sheep": [
        ("Baa, baa, black sheep, have you any wool?", "cartoon black sheep illustration"),
        ("Yes sir, yes sir, three bags full.", "wool bags cartoon illustration"),
        ("One for my master, one for my dame.", "cartoon farm illustration"),
        ("One for the little boy who lives down the lane.", "cartoon boy illustration"),
    ],
    "Hickory Dickory Dock": [
        ("Hickory dickory dock, the mouse ran up the clock.", "cartoon mouse clock illustration"),
        ("The clock struck one, the mouse ran down.", "cartoon clock illustration"),
        ("Hickory dickory dock.", "cartoon clock mouse illustration"),
    ],
    "Mary Had a Little Lamb": [
        ("Mary had a little lamb, its fleece was white as snow.", "cartoon lamb illustration"),
        ("And everywhere that Mary went, the lamb was sure to go.", "cartoon girl lamb illustration"),
        ("It followed her to school one day, which was against the rule.", "cartoon school illustration"),
        ("It made the children laugh and play to see a lamb at school.", "cartoon children playing"),
    ],
    "Humpty Dumpty": [
        ("Humpty Dumpty sat on a wall, Humpty Dumpty had a great fall.", "cartoon egg wall illustration"),
        ("All the king's horses and all the king's men,", "cartoon horses illustration"),
        ("couldn't put Humpty together again.", "cartoon egg illustration"),
    ],
    "Jack and Jill": [
        ("Jack and Jill went up the hill, to fetch a pail of water.", "cartoon hill children illustration"),
        ("Jack fell down and broke his crown, and Jill came tumbling after.", "cartoon hill illustration"),
    ],
    "Rain Rain Go Away": [
        ("Rain, rain, go away, come again another day.", "cartoon rain illustration"),
        ("Little children want to play, rain, rain, go away.", "cartoon children playing sunshine"),
    ],
    "This Little Piggy": [
        ("This little piggy went to market, this little piggy stayed home.", "cartoon piglet illustration"),
        ("This little piggy had roast beef, this little piggy had none.", "cartoon pig illustration"),
        ("And this little piggy went wee wee wee, all the way home.", "cartoon piglet running"),
    ],
    "The Wheels on the Bus": [
        ("The wheels on the bus go round and round, round and round, round and round.", "cartoon bus illustration"),
        ("The wheels on the bus go round and round, all through the town.", "cartoon bus town illustration"),
        ("The wipers on the bus go swish swish swish.", "cartoon bus wipers illustration"),
        ("The horn on the bus goes beep beep beep.", "cartoon bus horn illustration"),
    ],
    "Five Little Ducks": [
        ("Five little ducks went out one day, over the hills and far away.", "cartoon ducks illustration"),
        ("Mother duck said quack quack quack quack, but only four little ducks came back.", "cartoon duck illustration"),
    ],
    "Let's Count to Ten": [
        ("Let's count to ten together! One, two, three.", "cartoon numbers illustration"),
        ("Four, five, six, keep going!", "cartoon numbers colorful"),
        ("Seven, eight, nine, almost there!", "cartoon numbers illustration"),
        ("And ten! Great counting!", "cartoon number ten illustration"),
    ],
    "The Alphabet Song": [
        ("A B C D E F G", "cartoon alphabet letters illustration"),
        ("H I J K L M N O P", "cartoon alphabet colorful"),
        ("Q R S T U V", "cartoon letters illustration"),
        ("W X Y and Z, now I know my A B Cs", "cartoon alphabet illustration"),
    ],
    "Old MacDonald Had a Farm": [
        ("Old MacDonald had a farm, E I E I O.", "cartoon farm illustration"),
        ("And on his farm he had a cow, E I E I O.", "cartoon cow illustration"),
        ("With a moo moo here and a moo moo there.", "cartoon cow farm illustration"),
        ("Old MacDonald had a farm, E I E I O.", "cartoon farm animals illustration"),
    ],
}

SEED_TOPICS = list(RHYMES.keys())
INVENT_PROMPT = ""  # unused - kids content never falls back to LLM invention, see pick_topic below

pick_topic, preview_topics = make_topic_picker(USED_TOPICS_FILE, SEED_TOPICS, INVENT_PROMPT)


def generate_script(topic: str) -> list[dict]:
    """No LLM call - returns the real, curated rhyme text directly."""
    lines = RHYMES.get(topic, [])
    return [{"narration": narration, "keyword": keyword} for narration, keyword in lines]


def build_youtube_metadata(topic: str, credits: str) -> tuple[str, str, list[str]]:
    title = f"{topic} - Nursery Rhymes for Kids #Shorts"
    description = (
        f"{topic} - a classic nursery rhyme for toddlers and preschoolers. #Shorts #nurseryrhymes #kidssongs"
        + (f"\n\n{credits}" if credits else "")
    )
    tags = ["nursery rhymes", "kids songs", "toddler", "preschool", "children", "shorts"]
    return title, description, tags
