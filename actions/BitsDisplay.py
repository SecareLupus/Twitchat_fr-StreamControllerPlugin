"""
BitsDisplay — shows the latest cheer (username + bit amount) on a key.
Subscribes to BITS events from Twitchat.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class BitsDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_name: str = ""
        self._latest_bits: int = 0
        self._total_bits: int = 0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("BITS", self._on_bits)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("BITS", self._on_bits)

    def on_key_down(self):
        self._latest_name = ""
        self._latest_bits = 0
        self._total_bits = 0
        self._update_display()

    def _on_bits(self, data):
        if data and "user" in data:
            user = data["user"]
            bits = data.get("bits", 0)
            self._latest_name = user.get("displayName", user.get("login", ""))
            self._latest_bits = bits
            self._total_bits += bits
            self._update_display()

    def _update_display(self):
        if self._latest_name:
            self.set_center_label(f"{self._latest_name[:6]} {self._latest_bits}")
            self.set_bottom_label(f"Total: {self._total_bits}")
        else:
            self.set_center_label("No cheers")
            self.set_bottom_label("yet")
