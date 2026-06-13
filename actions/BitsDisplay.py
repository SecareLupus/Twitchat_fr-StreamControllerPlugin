"""
BitsDisplay — shows the latest cheer username + bit amount and total.
Requests GET_SUMMARY_DATA on startup for current state.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase


class BitsDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_name: str = ""
        self._latest_amount: int = 0
        self._total_bits: int = 0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("BITS", self._on_bits)
        self.plugin_base.twitchat.add_listener("SUMMARY_DATA", self._on_summary)
        self._request_data()
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("BITS", self._on_bits)
        self.plugin_base.twitchat.remove_listener("SUMMARY_DATA", self._on_summary)

    def on_key_down(self):
        self._request_data()

    def _request_data(self):
        self.plugin_base.twitchat.send_action("GET_SUMMARY_DATA")

    def _on_summary(self, data):
        if not data:
            return
        bits = data.get("bits", [])
        if bits:
            latest = bits[-1]
            self._latest_name = latest.get("login", "")
            self._latest_amount = latest.get("bits", 0)
            self._total_bits = sum(b.get("bits", 0) for b in bits)
            self._update_display()

    def _on_bits(self, data):
        if data and "user" in data:
            user = data["user"]
            self._latest_name = user.get("displayName", user.get("login", ""))
            amount = data.get("amount", 0)
            self._latest_amount = amount
            self._total_bits += amount
            self._update_display()

    def _update_display(self):
        if self._latest_name:
            self.set_center_label(self._latest_name[:6])
            self.set_bottom_label(f"{self._latest_amount} bits")
        else:
            self.set_center_label("No cheers")
            self.set_bottom_label("yet")
