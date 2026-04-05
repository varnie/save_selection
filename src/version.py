#!/usr/bin/env python3
"""Version info - read from VERSION file."""

import os

VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(str(__file__))), "VERSION")


def get_version():
    """Read version from VERSION file."""
    try:
        with open(VERSION_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


__version__ = get_version()
