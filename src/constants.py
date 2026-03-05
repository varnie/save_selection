#!/usr/bin/env python3
"""Application constants."""

import os
import sys
import tempfile

# App info
APP_NAME = "vocab_app"

# Platform detection
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# Default data directory
if IS_MACOS:
    DEFAULT_DATA_DIR = os.path.expanduser("~/Library/Application Support/vocab_app")
    CONFIG_DIR = os.path.expanduser("~/Library/Application Support/vocab_app")
    AUTOSTART_DIR = os.path.expanduser("~/Library/LaunchAgents")
    AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "com.vocab_app.plist")
else:
    DEFAULT_DATA_DIR = os.path.expanduser("~/.local/share/vocab_app")
    CONFIG_DIR = os.path.expanduser("~/.config/vocab_app")
    AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
    AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, f"{APP_NAME}.desktop")

# Config file
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings")

# Database
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "vocab.db")
DB_FILENAME = "vocab.db"

# Temp files
TEMP_PHRASE_FILE = os.path.join(tempfile.gettempdir(), "last_vocab_phrase")

# Icon directory
ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# Tray menu items: (label, callback_key) or None for separator
MENU_ITEMS = [
    ("Show next word", "show_next"),
    ("Pause (1 hour)", "pause"),
    None,
    ("Add word", "add_word"),
    ("Word Browser", "word_browser"),
    ("Quiz", "quiz"),
    ("Stats", "stats"),
    ("Settings", "settings"),
    None,
    ("Quit", "quit"),
]
