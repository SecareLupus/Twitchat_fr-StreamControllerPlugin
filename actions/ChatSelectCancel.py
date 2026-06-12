"""
ChatSelectCancel — deselects the currently selected message.
Sends CHAT_FEED_SELECT_ACTION_CANCEL.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class ChatSelectCancel(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "chat.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.set_bottom_label("Cancel")

    def on_key_down(self):
        self.plugin_base.twitchat.send_action("CHAT_FEED_SELECT_ACTION_CANCEL")
