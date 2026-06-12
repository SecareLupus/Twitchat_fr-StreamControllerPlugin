"""
ChatSelectUp — moves the message selection cursor up (to older messages).
Sends CHAT_FEED_SELECT with count=-1. Use in combination with the
SELECT_ACTION_* buttons to moderate messages from your Stream Deck.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class ChatSelectUp(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "chat.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.set_bottom_label("Prev Msg")

    def on_key_down(self):
        col = self.plugin_base.chat_column
        self.plugin_base.twitchat.send_action("CHAT_FEED_SELECT", {"count": -1, "col": col})
