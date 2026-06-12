"""
ChatColumnDown — decrements the chat column index at runtime.
Pairs with ChatColumnUp for navigating multi-column Twitchat layouts.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase


class ChatColumnDown(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "chat.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self._update_display()

    def on_key_down(self):
        settings = self.plugin_base.settings
        new_col = max(settings.chat_column - 1, 0)
        self.plugin_base._update_settings(chat_column=new_col)
        self._update_display()

    def _update_display(self):
        col = self.plugin_base.chat_column
        self.set_center_label(f"Col {col}")
        self.set_bottom_label("Prev Col")
