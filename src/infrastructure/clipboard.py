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
        result = subprocess.run([pbpaste], capture_output=True, text=True, check=False)  # noqa: S603
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
            result = subprocess.run(  # noqa: S603
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
                result = subprocess.run(  # noqa: S603
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


def clear_primary_selection() -> None:
    """Clear the PRIMARY selection to avoid stale text on next --save.

    On X11 the PRIMARY buffer persists even after text is deselected,
    which can cause a subsequent --save to re-save a deleted phrase.
    """
    if IS_MACOS:
        return

    xclip_path = shutil.which("xclip")
    if xclip_path:
        try:
            subprocess.run(  # noqa: S603
                [str(xclip_path), "-i", "/dev/null", "-selection", "primary"],
                capture_output=True,
                check=False,
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            pass
        except OSError:
            pass

    if os.environ.get("WAYLAND_DISPLAY"):
        wl_copy_path = shutil.which("wl-copy")
        if wl_copy_path:
            try:
                subprocess.run(  # noqa: S603
                    [str(wl_copy_path), "-p", ""],
                    capture_output=True,
                    check=False,
                    timeout=2,
                )
            except subprocess.TimeoutExpired:
                pass
            except OSError:
                pass
