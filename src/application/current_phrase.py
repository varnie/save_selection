"""Helpers for reading and writing the current phrase temp file."""

import os

from constants import TEMP_PHRASE_FILE


def write_current_phrase(phrase: str) -> None:
    """Write the current phrase to the temp file."""
    with open(TEMP_PHRASE_FILE, "w") as f:
        f.write(phrase)


def read_current_phrase() -> str | None:
    """Read the current phrase from the temp file, or None if empty/missing."""
    if not os.path.exists(TEMP_PHRASE_FILE):
        return None
    with open(TEMP_PHRASE_FILE) as f:
        content = f.read().strip()
    return content or None


def clear_current_phrase() -> None:
    """Remove the current phrase temp file."""
    if os.path.exists(TEMP_PHRASE_FILE):
        os.remove(TEMP_PHRASE_FILE)
