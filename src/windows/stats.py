#!/usr/bin/env python3
"""Stats window."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class StatsWindow(Gtk.Window):
    """Statistics window."""

    def __init__(self, vocab_service):
        super().__init__(title="Vocabulary Statistics")
        self.vocab_service = vocab_service
        self.set_default_size(400, 450)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.build_ui()

    def build_ui(self):
        """Build the UI."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_left(20)
        box.set_margin_right(20)
        self.add(box)

        # Title
        title = Gtk.Label()
        title.set_markup("<b>Vocabulary Statistics</b>")
        title.get_style_context().add_class("title")
        box.pack_start(title, False, False, 0)

        # Stats
        stats = self.vocab_service.get_stats()

        # Total words
        row = self._make_row("Total words:", str(stats.get("total_words", 0)))
        box.pack_start(row, False, False, 0)

        # Added today
        row = self._make_row("Added today:", str(stats.get("today_words", 0)))
        box.pack_start(row, False, False, 0)

        # Reviews today
        row = self._make_row("Reviews today:", str(stats.get("today_reviews", 0)))
        box.pack_start(row, False, False, 0)

        # Total reviews
        row = self._make_row("Total reviews:", str(stats.get("total_reviews", 0)))
        box.pack_start(row, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 10)

        # Streak
        streak = stats.get("streak", 0)
        streak_row = self._make_row(f"Streak:", f"{streak} days")
        box.pack_start(streak_row, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 10)

        # Due/overdue
        row = self._make_row("Due/overdue:", str(stats.get("due_count", 0)))
        box.pack_start(row, False, False, 0)

        # Short interval
        row = self._make_row("Learning (≤7 days):", str(stats.get("short_interval", 0)))
        box.pack_start(row, False, False, 0)

        # Long interval
        row = self._make_row("Mastered (>7 days):", str(stats.get("long_interval", 0)))
        box.pack_start(row, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 10)

        # Quiz stats
        quiz_stats = self.vocab_service.get_quiz_stats()
        if quiz_stats["total_quizzes"] > 0:
            quiz_title = Gtk.Label()
            quiz_title.set_markup("<b>Quiz</b>")
            box.pack_start(quiz_title, False, False, 0)

            row = self._make_row("Quizzes taken:", str(quiz_stats["total_quizzes"]))
            box.pack_start(row, False, False, 0)

            row = self._make_row("Average score:", f"{quiz_stats['avg_score']}%")
            box.pack_start(row, False, False, 0)

            row = self._make_row("Best score:", f"{quiz_stats['best_score']}%")
            box.pack_start(row, False, False, 0)

            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            box.pack_start(sep, False, False, 10)

        # Export button
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        export_btn = Gtk.Button(label="Export CSV")
        export_btn.connect("clicked", self.on_export)
        btn_box.pack_start(export_btn, True, True, 0)
        box.pack_start(btn_box, False, False, 0)

    def _make_row(self, label: str, value: str) -> Gtk.Box:
        """Make a stat row."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        lbl = Gtk.Label(label)
        lbl.set_xalign(0)
        lbl.set_hexpand(True)
        box.pack_start(lbl, True, True, 0)
        
        val = Gtk.Label(value)
        val.set_xalign(1)
        box.pack_start(val, False, False, 0)
        
        return box

    def on_export(self, widget):
        """Export to CSV."""
        dialog = Gtk.FileChooserDialog(
            "Export to CSV",
            self,
            Gtk.FileChooserAction.SAVE,
            ("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
        )
        dialog.set_current_name("vocabulary.csv")

        if dialog.run() == Gtk.ResponseType.OK:
            try:
                self.vocab_service.export_csv(dialog.get_filename())
                msg = Gtk.MessageDialog(
                    self,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.INFO,
                    Gtk.ButtonsType.OK,
                    "Export successful!"
                )
                msg.run()
                msg.destroy()
            except Exception as e:
                msg = Gtk.MessageDialog(
                    self,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.OK,
                    f"Export failed: {e}"
                )
                msg.run()
                msg.destroy()

        dialog.destroy()

    def refresh(self):
        """Refresh stats."""
        child = self.get_child()
        if child:
            self.remove(child)
        self.build_ui()
