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
