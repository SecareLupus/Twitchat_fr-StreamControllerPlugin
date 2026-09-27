"""
ChatSelectBan — bans the author of the currently selected message.
Sends CHAT_FEED_SELECT_ACTION_BAN.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

from ..backend.obs_connection import OBSConnection


class ChatSelectBan(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "cross.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.set_bottom_label("Ban")

    def on_key_down(self):
        OBSConnection.get().send_action("CHAT_FEED_SELECT_ACTION_BAN")
