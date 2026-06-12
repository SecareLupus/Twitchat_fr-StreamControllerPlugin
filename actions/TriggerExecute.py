"""
Trigger Execute action — executes a named Twitchat trigger by ID.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



class TriggerExecute(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "trigger.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self._update_icon()

    def on_key_down(self):
        settings = self.get_settings()
        trigger_id = settings.get("trigger_id", "")
        if trigger_id:
            self.plugin_base.twitchat.send_action("EXECUTE_TRIGGER", {"triggerId": trigger_id})
        self._update_icon()

    def _update_icon(self):
        settings = self.get_settings()
        trigger_id = settings.get("trigger_id", "")
        label = trigger_id[:8] if trigger_id else "Trigger"
        self.set_bottom_label(label)

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_id = settings.get("trigger_id", "")

        entry = Gtk.Entry()
        entry.set_text(current_id)
        entry.set_placeholder_text("Trigger ID (use Ctrl+Alt+D in Twitchat)")
        entry.connect("changed", lambda e: self._on_trigger_id_changed(e.get_text()))

        help_label = Gtk.Label(
            label="Find trigger IDs in Twitchat: open the triggers list and press Ctrl+Alt+D.",
            xalign=0, wrap=True
        )

        row = Adw.ActionRow(title="Trigger ID")
        row.add_suffix(entry)

        help_row = Adw.ActionRow()
        help_row.set_child(help_label)

        return [row, help_row]

    def _on_trigger_id_changed(self, value: str):
        settings = self.get_settings()
        settings["trigger_id"] = value
        self.set_settings(settings)
        self._update_icon()
