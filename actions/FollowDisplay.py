"""
FollowDisplay — shows the latest follower name and cumulative count.
Requests GET_SUMMARY_DATA on startup for current state, then listens
for live FOLLOW events to keep the display current.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase


class FollowDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_name: str = ""
        self._total_count: int = 0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("FOLLOW", self._on_follow)
        self.plugin_base.twitchat.add_listener("SUMMARY_DATA", self._on_summary)
        self._request_data()
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("FOLLOW", self._on_follow)
        self.plugin_base.twitchat.remove_listener("SUMMARY_DATA", self._on_summary)

    def on_key_down(self):
        self._request_data()

    def _request_data(self):
        print(f"[FollowDisplay] Requesting GET_SUMMARY_DATA (connected={self.plugin_base.obs_manager.is_connected()})")
        self.plugin_base.twitchat.send_action("GET_SUMMARY_DATA")

    def _on_summary(self, data):
        print(f"[FollowDisplay] _on_summary called, data keys: {list(data.keys()) if data else 'NONE'}")
        if not data:
            return
        follows = data.get("follows", [])
        print(f"[FollowDisplay] follows count: {len(follows)}")
        if follows:
            latest = follows[-1]
            self._latest_name = latest.get("login", "")
            self._total_count = len(follows)
            self._update_display()

    def _on_follow(self, data):
        if data and "user" in data:
            user = data["user"]
            self._latest_name = user.get("displayName", user.get("login", ""))
            self._total_count += 1
            self._update_display()

    def _update_display(self):
        if self._latest_name:
            self.set_center_label(self._latest_name[:8])
            self.set_bottom_label(str(self._total_count) if self._total_count else "")
        else:
            self.set_center_label("No followers")
            self.set_bottom_label("yet")
