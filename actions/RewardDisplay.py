"""
RewardDisplay — shows the latest channel points reward redemption.
Requests GET_SUMMARY_DATA on startup for current state.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase


class RewardDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reward_title: str = ""
        self._user_name: str = ""

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("REWARD_REDEEM", self._on_reward)
        self.plugin_base.twitchat.add_listener("SUMMARY_DATA", self._on_summary)
        self._request_data()
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("REWARD_REDEEM", self._on_reward)
        self.plugin_base.twitchat.remove_listener("SUMMARY_DATA", self._on_summary)

    def on_key_down(self):
        self._request_data()

    def _request_data(self):
        self.plugin_base.twitchat.send_action("GET_SUMMARY_DATA")

    def _on_summary(self, data):
        if not data:
            return
        rewards = data.get("rewards", [])
        if rewards:
            latest = rewards[-1]
            self._reward_title = latest.get("title", "")
            self._user_name = latest.get("login", "")
            self._update_display()

    def _on_reward(self, data):
        if data and "reward" in data:
            reward = data["reward"]
            user = data.get("user", {})
            self._reward_title = reward.get("title", "")
            self._user_name = user.get("displayName", user.get("login", ""))
            self._update_display()

    def _update_display(self):
        if self._reward_title:
            self.set_center_label(self._reward_title[:8])
            self.set_bottom_label(self._user_name[:7])
        else:
            self.set_center_label("No rewards")
            self.set_bottom_label("yet")
