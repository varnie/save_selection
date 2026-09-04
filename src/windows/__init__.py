# Windows package - shared GTK helpers for dialog windows.

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class BaseWindow(Gtk.Window):
    """Base window with centered position and default size."""

    def __init__(self, title: str, width: int, height: int) -> None:
        super().__init__(title=title)
        self.set_default_size(width, height)
        self.set_position(Gtk.WindowPosition.CENTER)


def set_margins(widget: Gtk.Widget, margin: int) -> None:
    """Apply uniform margins to an existing widget."""
    widget.set_margin_top(margin)
    widget.set_margin_bottom(margin)
    widget.set_margin_left(margin)
    widget.set_margin_right(margin)


def padded_box(
    orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL,
    spacing: int = 10,
    margin: int = 20,
) -> Gtk.Box:
    """Create a box with uniform margins."""
    box = Gtk.Box(orientation=orientation, spacing=spacing)
    set_margins(box, margin)
    return box


def show_message(parent: Gtk.Window, kind: Gtk.MessageType, text: str) -> None:
    """Show a modal OK dialog."""
    dialog = Gtk.MessageDialog(
        parent,
        Gtk.DialogFlags.DESTROY_WITH_PARENT,
        kind,
        Gtk.ButtonsType.OK,
        text,
    )
    dialog.run()
    dialog.destroy()


def ask_confirm(parent: Gtk.Window, text: str) -> bool:
    """Show a modal Yes/No dialog, return True on Yes."""
    dialog = Gtk.MessageDialog(
        parent,
        Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        Gtk.ButtonsType.YES_NO,
        text,
    )
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.YES


__all__ = ["BaseWindow", "ask_confirm", "padded_box", "set_margins", "show_message"]
