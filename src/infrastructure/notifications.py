#!/usr/bin/env python3
"""Infrastructure - Platform-specific notification service."""

import os
import subprocess
import shutil
import re
from constants import IS_MACOS


ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "translate.svg")


def send_notification(body: str, title: str = "Vocab") -> bool:
    """Send system notification.
    
    Args:
        body: Notification body text
        title: Notification title
        
    Returns:
        True if notification was sent successfully
    """
    if IS_MACOS:
        return _send_macos_notification(body, title)
    else:
        return _send_linux_notification(body, title)


def _send_macos_notification(body: str, title: str) -> bool:
    """Send notification on macOS."""
    clean_body = re.sub(r'<[^>]+>', '', body)
    
    if shutil.which("terminal-notifier"):
        result = subprocess.run(
            ["terminal-notifier", "-title", title, "-message", clean_body],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    
    # Fallback to osascript
    script = f'display notification "{clean_body}" with title "{title}"'
    result = subprocess.run(["osascript", "-e", script], check=False)
    return result.returncode == 0


def _send_linux_notification(body: str, title: str) -> bool:
    """Send notification on Linux."""
    args = ["notify-send", "-u", "low", title, body]
    
    if os.path.exists(ICON_PATH):
        args[1:1] = ["-i", ICON_PATH]
    
    result = subprocess.run(args, check=False)
    return result.returncode == 0
