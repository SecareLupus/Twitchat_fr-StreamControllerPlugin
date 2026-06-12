"""
AutoMod Accept — accepts the most recent automod-held chat message.
Sends AUTOMOD_ACCEPT with no parameters. Twitchat scans the last 1000
messages for the latest held message and allows it through.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class AutomodAccept(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "check.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.set_bottom_label("Accept")

    def on_key_down(self):
        self.plugin_base.twitchat.send_action("AUTOMOD_ACCEPT")
