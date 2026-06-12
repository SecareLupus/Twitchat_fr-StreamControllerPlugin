"""
RaffleControl — start, pick winner, or end a Twitchat chat raffle.
Displays the raffle winner name when a RAFFLE_RESULT event fires.

Modes:
  - Start: sends RAFFLE_START with configured command/duration
  - Pick Winner: sends RAFFLE_PICK_WINNER
  - End: sends RAFFLE_END
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



RAFFLE_MODES = {
    "start": "Start Raffle",
    "pick": "Pick Winner",
    "end": "End Raffle",
}


class RaffleControl(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        self._last_winner: str = ""

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "raffle.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("RAFFLE_RESULT", self._on_raffle_result)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("RAFFLE_RESULT", self._on_raffle_result)

    def on_key_down(self):
        settings = self.get_settings()
        mode = settings.get("mode", "start")

        if mode == "start":
            command = settings.get("command", "!join")
            duration = settings.get("duration", 60)
            data = {
                "mode": "chat",
                "command": command,
                "duration_s": duration,
                "showCountdownOverlay": True,
            }
            self.plugin_base.twitchat.send_action("RAFFLE_START", data)
        elif mode == "pick":
            self.plugin_base.twitchat.send_action("RAFFLE_PICK_WINNER")
        elif mode == "end":
            self.plugin_base.twitchat.send_action("RAFFLE_END")

    def _on_raffle_result(self, data):
        if data and "label" in data:
            self._last_winner = data.get("label", "")
            self._update_display()
            # Flash green briefly
            self.set_background_color([0, 200, 0, 255])

    def _update_display(self):
        settings = self.get_settings()
        mode = settings.get("mode", "start")
        if self._last_winner:
            self.set_center_label(f"Winner:{self._last_winner[:7]}")
        else:
            self.set_center_label("Raffle")
        self.set_bottom_label(RAFFLE_MODES.get(mode, "Start"))

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_mode = settings.get("mode", "start")
        current_command = settings.get("command", "!join")
        current_duration = settings.get("duration", 60)

        mode_combo = Gtk.ComboBoxText()
        for key, label in RAFFLE_MODES.items():
            mode_combo.append(key, label)
        mode_combo.set_active_id(current_mode)
        mode_combo.connect("changed", lambda c: self._on_setting_changed("mode", c.get_active_id()))

        cmd_entry = Gtk.Entry()
        cmd_entry.set_text(current_command)
        cmd_entry.set_placeholder_text("!join")
        cmd_entry.connect("changed", lambda e: self._on_setting_changed("command", e.get_text()))

        dur_adj = Gtk.Adjustment(value=current_duration, lower=10, upper=600, step_increment=10)
        dur_spinner = Gtk.SpinButton(adjustment=dur_adj)
        dur_spinner.set_value(current_duration)
        dur_spinner.connect("value-changed", lambda s: self._on_setting_changed("duration", s.get_value_as_int()))

        mode_row = Adw.ActionRow(title="Mode")
        mode_row.add_suffix(mode_combo)

        cmd_row = Adw.ActionRow(title="Chat Command")
        cmd_row.add_suffix(cmd_entry)

        dur_row = Adw.ActionRow(title="Duration (seconds)")
        dur_row.add_suffix(dur_spinner)

        return [mode_row, cmd_row, dur_row]

    def _on_setting_changed(self, key: str, value):
        settings = self.get_settings()
        settings[key] = value
        self.set_settings(settings)
        self._update_display()
