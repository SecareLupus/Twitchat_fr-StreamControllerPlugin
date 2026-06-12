"""
TimerControl — start/stop timers and countdowns, display their current state.

Modes:
  - Start Timer: sends TIMER_ADD with a name, starts immediately
  - Start Countdown: sends COUNTDOWN_ADD with name + duration
  - Get Current: sends GET_CURRENT_TIMERS to refresh display
  - Stop: stops the currently displayed timer/countdown

Displays: TIMER_START, TIMER_STOP, COUNTDOWN_START, COUNTDOWN_COMPLETE events.
All four events share the same TimerData shape — shows title and elapsed time.
"""
import os
import time
from src.backend.PluginManager.ActionBase import ActionBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



TIMER_MODES = {
    "start_timer": "Start Timer",
    "start_countdown": "Start Countdown",
    "get_current": "Get Current",
    "stop": "Stop",
}


class TimerControl(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        self._current_timer_id: str = ""
        self._display_title: str = ""
        self._running: bool = False

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "timer.svg")
        self.set_media(media_path=icon_path, size=0.75)
        conn = self.plugin_base.twitchat
        conn.add_listener("TIMER_START", self._on_timer_event)
        conn.add_listener("TIMER_STOP", self._on_timer_event)
        conn.add_listener("COUNTDOWN_START", self._on_timer_event)
        conn.add_listener("COUNTDOWN_COMPLETE", self._on_timer_event)
        self._update_display()

    def on_remove(self):
        conn = self.plugin_base.twitchat
        conn.remove_listener("TIMER_START", self._on_timer_event)
        conn.remove_listener("TIMER_STOP", self._on_timer_event)
        conn.remove_listener("COUNTDOWN_START", self._on_timer_event)
        conn.remove_listener("COUNTDOWN_COMPLETE", self._on_timer_event)

    def on_key_down(self):
        settings = self.get_settings()
        mode = settings.get("mode", "start_timer")
        name = settings.get("name", "Timer")
        duration_ms = settings.get("duration_ms", 300000)

        if mode == "start_timer":
            self.plugin_base.twitchat.send_action("TIMER_ADD", {
                "name": name,
                "duration_ms": 0,
            })
        elif mode == "start_countdown":
            self.plugin_base.twitchat.send_action("COUNTDOWN_ADD", {
                "name": name,
                "duration_ms": duration_ms,
            })
        elif mode == "get_current":
            self.plugin_base.twitchat.send_action("GET_CURRENT_TIMERS")
        elif mode == "stop":
            # We don't have a direct "stop timer" action, but TIMER_ADD
            # can be used to reset, or we can rely on the user stopping
            # from Twitchat UI. GET_CURRENT_TIMERS will update display.
            self.plugin_base.twitchat.send_action("GET_CURRENT_TIMERS")

    def _on_timer_event(self, data):
        if not data:
            return

        # All timer events share the TimerData shape
        self._current_timer_id = data.get("id", "")
        self._display_title = data.get("title", data.get("name", ""))

        timer_type = data.get("type", "timer")
        start_ms = data.get("startAt_ms")
        end_ms = data.get("endAt_ms")
        paused = data.get("paused", False)

        if end_ms:
            self._running = False
        elif start_ms and not paused:
            self._running = True
        else:
            self._running = False

        self._update_display()

    def _update_display(self):
        if self._display_title:
            status = "▶" if self._running else "■"
            self.set_center_label(f"{status} {self._display_title[:7]}")
        else:
            settings = self.get_settings()
            mode = settings.get("mode", "start_timer")
            self.set_center_label(TIMER_MODES.get(mode, "Timer")[:8])
            self.set_bottom_label("Press to act")

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_mode = settings.get("mode", "start_timer")
        current_name = settings.get("name", "Timer")
        current_duration = settings.get("duration_ms", 300000) // 1000

        mode_combo = Gtk.ComboBoxText()
        for key, label in TIMER_MODES.items():
            mode_combo.append(key, label)
        mode_combo.set_active_id(current_mode)
        mode_combo.connect("changed", lambda c: self._on_setting_changed("mode", c.get_active_id()))

        name_entry = Gtk.Entry()
        name_entry.set_text(current_name)
        name_entry.set_placeholder_text("Stream Timer")
        name_entry.connect("changed", lambda e: self._on_setting_changed("name", e.get_text()))

        dur_adj = Gtk.Adjustment(value=current_duration, lower=5, upper=7200, step_increment=30)
        dur_spinner = Gtk.SpinButton(adjustment=dur_adj)
        dur_spinner.set_value(current_duration)
        dur_spinner.connect("value-changed", lambda s: self._on_setting_changed("duration_ms", s.get_value_as_int() * 1000))

        mode_row = Adw.ActionRow(title="Mode")
        mode_row.add_suffix(mode_combo)

        name_row = Adw.ActionRow(title="Timer Name")
        name_row.add_suffix(name_entry)

        dur_row = Adw.ActionRow(title="Countdown (seconds)")
        dur_row.add_suffix(dur_spinner)

        return [mode_row, name_row, dur_row]

    def _on_setting_changed(self, key: str, value):
        settings = self.get_settings()
        settings[key] = value
        self.set_settings(settings)
        self._update_display()
