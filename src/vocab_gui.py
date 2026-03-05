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
from helpers import notify_cli, init_vocab_service
from windows.stats import StatsWindow
from windows.settings import SettingsWindow
from windows.add_word import AddWordDialog
from windows.word_browser import WordBrowserWindow
from windows.quiz import QuizSetupWindow


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
        self.vocab_service = init_vocab_service(self.config_file)
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
            "quiz": self.on_quiz,
            "stats": self.on_show_stats,
            "settings": self.on_settings,
            "quit": self.on_quit,
        }

    def notify(self, body, title="Vocab"):
        """Send notification with icon."""
        notify_cli(body, title)

    def _init_default_settings(self):
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

    def review_loop(self):
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

    def show_word_popup(self, word):
        """Show word popup notification."""
        body = self.vocab_service.get_next_word_notification()
        if body:
            self.notify(body)

    def check_wotd(self):
        """Check and show Word of the Day if enabled."""
        try:
            wotd = self.vocab_service.get_word_of_the_day()
            if wotd:
                result, success = self.vocab_service.save_wotd_to_vocab(wotd['word'], wotd['translation'])
                if success:
                    body = f"<b>{wotd['word']}</b> [{wotd['level']}]\n→ {wotd['translation']}\n\nSaved to your words!"
                else:
                    body = f"<b>{wotd['word']}</b> [{wotd['level']}]\n→ {wotd['translation']}"
                self.notify(body, "Word of the Day")
        except Exception as e:
            print(f"WOTD error: {e}")
        finally:
            self.vocab_service.remove_session()

    def get_current_phrase(self):
        """Get current word from temp file or memory."""
        temp_file = TEMP_PHRASE_FILE
        if os.path.exists(temp_file):
            with open(temp_file) as f:
                return f.read().strip()
        return self.current_word.get("phrase") if self.current_word else None

    # Menu handlers
    def on_show_next(self, widget):
        """Show next word immediately."""
        word = self.vocab_service.get_next_word()
        if word:
            self.current_word = word
            self.show_word_popup(word)
            self.tray.set_label(str(word.get("phrase", ""))[:20])

    def on_show_stats(self, widget):
        """Show stats window."""
        win = StatsWindow(self.vocab_service)
        win.show_all()

    def on_add_word(self, widget):
        """Show add word dialog."""
        def on_add(word):
            self.tray.set_label(word[:20])

        win = AddWordDialog(self.vocab_service, on_add)
        win.show_all()

    def on_pause(self, widget):
        """Pause reviews for 1 hour."""
        self.paused_until = time.time() + 3600
        self.tray.set_pause_label("Resume")
        self.tray.set_pause_callback(self.on_resume)

    def on_resume(self, widget):
        """Resume reviews."""
        self.paused_until = 0
        self.tray.set_pause_label("Pause (1 hour)")
        self.tray.set_pause_callback(self.on_pause)

    def on_settings(self, widget):
        """Show settings window."""
        win = SettingsWindow(self.vocab_service, config_file=self.config_file)
        win.show_all()

    def on_quiz(self, widget):
        """Show quiz setup window."""
        win = QuizSetupWindow(self.vocab_service)
        win.show_all()

    def on_word_browser(self, widget):
        """Show word browser window."""
        win = WordBrowserWindow(self.vocab_service)
        win.show_all()

    def on_quit(self, widget):
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
