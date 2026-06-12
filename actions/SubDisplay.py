"""
SubDisplay — shows the latest subscriber tier, name, and count.
Requests GET_SUMMARY_DATA on startup for current state.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase


class SubDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_name: str = ""
        self._tier: str = ""
        self._total_count: int = 0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("SUBSCRIPTION", self._on_sub)
        self.plugin_base.twitchat.add_listener("SUMMARY_DATA", self._on_summary)
        self._request_data()
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("SUBSCRIPTION", self._on_sub)
        self.plugin_base.twitchat.remove_listener("SUMMARY_DATA", self._on_summary)

    def on_key_down(self):
        self._request_data()

    def _request_data(self):
        self.plugin_base.twitchat.send_action("GET_SUMMARY_DATA")

    def _on_summary(self, data):
        if not data:
            return
        subs = data.get("subs", [])
        resubs = data.get("resubs", [])
        all_subs = subs + resubs
        if all_subs:
            latest = all_subs[-1]
            self._latest_name = latest.get("login", "")
            self._tier = str(latest.get("tier", ""))
            self._total_count = len(data.get("subs", [])) + len(data.get("resubs", [])) + len(data.get("subgifts", []))
            self._update_display()

    def _on_sub(self, data):
        if data and "user" in data:
            user = data["user"]
            self._latest_name = user.get("displayName", user.get("login", ""))
            self._tier = str(data.get("tier", ""))
            self._total_count += 1
            self._update_display()

    def _update_display(self):
        if self._latest_name:
            label = f"T{self._tier}" if self._tier else "Sub"
            self.set_center_label(self._latest_name[:6])
            self.set_bottom_label(f"{label} {self._total_count}")
        else:
            self.set_center_label("No subs")
            self.set_bottom_label("yet")
