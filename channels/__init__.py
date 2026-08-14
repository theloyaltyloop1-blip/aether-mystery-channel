"""AETHER channel registry - one module per niche/YouTube account."""
from . import mystery, philosophy, space

CHANNELS = {
    "mystery": mystery,
    "philosophy": philosophy,
    "space": space,
}


def get_channel(name: str):
    if name not in CHANNELS:
        raise ValueError(f"Unknown channel '{name}'. Known channels: {', '.join(CHANNELS)}")
    return CHANNELS[name]
