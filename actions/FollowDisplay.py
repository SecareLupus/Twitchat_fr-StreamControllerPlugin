"""
Latest Follower display — shows the most recent follower's name on a Stream Deck key.
Subscribes to FOLLOW events from Twitchat.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class FollowDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_follower: str = ""
        self._follow_count: int = 0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("FOLLOW", self._on_follow)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("FOLLOW", self._on_follow)

    def on_key_down(self):
        # Reset on press
        self._latest_follower = ""
        self._follow_count = 0
        self._update_display()

    def _on_follow(self, data):
        if data and "user" in data:
            user = data["user"]
            self._latest_follower = user.get("displayName", user.get("login", ""))
            self._follow_count += 1
            self._update_display()

    def _update_display(self):
        if self._latest_follower:
            self.set_center_label(self._latest_follower[:8])
            self.set_bottom_label(f"Follows: {self._follow_count}")
        else:
            self.set_center_label("No follows")
            self.set_bottom_label("yet")
