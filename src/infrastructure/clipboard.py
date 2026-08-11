"""Infrastructure - Platform-specific clipboard service."""

import logging
import os
import shutil
import subprocess

from constants import IS_MACOS

logger = logging.getLogger(__name__)


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
    pbpaste_path = shutil.which("pbpaste")
    if not pbpaste_path:
        return ""
    pbpaste = str(pbpaste_path)
    try:
        result = subprocess.run([pbpaste], capture_output=True, text=True, check=False)  # ruff:ignore[subprocess-without-shell-equals-true]
        return result.stdout.strip()
    except OSError as e:
        logger.warning("Failed to run pbpaste: %s", e)
        return ""


def _get_linux_clipboard() -> str:
    """Get clipboard text on Linux (supports X11 and Wayland)."""
    # Try X11 primary selection first
    xclip_path = shutil.which("xclip")
    if xclip_path:
        xclip = str(xclip_path)
        try:
            result = subprocess.run(  # ruff:ignore[subprocess-without-shell-equals-true]
                [xclip, "-o", "-selection", "primary"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.stdout:
                return result.stdout.strip()
        except OSError as e:
            logger.warning("Failed to run xclip: %s", e)

    # Try Wayland primary selection
    if os.environ.get("WAYLAND_DISPLAY"):
        wl_paste_path = shutil.which("wl-paste")
        if wl_paste_path:
            wl_paste = str(wl_paste_path)
            try:
                result = subprocess.run(  # ruff:ignore[subprocess-without-shell-equals-true]
                    [wl_paste, "-p"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.stdout:
                    return result.stdout.strip()
            except OSError as e:
                logger.warning("Failed to run wl-paste: %s", e)

    return ""
