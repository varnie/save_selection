#!/usr/bin/env python3
"""Main vocab GUI application with system tray."""

import os
import sys
import threading
import time

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from constants import CONFIG_FILE, TEMP_PHRASE_FILE, IS_MACOS, IS_LINUX
from application import create_vocab_service
from infrastructure.notifications import send_notification
from windows.stats import StatsWindow
from windows.settings import SettingsWindow
from windows.add_word import AddWordDialog
from windows.word_browser import WordBrowserWindow


def _create_tray():
    if IS_MACOS:
        from tray_macos import MacOSTray
        return MacOSTray()
    from tray_linux import LinuxTray
    return LinuxTray()


class VocabTrayApp:
    """Main application with system tray."""

    def __init__(self):
        # Config file path
        self.config_file = CONFIG_FILE

        # Initialize services
        self.vocab_service = create_vocab_service(self.config_file)
        if not self.vocab_service:
            error_dialog = Gtk.MessageDialog(
                None,
                Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                "Failed to initialize database. Check your settings."
            )
            error_dialog.run()
            sys.exit(1)

        # Set default settings if not set
        self._init_default_settings()

        # State
        self.current_word = None
        self.paused_until = 0
        self.running = True
        self.settings_changed = threading.Event()

        # Create system tray
        self.tray = _create_tray()
        self.tray.setup(self._menu_callbacks())

        # Start review loop
        self.review_thread = threading.Thread(target=self.review_loop, daemon=True)
        self.review_thread.start()

        # GNOME tray warning (one-time, Linux only)
        if IS_LINUX:
            from tray_linux import get_desktop_environment
            if get_desktop_environment() in ("gnome", "ubuntu"):
                if not self.vocab_service.get_setting("gnome_tray_warning_shown"):
                    self.notify("GNOME detected. If tray icon is missing, install 'Top Icons' or 'Tray Icons' extension.", "Vocab")
                    self.vocab_service.set_setting("gnome_tray_warning_shown", "true")

        # Word of the Day (delayed to not block startup)
        threading.Timer(2.0, self.check_wotd).start()

    def _menu_callbacks(self):
        return {
            "show_next": self.on_show_next,
            "pause": self.on_pause,
            "add_word": self.on_add_word,
            "word_browser": self.on_word_browser,
            "stats": self.on_show_stats,
            "settings": self.on_settings,
            "quit": self.on_quit,
        }

    def notify(self, body: str, title: str = "Vocab") -> None:
        """Send notification with icon."""
        send_notification(body, title)

    def _init_default_settings(self) -> None:
        """Initialize default settings if not set."""
        defaults = {
            "review_interval": "3600",
            "source_lang": "en",
            "target_lang": "ru",
            "translation_provider": "google",
            "autostart": "false",
        }
        for key, value in defaults.items():
            if self.vocab_service.get_setting(key) is None:
                self.vocab_service.set_setting(key, value)

    def review_loop(self) -> None:
        """Background review loop."""
        while self.running:
            try:
                # Reload settings each iteration to pick up changes
                settings = self.vocab_service.get_settings()
                interval = int(settings.get("review_interval", 3600))

                # Check if paused
                if time.time() < self.paused_until:
                    self.settings_changed.wait(60)
                    continue

                # Get next word
                word = self.vocab_service.get_next_word()
                if word:
                    self.current_word = word
                    self.show_word_popup(word)
                    # Wait for interval, but check every minute for settings changes
                    for _ in range(interval // 60):
                        if not self.running:
                            break
                        self.settings_changed.wait(60)
                        self.settings_changed.clear()
                else:
                    # No words due, check again in 5 minutes
                    self.settings_changed.wait(300)
                    self.settings_changed.clear()

            except Exception as e:
                print(f"Review loop error: {e}")
                self.settings_changed.wait(60)

    def show_word_popup(self, word) -> None:
        """Show word popup notification."""
        if not word:
            return
        
        translation, trans_lang = self.vocab_service.get_translation_with_lang(word.id)
        
        interval = word.interval_days
        if interval == 1:
            interval_str = "1 day"
        elif interval < 30:
            interval_str = f"{interval} days"
        elif interval < 365:
            interval_str = f"{interval // 30} mo"
        else:
            interval_str = f"{interval // 365} yr"
        
        abbrev = self.vocab_service.get_language_abbreviation(trans_lang) if trans_lang else "—"
        
        body = f"<b>{word.phrase}</b> [{interval_str}]"
        if translation:
            body += f"\n→ {translation} [{abbrev}]"
        
        from constants import TEMP_PHRASE_FILE
        with open(TEMP_PHRASE_FILE, "w") as f:
            f.write(word.phrase)
        
        self.vocab_service.skip_word(word.id)
        self.notify(body)

    def check_wotd(self) -> None:
        """Check and show Word of the Day if enabled."""
        try:
            word = self.vocab_service.get_word_of_the_day()
            if word:
                body = f"<b>{word.phrase}</b>\n→ {word.translation}"
                self.notify(body, "Word of the Day")
        except Exception as e:
            print(f"WOTD error: {e}")
        finally:
            self.vocab_service.remove_session()

    def get_current_phrase(self) -> str | None:
        """Get current word from temp file or memory."""
        temp_file = TEMP_PHRASE_FILE
        if os.path.exists(temp_file):
            with open(temp_file) as f:
                return f.read().strip()
        return self.current_word.phrase if self.current_word else None

    # Menu handlers
    def on_show_next(self, widget: Gtk.Widget) -> None:
        """Show next word immediately."""
        word = self.vocab_service.get_next_word()
        if word:
            self.current_word = word
            self.show_word_popup(word)
            self.tray.set_label(str(word.phrase)[:20])

    def on_show_stats(self, widget: Gtk.Widget) -> None:
        """Show stats window."""
        win = StatsWindow(self.vocab_service)
        win.show_all()

    def on_add_word(self, widget: Gtk.Widget) -> None:
        """Show add word dialog."""
        def on_add(word):
            self.tray.set_label(word[:20])

        win = AddWordDialog(self.vocab_service, on_add)
        win.show_all()

    def on_pause(self, widget: Gtk.Widget) -> None:
        """Pause reviews for 1 hour."""
        self.paused_until = time.time() + 3600
        self.tray.set_pause_label("Resume")

    def on_resume(self, widget: Gtk.Widget) -> None:
        """Resume reviews."""
        self.paused_until = None
        self.tray.set_pause_label("Pause (1 hour)")

    def on_settings(self, widget: Gtk.Widget) -> None:
        """Show settings window."""
        win = SettingsWindow(self.vocab_service, config_file=CONFIG_FILE)
        win.show_all()

    def on_word_browser(self, widget: Gtk.Widget) -> None:
        """Show word browser window."""
        win = WordBrowserWindow(self.vocab_service)
        win.show_all()

    def on_quit(self, widget: Gtk.Widget) -> None:
        """Quit application."""
        self.running = False
        self.vocab_service.close()
        Gtk.main_quit()


def main():
    """Main entry point - GUI only."""
    app = VocabTrayApp()
    Gtk.main()


if __name__ == "__main__":
    main()
