"""AETHER channel registry - one module per niche/YouTube account."""
from . import mystery, philosophy, kids

CHANNELS = {
    "mystery": mystery,
    "philosophy": philosophy,
    "kids": kids,
}


def get_channel(name: str):
    if name not in CHANNELS:
        raise ValueError(f"Unknown channel '{name}'. Known channels: {', '.join(CHANNELS)}")
    return CHANNELS[name]
