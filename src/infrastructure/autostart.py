#!/usr/bin/env python3
"""Autostart management service."""

import os

from constants import AUTOSTART_DIR, AUTOSTART_FILE


class AutostartManager:
    """Manages application autostart functionality."""

    @staticmethod
    def is_enabled() -> bool:
        """Check if autostart is enabled."""
        return os.path.exists(AUTOSTART_FILE)

    @staticmethod
    def enable() -> None:
        """Enable autostart by creating .desktop file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)

        venv_python = os.path.join(src_dir, "venv", "bin", "python3")
        exec_path = os.path.join(current_dir, "vocab_gui.py")

        if os.path.exists(venv_python):
            python_exec = venv_python
        else:
            python_exec = "python3"

        os.makedirs(AUTOSTART_DIR, exist_ok=True)

        desktop_content = f"""[Desktop Entry]
Type=Application
Name=Vocab App
Exec={python_exec} {exec_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        with open(AUTOSTART_FILE, "w") as f:
            f.write(desktop_content)

    @staticmethod
    def disable() -> None:
        """Disable autostart by removing .desktop file."""
        if os.path.exists(AUTOSTART_FILE):
            os.remove(AUTOSTART_FILE)
