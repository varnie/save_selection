"""Autostart management service."""

import os
import plistlib

from constants import AUTOSTART_DIR, AUTOSTART_FILE, IS_MACOS


def _script_path() -> str:
    """Path to the vocab_gui.py script."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vocab_gui.py"
    )


def _python_path() -> str:
    """Path to the bundled venv python, falling back to system python3."""
    venv_python = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "venv",
        "bin",
        "python3",
    )
    return venv_python if os.path.exists(venv_python) else "python3"


class AutostartManager:
    """Manages application autostart functionality."""

    @staticmethod
    def is_enabled() -> bool:
        """Check if autostart is enabled."""
        return os.path.exists(AUTOSTART_FILE)

    @staticmethod
    def enable() -> None:
        """Enable autostart by creating a platform launch file."""
        os.makedirs(AUTOSTART_DIR, exist_ok=True)

        if IS_MACOS:
            AutostartManager._write_plist()
        else:
            AutostartManager._write_desktop_entry()

    @staticmethod
    def disable() -> None:
        """Disable autostart by removing the launch file."""
        if os.path.exists(AUTOSTART_FILE):
            os.remove(AUTOSTART_FILE)

    @staticmethod
    def _write_plist() -> None:
        """Write a macOS LaunchAgent plist."""
        plist = {
            "Label": "com.vocab_app",
            "ProgramArguments": [_python_path(), _script_path()],
            "RunAtLoad": True,
            "KeepAlive": False,
        }
        with open(AUTOSTART_FILE, "wb") as f:
            plistlib.dump(plist, f)

    @staticmethod
    def _write_desktop_entry() -> None:
        """Write a Linux .desktop autostart file."""
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=Vocab App
Exec={_python_path()} {_script_path()}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        with open(AUTOSTART_FILE, "w") as f:
            f.write(desktop_content)
