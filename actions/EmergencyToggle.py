"""
Emergency Toggle action — toggles Twitchat emergency mode on/off.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class EmergencyToggle(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._emergency_active = False

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "alert.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self._update_icon()
        # Subscribe to emergency mode events to keep state in sync
        self.plugin_base.twitchat.add_listener("EMERGENCY_MODE", self._on_emergency_event)

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("EMERGENCY_MODE", self._on_emergency_event)

    def on_key_down(self):
        # Send SET_EMERGENCY_MODE without data to toggle
        self.plugin_base.twitchat.send_action("SET_EMERGENCY_MODE")
        self._emergency_active = not self._emergency_active
        self._update_icon()

    def _on_emergency_event(self, data):
        if data and "enabled" in data:
            self._emergency_active = data["enabled"]
            self._update_icon()

    def _update_icon(self):
        if self._emergency_active:
            self.set_background_color([255, 0, 0, 255])
            self.set_bottom_label("STOP")
        else:
            self.set_background_color([0, 100, 0, 255])
            self.set_bottom_label("START")
