"""
Latest Subscriber display — shows the most recent subscriber's name and tier.
Subscribes to SUBSCRIPTION events from Twitchat.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



TIER_LABELS = {
    "1000": "T1",
    "2000": "T2",
    "3000": "T3",
    "Prime": "Prime",
}


class SubDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_sub: str = ""
        self._latest_tier: str = ""
        self._sub_count: int = 0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("SUBSCRIPTION", self._on_subscription)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("SUBSCRIPTION", self._on_subscription)

    def on_key_down(self):
        self._latest_sub = ""
        self._latest_tier = ""
        self._sub_count = 0
        self._update_display()

    def _on_subscription(self, data):
        if data and "user" in data:
            user = data["user"]
            tier = data.get("tier", "")
            self._latest_sub = user.get("login", "")
            self._latest_tier = TIER_LABELS.get(tier, tier)
            self._sub_count += 1
            self._update_display()

    def _update_display(self):
        if self._latest_sub:
            self.set_center_label(f"{self._latest_tier} {self._latest_sub}"[:8])
            self.set_bottom_label(f"Subs: {self._sub_count}")
        else:
            self.set_center_label("No subs")
            self.set_bottom_label("yet")
