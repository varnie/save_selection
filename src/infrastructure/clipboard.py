#!/usr/bin/env python3
"""Infrastructure - Platform-specific clipboard service."""

import os
import subprocess
from constants import IS_MACOS


def get_clipboard_text() -> str:
    """Get text from clipboard/selection.
    
    Returns:
        Clipboard text content, or empty string if unavailable
    """
    if IS_MACOS:
        return _get_macos_clipboard()
    else:
        return _get_linux_clipboard()


def _get_macos_clipboard() -> str:
    """Get clipboard text on macOS using pbpaste."""
    try:
        result = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, check=False
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_linux_clipboard() -> str:
    """Get clipboard text on Linux (supports X11 and Wayland)."""
    # Try X11 primary selection first
    try:
        result = os.popen("xclip -o -selection primary 2>/dev/null").read().strip()
        if result:
            return result
    except Exception:
        pass

    # Try Wayland primary selection
    if os.environ.get("WAYLAND_DISPLAY"):
        try:
            result = os.popen("wl-paste -p 2>/dev/null").read().strip()
            if result:
                return result
        except Exception:
            pass

    return ""
