"""Word browser window."""

import gi

gi.require_version("Gtk", "3.0")
from datetime import datetime, timezone

from gi.repository import GLib, Gtk

from domain.entities import Word


class WordBrowserWindow(Gtk.Window):
    """Word browser and manager window."""

    search_entry: Gtk.Entry
    lang_combo: Gtk.ComboBoxText
    model: Gtk.ListStore
    treeview: Gtk.TreeView
    delete_btn: Gtk.Button
    status_label: Gtk.Label

    def __init__(self, vocab_service) -> None:
        super().__init__(title="Word Browser")
        self.vocab_service = vocab_service
        self.selected_word_id: int | None = None
        self.words: list[Word] = []
        self.page_size = 100
        self.current_page = 0
        self._search_timer_id: int | None = None
        self.set_default_size(910, 600)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.build_ui()
        self.load_words()

    def build_ui(self) -> None:
        """Build the UI."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(15)
        main_box.set_margin_bottom(15)
        main_box.set_margin_left(15)
        main_box.set_margin_right(15)
        self.add(main_box)

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(toolbar, False, False, 0)

        # Search entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search words...")
        self.search_entry.set_width_chars(25)
        self.search_entry.connect("changed", self.on_search_changed)
        self.search_entry.connect("activate", self.on_search_activate)
        toolbar.pack_start(self.search_entry, False, False, 0)

        # Language filter
        toolbar.pack_start(Gtk.Label("Language:"), False, False, 5)

        self.lang_combo = Gtk.ComboBoxText()
        settings = self.vocab_service.get_settings()
        current_lang = settings.get("target_lang", "ru")

        # Get word counts per language
        lang_counts = self.vocab_service.get_language_counts()
        languages = self.vocab_service.get_languages()
        sorted_languages = sorted(languages, key=lambda lang: lang.name)
        lang_names = {lang.code: lang.name for lang in languages}

        # Current language count and name
        current_name, current_count = lang_counts.get(current_lang, (None, 0)) if current_lang else (None, 0)
        if not current_name:
            current_name = lang_names.get(current_lang, current_lang.upper() if current_lang else "")

        if current_count > 0:
            self.lang_combo.append(current_lang, f"{current_name} ({current_count})")

        # Sort languages alphabetically and add with counts
        for lang in sorted_languages:
            if lang.code == current_lang:
                continue
            name, count = lang_counts.get(lang.code, (lang.name, 0))
            if count > 0:
                self.lang_combo.append(lang.code, f"{name} ({count})")

        self.lang_combo.set_active_id(current_lang if current_lang else "")
        self.lang_combo.connect("changed", self.on_lang_changed)
        toolbar.pack_start(self.lang_combo, False, False, 0)

        # Refresh button
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", self.on_refresh)
        toolbar.pack_start(refresh_btn, False, False, 0)

        # TreeView
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        main_box.pack_start(scrolled, True, True, 0)

        # Create model for TreeView
        self.model = Gtk.ListStore(int, str, str, str)
        self.treeview = Gtk.TreeView(model=self.model)

        # Columns
        columns = [
            ("#", 50),
            ("Word", 300),
            ("Translation", 300),
            ("Last reviewed", 120),
        ]

        for i, (title, width) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_fixed_width(width)
            column.set_sort_column_id(i)
            self.treeview.append_column(column)

        self.treeview.connect("row-activated", self.on_row_activated)
        self.treeview.connect("cursor-changed", self.on_cursor_changed)
        scrolled.add(self.treeview)

        # Bottom bar
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(bottom_bar, False, False, 0)

        # Delete button
        self.delete_btn = Gtk.Button(label="Delete Selected")
        self.delete_btn.connect("clicked", self.on_delete)
        self.delete_btn.set_sensitive(False)
        bottom_bar.pack_start(self.delete_btn, False, False, 0)

        # Pagination
        self.prev_btn = Gtk.Button(label="← Prev")
        self.prev_btn.connect("clicked", self.on_prev_page)
        bottom_bar.pack_start(self.prev_btn, False, False, 0)

        self.next_btn = Gtk.Button(label="Next →")
        self.next_btn.connect("clicked", self.on_next_page)
        bottom_bar.pack_start(self.next_btn, False, False, 0)

        # Status label
        self.status_label = Gtk.Label("")
        self.status_label.set_xalign(0)
        bottom_bar.pack_start(self.status_label, True, True, 0)

    def load_words(self) -> None:
        """Load words from database."""
        search = self.search_entry.get_text().strip() or None
        lang = self.lang_combo.get_active_id() if self.lang_combo.get_model() else None

        # If empty or None, use current language from settings
        if not lang:
            settings = self.vocab_service.get_settings()
            lang = settings.get("target_lang", "ru")

        self.words = self.vocab_service.get_words(
            search=search,
            target_lang=lang,
            limit=self.page_size,
            offset=self.current_page * self.page_size,
        )
        self.refresh_model()

    def refresh_model(self) -> None:
        """Refresh the tree model."""
        self.model.clear()

        for i, word in enumerate(self.words):
            phrase = word.phrase
            target = word.translation
            last_reviewed_ts = word.last_reviewed

            if last_reviewed_ts:
                lr = datetime.fromtimestamp(last_reviewed_ts, tz=timezone.utc)
                last_reviewed_str = lr.strftime("%Y-%m-%d")
            else:
                last_reviewed_str = "Never"

            self.model.append([i + 1, phrase, target, last_reviewed_str])

        total = len(self.words)
        start = self.current_page * self.page_size + 1 if total > 0 else 0
        end = start + total - 1
        self.status_label.set_text(f"Showing: {start}-{end}  (page {self.current_page + 1})")
        self.prev_btn.set_sensitive(self.current_page > 0)
        self.next_btn.set_sensitive(total == self.page_size)

    def on_search_changed(self, widget: Gtk.Widget) -> None:
        """Handle search entry changed with debounce."""
        if self._search_timer_id is not None:
            GLib.source_remove(self._search_timer_id)
        self._search_timer_id = GLib.timeout_add(300, self._debounced_search)

    def _debounced_search(self) -> bool:
        """Debounced search callback."""
        self._search_timer_id = None
        self.current_page = 0
        self.load_words()
        return False

    def on_search_activate(self, widget: Gtk.Widget) -> None:
        """Handle search entry Enter key."""
        if self._search_timer_id is not None:
            GLib.source_remove(self._search_timer_id)
            self._search_timer_id = None
        self.current_page = 0
        self.load_words()

    def on_lang_changed(self, widget: Gtk.Widget) -> None:
        """Handle language dropdown changed."""
        self.load_words()

    def on_refresh(self, widget: Gtk.Widget) -> None:
        """Handle refresh button clicked."""
        self.current_page = 0
        self.load_words()

    def on_prev_page(self, widget: Gtk.Widget) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_words()

    def on_next_page(self, widget: Gtk.Widget) -> None:
        """Go to next page."""
        self.current_page += 1
        self.load_words()

    def on_cursor_changed(self, widget: Gtk.Widget) -> None:
        """Handle row selection."""
        selection = self.treeview.get_selection()
        model, it = selection.get_selected()

        if it and model:
            idx = model.get_value(it, 0) - 1
            if 0 <= idx < len(self.words):
                self.selected_word_id = self.words[idx].id
                self.delete_btn.set_sensitive(True)
            else:
                self.selected_word_id = None
                self.delete_btn.set_sensitive(False)
        else:
            self.selected_word_id = None
            self.delete_btn.set_sensitive(False)

    def on_row_activated(
        self, treeview: Gtk.TreeView, path: Gtk.TreePath, column: Gtk.TreeViewColumn
    ) -> None:
        """Handle row double-clicked."""
        model = treeview.get_model()
        it = model.get_iter(path)
        if it:
            idx = model.get_value(it, 0) - 1
            if 0 <= idx < len(self.words):
                word = self.words[idx]
                self.show_edit_dialog(word)

    def on_delete(self, widget: Gtk.Widget) -> None:
        """Handle delete button clicked."""
        if not self.selected_word_id:
            return

        # Find the word
        word = None
        for w in self.words:
            if w.id == self.selected_word_id:
                word = w
                break

        if not word:
            return

        # Get current language from dropdown
        current_lang = self.lang_combo.get_active_id() if self.lang_combo.get_model() else None

        # Confirm dialog
        dialog = Gtk.MessageDialog(
            self,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO,
            f"Delete translation for '{word.phrase}'?",
        )
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            # Only delete translation for current language, not the whole word
            self.vocab_service.delete_translation(self.selected_word_id, current_lang)
            self.selected_word_id = None
            self.load_words()
            self.refresh_lang_dropdown()

    def refresh_lang_dropdown(self) -> None:
        """Refresh language dropdown counts."""
        lang_counts = self.vocab_service.get_language_counts()

        # Preserve current selection before rebuilding
        selected_lang = self.lang_combo.get_active_id() if self.lang_combo.get_model() else None
        if not selected_lang:
            settings = self.vocab_service.get_settings()
            selected_lang = settings.get("target_lang", "ru")

        # Get all languages and update counts
        languages = self.vocab_service.get_languages()
        sorted_languages = sorted(languages, key=lambda lang: lang.name)
        lang_names = {lang.code: lang.name for lang in languages}

        self.lang_combo.remove_all()

        # Add selected language first (only if has words)
        selected_name, selected_count = lang_counts.get(selected_lang, (None, 0)) if selected_lang else (None, 0)
        if not selected_name:
            selected_name = lang_names.get(selected_lang, selected_lang.upper() if selected_lang else "")

        if selected_count > 0:
            self.lang_combo.append(selected_lang, f"{selected_name} ({selected_count})")

        # Add other languages
        for lang in sorted_languages:
            if lang.code == selected_lang:
                continue
            name, count = lang_counts.get(lang.code, (lang.name, 0))
            if count > 0:
                self.lang_combo.append(lang.code, f"{name} ({count})")

        # Set active to preserved selection
        self.lang_combo.set_active_id(selected_lang if selected_count > 0 else "")

        # Reload words with the selected language
        self.load_words()

    def show_edit_dialog(self, word: Word) -> None:
        """Show edit dialog for a word."""
        dialog = Gtk.Dialog(
            "Edit Word",
            self,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK),
        )

        box = dialog.get_content_area()
        box.set_margin_top(15)
        box.set_margin_bottom(15)
        box.set_margin_left(15)
        box.set_margin_right(15)

        # Word entry
        box.pack_start(Gtk.Label("Word:"), False, False, 5)
        word_entry = Gtk.Entry()
        word_entry.set_text(word.phrase)
        box.pack_start(word_entry, False, False, 5)

        # Translation entry
        box.pack_start(Gtk.Label("Translation:"), False, False, 5)
        trans_entry = Gtk.Entry()
        trans_entry.set_text(word.translation)
        box.pack_start(trans_entry, False, False, 5)

        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_phrase = word_entry.get_text().strip()
            new_trans = trans_entry.get_text().strip()

            if new_phrase:
                self.vocab_service.update_word(
                    word.id, new_phrase, new_trans if new_trans else None
                )
                self.load_words()
                self.refresh_lang_dropdown()

        dialog.destroy()
