#!/usr/bin/env python3
"""Main vocab GUI application with system tray."""

import logging
import os
import sys
import threading
import time

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

from application import create_vocab_service
from config import DEFAULT_SETTINGS
from constants import CONFIG_FILE, IS_LINUX, IS_MACOS, TEMP_PHRASE_FILE
from infrastructure.notifications import send_notification
from windows.add_word import AddWordDialog
from windows.settings import SettingsWindow
from windows.stats import StatsWindow
from windows.word_browser import WordBrowserWindow

logger = logging.getLogger(__name__)


def _create_tray():
    if IS_MACOS:
        from infrastructure.tray.tray_macos import MacOSTray

        return MacOSTray()
    from infrastructure.tray.tray_linux import LinuxTray

    return LinuxTray()


class VocabApp(Gtk.Application):
    """Main application with system tray using Gtk.Application."""

    def __init__(self):
        super().__init__(
            application_id="com.vocab_app",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.connect("activate", self._on_activate)

        self.config_file = CONFIG_FILE
        self.vocab_service = None
        self.current_word = None
        self.paused_until = 0.0
        self.running = True
        self._state_lock = threading.Lock()
        self.settings_changed = threading.Event()
        self.tray = None

        self._windows = {}

    def do_startup(self):
        Gtk.Application.do_startup(self)

        # Keep app running even without windows (tray app)
        Gio.Application.hold(self)

        try:
            self.vocab_service = create_vocab_service(self.config_file)
        except Exception as e:
            logger.exception("Error creating vocab_service: %s", e)
            import traceback

            traceback.print_exc()
            sys.exit(1)
        if not self.vocab_service:
            error_dialog = Gtk.MessageDialog(
                None,
                Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                "Failed to initialize database. Check your settings.",
            )
            error_dialog.run()
            sys.exit(1)

        self._init_default_settings()

        self.tray = _create_tray()
        self.tray.setup(self._menu_callbacks())

        self.review_thread = threading.Thread(target=self.review_loop, daemon=True)
        self.review_thread.start()

        if IS_LINUX:
            from infrastructure.tray import get_desktop_environment

            if get_desktop_environment() in (
                "gnome",
                "ubuntu",
            ) and not self.vocab_service.get_setting("gnome_tray_warning_shown"):
                self.notify(
                    "GNOME detected. If tray icon is missing, "
                    "install 'Top Icons' or 'Tray Icons' extension.",
                    "Vocab",
                )
                self.vocab_service.set_setting("gnome_tray_warning_shown", "true")

        threading.Timer(2.0, self.check_wotd).start()

    def do_activate(self):
        Gtk.Application.do_activate(self)

    def _on_activate(self, app):
        pass

    def hold(self):
        """Keep the application running."""
        Gio.Application.hold(self)

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

    def _open_window(self, key, create_fn):
        if self._windows.get(key):
            self._windows[key].present()
        else:
            win = create_fn()
            win.set_application(self)
            win.show_all()
            self._windows[key] = win

    def _on_window_closed(self, key, window=None):
        self._windows[key] = None

    @staticmethod
    def notify(body: str, title: str = "Vocab") -> None:
        """Send notification with icon."""
        send_notification(body, title)

    def _init_default_settings(self) -> None:
        """Initialize default settings if not set."""
        defaults = DEFAULT_SETTINGS.copy()
        defaults["autostart"] = "false"
        for key, value in defaults.items():
            if self.vocab_service.get_setting(key) is None:
                self.vocab_service.set_setting(key, value)

    def review_loop(self) -> None:
        """Background review loop."""
        consecutive_errors = 0
        max_errors = 3
        while True:
            with self._state_lock:
                if not self.running:
                    break
                current_paused = self.paused_until

            try:
                settings = self.vocab_service.get_settings()
                interval = int(settings.get("review_interval", 3600))

                now = time.time()
                if now < current_paused:
                    wait_time = int(current_paused - now)
                    self.settings_changed.wait(min(wait_time, 60))
                    continue

                word = self.vocab_service.get_next_word()
                if word:
                    with self._state_lock:
                        self.current_word = word
                    self.show_word_popup(word)
                    for _ in range(interval // 60):
                        with self._state_lock:
                            if not self.running:
                                break
                        self.settings_changed.wait(60)
                        self.settings_changed.clear()
                else:
                    self.settings_changed.wait(300)
                    self.settings_changed.clear()

                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                logger.exception("Review loop error (%d/%d): %s", consecutive_errors, max_errors, e)
                if consecutive_errors >= max_errors:
                    logger.critical("Too many review loop errors, stopping")
                    break
                self.settings_changed.wait(60)

        self.vocab_service.remove_session()

    def show_word_popup(self, word) -> None:
        """Show word popup notification."""
        if not word:
            return

        translation, trans_lang = self.vocab_service.get_translation_with_lang(word.id)

        abbrev = self.vocab_service.get_language_abbreviation(trans_lang) if trans_lang else "—"

        body = f"<b>{word.phrase}</b>"
        if translation:
            body += f"\n→ {translation} [{abbrev}]"

        self._set_current_phrase(word.phrase)
        self.vocab_service.review_word(word.id)
        self.notify(body)

    def check_wotd(self) -> None:
        """Check and show Word of the Day if enabled."""
        try:
            word = self.vocab_service.get_word_of_the_day()
            if word:
                self._set_current_phrase(word.phrase)
                body = f"<b>{word.phrase}</b>\n→ {word.translation}"
                self.notify(body, "Word of the Day")
        except Exception as e:
            logger.exception("WOTD error: %s", e)
        finally:
            self.vocab_service.remove_session()

    @staticmethod
    def _set_current_phrase(phrase: str) -> None:
        """Set current phrase for discard hotkey."""
        with open(TEMP_PHRASE_FILE, "w") as f:
            f.write(phrase)

    def get_current_phrase(self) -> str | None:
        """Get current word from temp file or memory."""
        if os.path.exists(TEMP_PHRASE_FILE):
            with open(TEMP_PHRASE_FILE) as f:
                return f.read().strip()
        with self._state_lock:
            return self.current_word.phrase if self.current_word else None

    def on_show_next(self, widget=None) -> None:
        """Show next word immediately (falls back to soonest upcoming if none due)."""
        word = self.vocab_service.get_next_word()
        if word:
            with self._state_lock:
                self.current_word = word
            self.show_word_popup(word)
            self.tray.set_label(str(word.phrase)[:20])

    def on_show_stats(self, widget=None) -> None:
        """Show stats window."""

        def create_window():
            win = StatsWindow(self.vocab_service)
            win.connect("destroy", lambda w: self._on_window_closed("stats", w))
            return win

        self._open_window("stats", create_window)

    def on_add_word(self, widget=None) -> None:
        """Show add word dialog."""

        def on_add(word):
            self.tray.set_label(word[:20])

        def create_window():
            win = AddWordDialog(self.vocab_service, on_add)
            win.connect("destroy", lambda w: self._on_window_closed("add", w))
            return win

        self._open_window("add", create_window)

    def on_pause(self, widget=None) -> None:
        """Toggle pause/resume reviews."""
        with self._state_lock:
            if self.paused_until > time.time():
                self.paused_until = 0.0
                self.tray.set_pause_label("Pause (1 hour)")
            else:
                self.paused_until = time.time() + 3600
                self.tray.set_pause_label("Resume")
        self.settings_changed.set()

    def on_settings(self, widget=None) -> None:
        """Show settings window."""

        def create_window():
            win = SettingsWindow(self.vocab_service, config_file=self.config_file)
            win.connect("destroy", lambda w: self._on_window_closed("settings", w))
            return win

        self._open_window("settings", create_window)

    def on_word_browser(self, widget=None) -> None:
        """Show word browser window."""

        def create_window():
            win = WordBrowserWindow(self.vocab_service)
            win.connect("destroy", lambda w: self._on_window_closed("browser", w))
            return win

        self._open_window("browser", create_window)

    def on_quit(self, widget=None) -> None:
        """Quit application."""
        with self._state_lock:
            self.running = False
        self.settings_changed.set()
        self.vocab_service.close()
        self.quit()


def main():
    """Main entry point - GUI only."""
    app = VocabApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
