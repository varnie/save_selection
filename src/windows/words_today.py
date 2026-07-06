"""Words added today window."""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class WordsTodayWindow(Gtk.Window):
    """Window showing words added today."""

    def __init__(self, vocab_service):
        super().__init__(title="Words Added Today")
        self.vocab_service = vocab_service
        self.set_default_size(500, 400)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.build_ui()

    def build_ui(self) -> None:
        """Build the UI."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_left(10)
        vbox.set_margin_right(10)
        self.add(vbox)

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
