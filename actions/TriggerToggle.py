"""
TriggerToggle — enable or disable a Twitchat trigger by ID.
Companion to TriggerExecute — this toggles the on/off state rather than firing.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



TOGGLE_MODES = {
    "enable": "Enable Trigger",
    "disable": "Disable Trigger",
}


class TriggerToggle(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "trigger.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self._update_display()

    def on_key_down(self):
        settings = self.get_settings()
        trigger_id = settings.get("trigger_id", "")
        mode = settings.get("mode", "enable")
        if trigger_id:
            enabled = mode == "enable"
            self.plugin_base.twitchat.send_action("TOGGLE_TRIGGER", {
                "triggerId": trigger_id,
                "enabled": enabled,
            })

    def _update_display(self):
        settings = self.get_settings()
        trigger_id = settings.get("trigger_id", "")
        mode = settings.get("mode", "enable")
        label = TOGGLE_MODES.get(mode, "Toggle")
        if trigger_id:
            self.set_bottom_label(f"{label[:7]} {trigger_id[:4]}")
        else:
            self.set_bottom_label(label[:8])

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_id = settings.get("trigger_id", "")
        current_mode = settings.get("mode", "enable")

        id_entry = Gtk.Entry()
        id_entry.set_text(current_id)
        id_entry.set_placeholder_text("Trigger ID")
        id_entry.connect("changed", lambda e: self._on_setting("trigger_id", e.get_text()))

        mode_combo = Gtk.ComboBoxText()
        for key, label in TOGGLE_MODES.items():
            mode_combo.append(key, label)
        mode_combo.set_active_id(current_mode)
        mode_combo.connect("changed", lambda c: self._on_setting("mode", c.get_active_id()))

        id_row = Adw.ActionRow(title="Trigger ID")
        id_row.add_suffix(id_entry)

        mode_row = Adw.ActionRow(title="Action")
        mode_row.add_suffix(mode_combo)

        return [id_row, mode_row]

    def _on_setting(self, key: str, value):
        settings = self.get_settings()
        settings[key] = value
        self.set_settings(settings)
        self._update_display()
