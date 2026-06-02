"""Settings window."""

import os
import plistlib

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from config import DEFAULT_SETTINGS, read_config, write_config
from constants import AUTOSTART_DIR, AUTOSTART_FILE, DEFAULT_DATA_DIR, IS_MACOS
from infrastructure.translation import ProviderRegistry
from version import get_version
from wotd import CEFR_LEVELS


def _get_autostart_enabled() -> bool:
    """Check if autostart is currently enabled."""
    return os.path.exists(AUTOSTART_FILE)


def _set_autostart(enabled: bool):
    """Enable or disable autostart."""
    if enabled:
        os.makedirs(AUTOSTART_DIR, exist_ok=True)
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(str(__file__)))), "vocab_gui.py"
        )
        python_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(str(__file__))))),
            "venv",
            "bin",
            "python3",
        )

        if IS_MACOS:
            # macOS LaunchAgent plist
            plist = {
                "Label": "com.vocab_app",
                "ProgramArguments": [python_path, script_path],
                "RunAtLoad": True,
                "KeepAlive": False,
            }
            with open(AUTOSTART_FILE, "wb") as f:
                plistlib.dump(plist, f)
        else:
            # Linux .desktop file
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Vocab App
Exec={python_path} {script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            with open(AUTOSTART_FILE, "w") as f:
                f.write(desktop_entry)
    elif os.path.exists(AUTOSTART_FILE):
        os.remove(AUTOSTART_FILE)


class SettingsWindow(Gtk.Window):
    """Settings window."""

    def __init__(self, vocab_service, on_save=None, config_file=None):
        super().__init__(title="Settings")
        self.vocab_service = vocab_service
        self.on_save = on_save
        self.config_file = config_file
        self.set_default_size(600, 1100)
        self.set_position(Gtk.WindowPosition.CENTER)

        self._test_completed = True

        self.build_ui()

    def build_ui(self) -> None:
        """Build the UI."""
        scroll = Gtk.ScrolledWindow()
        self.add(scroll)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_left(20)
        box.set_margin_right(20)
        scroll.add(box)

        # Review settings
        # Interval
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        interval_box.pack_start(Gtk.Label("Review Interval:"), False, False, 0)
        self.interval_combo = Gtk.ComboBoxText()
        intervals = [
            ("1800", "30 minutes"),
            ("3600", "1 hour"),
            ("7200", "2 hours"),
            ("14400", "4 hours"),
            ("28800", "8 hours"),
        ]
        for value, label in intervals:
            self.interval_combo.append(value, label)
        current_interval = str(self.vocab_service.get_setting("review_interval", DEFAULT_SETTINGS["review_interval"]))
        self.interval_combo.set_active_id(current_interval)
        interval_box.pack_end(self.interval_combo, False, False, 0)

        # Wrap REVIEW in frame
        review_frame = self._make_frame("Review", interval_box)
        box.pack_start(review_frame, False, False, 0)

        # Translation container for frame
        translation_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Provider
        provider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        provider_box.pack_start(Gtk.Label("Dictionary/API:"), False, False, 0)
        self.provider_combo = Gtk.ComboBoxText()
        for provider, name in ProviderRegistry.list_providers():
            self.provider_combo.append(provider, name)

        # Handle legacy "google" setting and default
        current_provider = self.vocab_service.get_settings().get(
            "translation_provider", "google_direct"
        )
        if current_provider == "google":
            current_provider = "google_direct"  # Legacy fallback
        if current_provider not in [p[0] for p in ProviderRegistry.list_providers()]:
            current_provider = "google_direct"  # Default if not found

        self.provider_combo.set_active_id(current_provider)
        provider_box.pack_end(self.provider_combo, False, False, 0)
        translation_box.pack_start(provider_box, False, False, 0)

        # Source language
        src_lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        src_lang_box.pack_start(Gtk.Label("Source Language:"), False, False, 0)
        self.src_lang_combo = Gtk.ComboBoxText()
        for lang in self.vocab_service.get_languages():
            self.src_lang_combo.append(lang.code, lang.name)
        current_src_lang = self.vocab_service.get_settings().get("source_lang", "en")
        self.src_lang_combo.set_active_id(current_src_lang)
        src_lang_box.pack_end(self.src_lang_combo, False, False, 0)
        translation_box.pack_start(src_lang_box, False, False, 0)

        # Target language
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lang_box.pack_start(Gtk.Label("Target Language:"), False, False, 0)
        self.lang_combo = Gtk.ComboBoxText()
        for lang in self.vocab_service.get_languages():
            self.lang_combo.append(lang.code, lang.name)
        current_lang = self.vocab_service.get_settings().get("target_lang", "ru")
        self.lang_combo.set_active_id(current_lang)
        lang_box.pack_end(self.lang_combo, False, False, 0)
        translation_box.pack_start(lang_box, False, False, 0)

        # Test API button
        test_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        test_btn = Gtk.Button(label="Test API")
        test_btn.connect("clicked", self.on_test_api)
        test_btn_box.pack_start(test_btn, False, False, 0)

        self.test_spinner = Gtk.Spinner()
        self.test_spinner.set_size_request(20, 20)
        self.test_spinner.hide()
        test_btn_box.pack_start(self.test_spinner, False, False, 0)

        self.test_status_label = Gtk.Label("")
        self.test_status_label.set_xalign(0)
        self.test_status_label.set_line_wrap(True)
        self.test_status_label.hide()
        test_btn_box.pack_start(self.test_status_label, True, True, 0)

        translation_box.pack_start(test_btn_box, False, False, 0)

        # Wrap translation in frame
        translation_frame = self._make_frame("Translation", translation_box)
        box.pack_start(translation_frame, False, False, 0)

        # Keyboard shortcuts container
        shortcuts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # Info label - platform-specific instructions
        if IS_MACOS:
            shortcut_info = (
                "Configure hotkeys in System Settings → Keyboard → Shortcuts → Services\n"
                "or use a tool like Hammerspoon / Karabiner.\n\n"
                "Commands:"
            )
        else:
            shortcut_info = (
                "Configure hotkeys in your desktop environment:\n"
                "(Usually Settings → Keyboard → Shortcuts)\n\n"
                "Commands:"
            )
        info_label = Gtk.Label(shortcut_info)
        info_label.set_xalign(0)
        info_label.set_line_wrap(True)
        shortcuts_box.pack_start(info_label, False, False, 0)

        # Commands info
        cli_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vocab_cli.py"
        )
        cmds_label = Gtk.Label(
            f"Save selected:   python3 {cli_path} --save\n"
            f"Delete current: python3 {cli_path} --delete\n"
            f"Show next:      python3 {cli_path} --next"
        )
        cmds_label.set_xalign(0)
        cmds_label.set_line_wrap(True)
        cmds_label.set_selectable(True)
        shortcuts_box.pack_start(cmds_label, False, False, 0)

        # Wrap in frame
        shortcuts_frame = self._make_frame("Keyboard Shortcuts", shortcuts_box)
        box.pack_start(shortcuts_frame, False, False, 0)

        # Startup settings
        self.autostart_check = Gtk.CheckButton(label="Start with system login")
        autostart = _get_autostart_enabled()
        self.autostart_check.set_active(autostart)

        # Wrap startup in frame
        startup_frame = self._make_frame("Startup", self.autostart_check)
        box.pack_start(startup_frame, False, False, 0)

        # Data directory
        data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        hint_label = Gtk.Label(f"Leave empty to use default: {DEFAULT_DATA_DIR}")
        hint_label.set_xalign(0)
        hint_label.set_line_wrap(True)
        data_box.pack_start(hint_label, False, False, 0)

        # Custom data directory (read from config file)
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dir_box.pack_start(Gtk.Label("Custom Path:"), False, False, 0)

        # Read from config file if available (JSON)
        config = read_config(self.config_file) if self.config_file else {}
        custom_data_dir = config.get("data_dir", "")

        self.data_dir_entry = Gtk.Entry()
        self.data_dir_entry.set_text(custom_data_dir)
        dir_box.pack_end(self.data_dir_entry, True, True, 0)
        data_box.pack_start(dir_box, False, False, 0)

        # Wrap data in frame
        data_frame = self._make_frame("Data", data_box)
        box.pack_start(data_frame, False, False, 0)

        # Word of the Day settings
        self.wotd_check = Gtk.CheckButton(label="Enable Word of the Day")
        wotd_enabled = self.vocab_service.get_setting("wotd_enabled", "false") == "true"
        self.wotd_check.set_active(wotd_enabled)

        wotd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        wotd_box.pack_start(self.wotd_check, False, False, 0)

        level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        level_box.pack_start(Gtk.Label("Level:"), False, False, 0)
        self.wotd_level_combo = Gtk.ComboBoxText()
        for level in CEFR_LEVELS:
            self.wotd_level_combo.append(level, level)

        current_level = self.vocab_service.get_setting("wotd_level", "B2")
        self.wotd_level_combo.set_active_id(current_level)
        level_box.pack_end(self.wotd_level_combo, False, False, 0)
        wotd_box.pack_start(level_box, False, False, 0)

        # Wrap WOTD in frame
        wotd_frame = self._make_frame("Word of the Day", wotd_box)
        box.pack_start(wotd_frame, False, False, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.destroy())
        btn_box.pack_start(cancel_btn, True, True, 0)

        save_btn = Gtk.Button(label="Save Settings")
        save_btn.connect("clicked", self.on_save_settings)
        btn_box.pack_start(save_btn, True, True, 0)

        box.pack_start(btn_box, False, False, 10)

        # Version footer
        footer_label = Gtk.Label(f"App version: {get_version()}")
        footer_label.set_xalign(0)
        footer_label.set_margin_top(10)
        footer_label.set_selectable(True)
        box.pack_start(footer_label, False, False, 0)

    def _make_section(self, title: str) -> Gtk.Label:
        """Make a section header."""
        label = Gtk.Label()
        label.set_markup(f"<b>{title}</b>")
        label.set_xalign(0)
        return label

    def _make_frame(self, title: str, content: Gtk.Widget) -> Gtk.Frame:
        """Wrap content in a frame with a border."""
        frame = Gtk.Frame(label=title)
        frame.set_shadow_type(Gtk.ShadowType.IN)
        align = Gtk.Alignment.new(0, 0, 1, 1)
        align.set_padding(10, 10, 10, 10)
        align.add(content)
        frame.add(align)
        return frame

    def on_test_api(self, widget: Gtk.Widget) -> None:
        """Test translation API."""
        if not self._test_completed:
            return

        provider = self.provider_combo.get_active_id()
        source_lang = self.src_lang_combo.get_active_id()
        target_lang = self.lang_combo.get_active_id()

        self.vocab_service.set_setting("translation_provider", provider)
        self.vocab_service.set_setting("source_lang", source_lang)
        self.vocab_service.set_setting("target_lang", target_lang)

        provider_name = ProviderRegistry.get(provider).get_name()
        self.test_status_label.set_text(f"Testing {provider_name}...")
        self.test_spinner.show()
        self.test_spinner.start()
        self._test_completed = False

        # Safety timeout: force failure after 30 seconds
        def test_timeout():
            if not self._test_completed:
                GLib.idle_add(self._test_complete, False, provider_name)
            return False

        GLib.timeout_add_seconds(30, test_timeout)

        def run_test():
            success = self.vocab_service.test_translation_api()
            GLib.idle_add(self._test_complete, success, provider_name)

        import threading

        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()

    def _test_complete(self, success, provider_name):
        """Handle test completion."""
        if self._test_completed:
            return
        self._test_completed = True

        self.test_spinner.stop()
        self.test_spinner.hide()

        status = "Success!" if success else "Failed!"
        detail = "works." if success else "not working."
        self.test_status_label.set_text(f"{status} {provider_name} {detail}")

        GLib.timeout_add(3000, self._clear_test_status)

    def _clear_test_status(self):
        """Clear the test status after a delay."""
        self.test_status_label.set_text("")
        return False

    def on_save_settings(self, widget: Gtk.Widget) -> None:
        """Save settings."""
        settings = {
            "review_interval": self.interval_combo.get_active_id(),
            "translation_provider": self.provider_combo.get_active_id(),
            "source_lang": self.src_lang_combo.get_active_id(),
            "target_lang": self.lang_combo.get_active_id(),
            "autostart": "true" if self.autostart_check.get_active() else "false",
            "wotd_enabled": "true" if self.wotd_check.get_active() else "false",
            "wotd_level": self.wotd_level_combo.get_active_id(),
        }

        new_data_dir = self.data_dir_entry.get_text().strip()

        data_dir_changed = False
        if self.config_file:
            config = read_config(self.config_file)
            old_data_dir = config.get("data_dir", "")
            if old_data_dir != new_data_dir:
                data_dir_changed = True
            config["data_dir"] = new_data_dir
            write_config(self.config_file, config)

        self.vocab_service.save_settings(settings)

        # Handle autostart
        _set_autostart(self.autostart_check.get_active())

        if self.on_save:
            self.on_save(settings)

        # Show confirmation
        if data_dir_changed:
            msg_text = (
                "Settings saved!\n\n"
                "Note: You need to restart the app for data directory changes to take effect."
            )
        else:
            msg_text = "Settings saved successfully!"

        msg = Gtk.MessageDialog(
            self,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            msg_text,
        )
        msg.run()
        msg.destroy()
