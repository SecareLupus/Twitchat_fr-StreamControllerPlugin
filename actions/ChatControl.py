"""
Chat Control action — marks messages read, scrolls, pauses the Twitchat chat feed.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



CHAT_OPERATIONS = {
    "greet_read": {"label": "Greet Feed: Mark Read", "action": "GREET_FEED_READ", "has_count": True},
    "greet_read_all": {"label": "Greet Feed: Mark All Read", "action": "GREET_FEED_READ_ALL", "has_count": False},
    "chat_read": {"label": "Chat Feed: Mark Read", "action": "CHAT_FEED_READ", "has_count": True},
    "chat_read_all": {"label": "Chat Feed: Mark All Read", "action": "CHAT_FEED_READ_ALL", "has_count": False},
    "chat_pause": {"label": "Chat Feed: Pause", "action": "CHAT_FEED_PAUSE", "has_count": False},
    "chat_unpause": {"label": "Chat Feed: Unpause", "action": "CHAT_FEED_UNPAUSE", "has_count": False},
    "chat_scroll_up": {"label": "Chat Feed: Scroll Up", "action": "CHAT_FEED_SCROLL_UP", "has_count": True},
    "chat_scroll_down": {"label": "Chat Feed: Scroll Down", "action": "CHAT_FEED_SCROLL_DOWN", "has_count": True},
}


class ChatControl(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "chat.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self._update_icon()

    def on_key_down(self):
        settings = self.get_settings()
        operation_key = settings.get("operation", "greet_read")
        op = CHAT_OPERATIONS.get(operation_key, CHAT_OPERATIONS["greet_read"])

        data = None
        if op["has_count"]:
            count = settings.get("count", 1)
            if op["action"] in ("CHAT_FEED_SCROLL_UP", "CHAT_FEED_SCROLL_DOWN"):
                data = {"scrollBy": count}
            else:
                data = {"count": count}

        self.plugin_base.twitchat.send_action(op["action"], data)
        self._update_icon()

    def _update_icon(self):
        settings = self.get_settings()
        operation_key = settings.get("operation", "greet_read")
        op = CHAT_OPERATIONS.get(operation_key, CHAT_OPERATIONS["greet_read"])
        label = op["label"].split(": ")[-1] if ": " in op["label"] else op["label"]
        self.set_bottom_label(label[:8])

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_op = settings.get("operation", "greet_read")
        current_count = settings.get("count", 1)

        op_combo = Gtk.ComboBoxText()
        for key, op in CHAT_OPERATIONS.items():
            op_combo.append(key, op["label"])
        op_combo.set_active_id(current_op)
        op_combo.connect("changed", lambda c: self._on_operation_changed(c.get_active_id()))

        count_adj = Gtk.Adjustment(value=current_count, lower=-50, upper=500, step_increment=1)
        count_spinner = Gtk.SpinButton(adjustment=count_adj)
        count_spinner.set_value(current_count)
        count_spinner.set_visible(CHAT_OPERATIONS[current_op]["has_count"])
        count_spinner.connect("value-changed", lambda s: self._on_count_changed(s.get_value_as_int()))

        op_row = Adw.ActionRow(title="Operation")
        op_row.add_suffix(op_combo)

        count_row = Adw.ActionRow(title="Count / Scroll Pixels")
        count_row.add_suffix(count_spinner)

        return [op_row, count_row]

    def _on_operation_changed(self, key: str):
        settings = self.get_settings()
        settings["operation"] = key
        self.set_settings(settings)
        self._update_icon()

    def _on_count_changed(self, value: int):
        settings = self.get_settings()
        settings["count"] = value
        self.set_settings(settings)
