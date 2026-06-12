"""
RewardDisplay — shows the latest channel points reward redemption.
Subscribes to REWARD_REDEEM events. Displays reward title and redeemer name.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class RewardDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reward_title: str = ""
        self._user_name: str = ""
        self._redeem_count: int = 0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("REWARD_REDEEM", self._on_reward)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("REWARD_REDEEM", self._on_reward)

    def on_key_down(self):
        self._reward_title = ""
        self._user_name = ""
        self._redeem_count = 0
        self._update_display()

    def _on_reward(self, data):
        if data and "reward" in data:
            reward = data["reward"]
            user = data.get("user", {})
            self._reward_title = reward.get("title", "")
            self._user_name = user.get("displayName", user.get("login", ""))
            self._redeem_count += 1
            self._update_display()

    def _update_display(self):
        if self._reward_title:
            cost = ""
            self.set_center_label(self._reward_title[:8])
            self.set_bottom_label(f"{self._user_name[:6]} x{self._redeem_count}")
        else:
            self.set_center_label("No rewards")
            self.set_bottom_label("yet")
