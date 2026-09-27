"""
ClearHighlight — removes the currently displayed message from the chat highlight overlay.
Sends CLEAR_CHAT_HIGHLIGHT with no parameters.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

from ..backend.obs_connection import OBSConnection


class ClearHighlight(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "highlight.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.set_bottom_label("Clear HL")

    def on_key_down(self):
        OBSConnection.get().send_action("CLEAR_CHAT_HIGHLIGHT")
