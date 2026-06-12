"""
SendMessage action — sends a pre-configured chat message via SEND_MESSAGE.
Use for quick-chat macros like !commands, !discord, !lurk, etc.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



class SendMessage(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "chat.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self._update_display()

    def on_key_down(self):
        settings = self.get_settings()
        message = settings.get("message", "")
        if message:
            self.plugin_base.twitchat.send_action("SEND_MESSAGE", {"message": message})

    def _update_display(self):
        settings = self.get_settings()
        message = settings.get("message", "")
        label = message[:8] if message else "Send Msg"
        self.set_bottom_label(label)

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_message = settings.get("message", "")

        entry = Gtk.Entry()
        entry.set_text(current_message)
        entry.set_placeholder_text("!commands")
        entry.connect("changed", lambda e: self._on_message_changed(e.get_text()))

        row = Adw.ActionRow(title="Chat Message")
        row.add_suffix(entry)

        return [row]

    def _on_message_changed(self, value: str):
        settings = self.get_settings()
        settings["message"] = value
        self.set_settings(settings)
        self._update_display()
