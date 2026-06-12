"""
CounterControl — increment/decrement a Twitchat counter and display its current value.

Sends COUNTER_ADD to increment (or decrement with negative value).
Displays COUNTER_UPDATE events to show the counter's current value on the key.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



class CounterControl(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        self._counter_name: str = ""
        self._counter_value: int = 0
        self._counter_id: str = ""

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "counter.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("COUNTER_UPDATE", self._on_counter_update)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("COUNTER_UPDATE", self._on_counter_update)

    def on_key_down(self):
        settings = self.get_settings()
        counter_id = settings.get("counter_id", "")
        amount = settings.get("amount", 1)

        if counter_id:
            self.plugin_base.twitchat.send_action("COUNTER_ADD", {
                "id": counter_id,
                "amount": amount,
            })
            self._counter_id = counter_id

    def on_key_up(self):
        # Send GET to refresh after increment
        pass

    def _on_counter_update(self, data):
        if not data:
            return
        # Match against our configured counter ID
        if self._counter_id and data.get("id") != self._counter_id:
            return

        self._counter_name = data.get("name", "")
        self._counter_value = data.get("value", 0)
        self._counter_id = data.get("id", self._counter_id)
        self._update_display()

    def _update_display(self):
        if self._counter_name:
            self.set_center_label(str(self._counter_value))
            self.set_bottom_label(self._counter_name[:8])
        else:
            self.set_center_label("Counter")
            self.set_bottom_label("Set ID first")

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_id = settings.get("counter_id", "")
        current_amount = settings.get("amount", 1)

        id_entry = Gtk.Entry()
        id_entry.set_text(current_id)
        id_entry.set_placeholder_text("Counter ID (UUID)")
        id_entry.connect("changed", lambda e: self._on_setting_changed("counter_id", e.get_text()))

        amount_adj = Gtk.Adjustment(value=current_amount, lower=-100, upper=100, step_increment=1)
        amount_spinner = Gtk.SpinButton(adjustment=amount_adj)
        amount_spinner.set_value(current_amount)
        amount_spinner.connect("value-changed", lambda s: self._on_setting_changed("amount", s.get_value_as_int()))

        id_row = Adw.ActionRow(title="Counter ID")
        id_row.add_suffix(id_entry)

        amount_row = Adw.ActionRow(title="Step (+/-)")
        amount_row.add_suffix(amount_spinner)

        return [id_row, amount_row]

    def _on_setting_changed(self, key: str, value):
        settings = self.get_settings()
        settings[key] = value
        self.set_settings(settings)
        # If counter ID changed, request its current value
        if key == "counter_id" and value:
            self._counter_id = value
            self.plugin_base.twitchat.send_action("COUNTER_GET", {"id": value})
        self._update_display()
