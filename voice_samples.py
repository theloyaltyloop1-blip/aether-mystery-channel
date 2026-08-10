import asyncio
import os
import edge_tts

SAMPLE_TEXT = (
    "In 1947, a commercial airliner vanished over the Andes without a trace. "
    "For over fifty years, no one knew what happened to it, or the seventeen people on board."
)

VOICES = {
    "christopher": "en-US-ChristopherNeural",  # authoritative US
    "thomas": "en-GB-ThomasNeural",             # serious British
    "ryan": "en-GB-RyanNeural",                 # British, general
    "eric": "en-US-EricNeural",                 # rational US
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "voice_samples")


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, voice in VOICES.items():
        dest = os.path.join(OUT_DIR, f"{name}.mp3")
        await edge_tts.Communicate(SAMPLE_TEXT, voice).save(dest)
        print(dest)


if __name__ == "__main__":
    asyncio.run(main())
