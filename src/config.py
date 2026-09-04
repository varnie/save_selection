#!/usr/bin/env python3
"""Config helpers."""

import json
import os


def read_config(config_file: str) -> dict:
    """Read JSON config file, return empty dict on error."""
    if not os.path.exists(config_file):
        return {}
    try:
        with open(config_file) as f:
            return json.load(f)
    except Exception:
        return {}


def write_config(config_file: str, config: dict) -> bool:
    """Write JSON config file, return True on success."""
    try:
        config_dir = os.path.dirname(config_file)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(config, f)
        return True
    except Exception:
        return False


# Setting keys (single source of truth — use instead of string literals).
REVIEW_INTERVAL_KEY = "review_interval"
SOURCE_LANG_KEY = "source_lang"
TARGET_LANG_KEY = "target_lang"
TRANSLATION_PROVIDER_KEY = "translation_provider"
WOTD_ENABLED_KEY = "wotd_enabled"
WOTD_LEVEL_KEY = "wotd_level"
DATA_DIR_KEY = "data_dir"
GNOME_TRAY_WARNING_KEY = "gnome_tray_warning_shown"

# Default setting values.
DEFAULT_REVIEW_INTERVAL = "3600"
DEFAULT_SOURCE_LANG = "en"
DEFAULT_TARGET_LANG = "ru"
DEFAULT_TRANSLATION_PROVIDER = "mymemory"
DEFAULT_WOTD_ENABLED = "false"
DEFAULT_WOTD_LEVEL = "B2"


DEFAULT_SETTINGS = {
    REVIEW_INTERVAL_KEY: DEFAULT_REVIEW_INTERVAL,
    SOURCE_LANG_KEY: DEFAULT_SOURCE_LANG,
    TARGET_LANG_KEY: DEFAULT_TARGET_LANG,
    TRANSLATION_PROVIDER_KEY: DEFAULT_TRANSLATION_PROVIDER,
    GNOME_TRAY_WARNING_KEY: "false",
}
