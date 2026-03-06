#!/usr/bin/env python3
"""Shared helpers for CLI and GUI."""

import os
import subprocess
from typing import Optional

from config import read_config
from constants import DEFAULT_DB_PATH, CONFIG_FILE, IS_MACOS
from vocab import VocabService

# Module-level icon path
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "translate.svg")


def notify_cli(body, title="Vocab"):
    """Send notification - uses terminal-notifier on macOS, notify-send on Linux."""
    if IS_MACOS:
        import re
        import shutil
        clean_body = re.sub(r'<[^>]+>', '', body)
        if shutil.which("terminal-notifier"):
            subprocess.run(
                ["terminal-notifier", "-title", title, "-message", clean_body],
                check=False,
            )
        else:
            # Fallback to osascript (may be silently blocked)
            script = f'display notification "{clean_body}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=False)
    else:
        args = ["notify-send", "-u", "low", title, body]
        if os.path.exists(ICON_PATH):
            args[1:1] = ["-i", ICON_PATH]
        subprocess.run(args, check=False)


def get_clipboard_text() -> str:
    """Get text from clipboard/selection."""
    if IS_MACOS:
        # macOS: use pbpaste
        try:
            result = subprocess.run(
                ["pbpaste"], capture_output=True, text=True, check=False
            )
            return result.stdout.strip()
        except Exception:
            return ""

    # Linux: Primary selection first (X11)
    try:
        result = os.popen("xclip -o -selection primary 2>/dev/null").read().strip()
        if result:
            return result
    except Exception:
        pass

    # Wayland primary selection
    if os.environ.get("WAYLAND_DISPLAY"):
        try:
            result = os.popen("wl-paste -p 2>/dev/null").read().strip()
            if result:
                return result
        except Exception:
            pass

    return ""


def get_db_path(config_file: str = CONFIG_FILE) -> str:
    """Determine DB path from config file or default."""
    config = read_config(config_file)
    custom_data_dir = config.get("data_dir")

    if custom_data_dir:
        custom_db_path = os.path.join(os.path.expanduser(custom_data_dir), "vocab.db")
        # If custom path is specified, use it (create directory if needed)
        os.makedirs(os.path.dirname(custom_db_path), exist_ok=True)
        return custom_db_path

    return DEFAULT_DB_PATH


def init_vocab_service(config_file: str = CONFIG_FILE, must_exist: bool = False) -> Optional[VocabService]:
    """Initialize VocabService with DB from config.

    Args:
        config_file: Path to config file
        must_exist: If True, exit with error if DB doesn't exist

    Returns:
        VocabService instance or None if DB doesn't exist
    """
    db_path = get_db_path(config_file)

    if not os.path.exists(db_path):
        if must_exist:
            print(f"Error: Database not found at {db_path}")
            print("Please run the GUI app first to initialize the database.")
            return None

        # Create DB if it doesn't exist
        data_dir = os.path.dirname(db_path)
        os.makedirs(data_dir, exist_ok=True)

    return VocabService(db_path)
