"""
ChatSelectHighlight — sends the currently selected message to the chat highlight overlay.
Sends CHAT_FEED_SELECT_ACTION_HIGHLIGHT.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class ChatSelectHighlight(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "highlight.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.set_bottom_label("Highlight")

    def on_key_down(self):
        self.plugin_base.twitchat.send_action("CHAT_FEED_SELECT_ACTION_HIGHLIGHT")
