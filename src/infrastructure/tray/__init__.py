#!/usr/bin/env python3
"""Infrastructure tray implementations."""

import sys

if sys.platform == "darwin":
    from infrastructure.tray.tray_macos import MacOSTray

    __all__ = ["MacOSTray"]
else:
    from infrastructure.tray.tray_linux import LinuxTray, get_desktop_environment

    __all__ = ["LinuxTray", "get_desktop_environment"]
