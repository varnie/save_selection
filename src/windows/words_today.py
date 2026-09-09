"""Words added today window."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from windows import BaseWindow, padded_box


class WordsTodayWindow(BaseWindow):
    """Window showing words added today."""

    def __init__(self, vocab_service):
        super().__init__(title="Words Added Today", width=500, height=400)
        self.vocab_service = vocab_service
        self.build_ui()

    def build_ui(self) -> None:
        """Build the UI."""
        vbox = padded_box(spacing=6, margin=10)
        self.add(vbox)

        self.wotd_label = Gtk.Label("")
        self.wotd_label.set_xalign(0)
        vbox.pack_start(self.wotd_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        vbox.pack_start(scrolled, True, True, 0)

        self.list_store = Gtk.ListStore(str, str)
        self.tree_view = Gtk.TreeView(model=self.list_store)
        self.tree_view.set_headers_visible(True)

        word_col = Gtk.TreeViewColumn("Word", Gtk.CellRendererText(), text=0)
        word_col.set_resizable(True)
        word_col.set_sort_column_id(0)
        self.tree_view.append_column(word_col)

        trans_col = Gtk.TreeViewColumn("Translation", Gtk.CellRendererText(), text=1)
        trans_col.set_resizable(True)
        trans_col.set_sort_column_id(1)
        self.tree_view.append_column(trans_col)

        scrolled.add(self.tree_view)

        self._populate()

    def _populate(self) -> None:
        """Fetch and display words added today."""
        self.list_store.clear()
        words = self.vocab_service.get_words_added_today()
        for w in words:
            self.list_store.append([w.phrase, w.translation or ""])
        self._refresh_wotd_banner()

    def _refresh_wotd_banner(self) -> None:
        """Show today's Word of the Day above the list, if already shown."""
        today = self.vocab_service.get_today_display()
        if today is None:
            self.wotd_label.hide()
            return
        word, translation, level = today
        text = f"⭐ Word of the Day [{level}]: {word}"
        if translation:
            text += f" → {translation}"
        self.wotd_label.set_text(text)
        self.wotd_label.show()
