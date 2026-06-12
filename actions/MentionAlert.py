"""
MentionAlert — alerts when someone @mentions you in chat.
Flashes the key red briefly on MENTION events, shows the mentioner's name.
"""
import os
import threading
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page



class MentionAlert(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_mention: str = ""
        self._mention_count: int = 0
        self._flash_lock = threading.Lock()
        self._flashing: bool = False

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "alert.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("MENTION", self._on_mention)
        self.set_background_color([0, 100, 0, 255])
        self.set_center_label("No @mentions")
        self.set_bottom_label("")

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("MENTION", self._on_mention)

    def on_key_down(self):
        self._last_mention = ""
        self._mention_count = 0
        self._flashing = False
        self.set_background_color([0, 100, 0, 255])
        self.set_center_label("No @mentions")
        self.set_bottom_label("")

    def _on_mention(self, data):
        if data and "user" in data:
            user = data["user"]
            self._last_mention = user.get("displayName", user.get("login", ""))
            self._mention_count += 1
            self._update_display()
            self._trigger_flash()

    def _update_display(self):
        self.set_center_label(f"@{self._last_mention[:8]}")
        self.set_bottom_label(f"Mentions: {self._mention_count}")

    def _trigger_flash(self):
        with self._flash_lock:
            if self._flashing:
                return
            self._flashing = True

        # Flash red 3 times over ~1.5 seconds
        for i in range(3):
            self.set_background_color([200, 30, 30, 255])
            threading.Event().wait(0.25)
            self.set_background_color([0, 100, 0, 255])
            threading.Event().wait(0.25)

        with self._flash_lock:
            self._flashing = False
