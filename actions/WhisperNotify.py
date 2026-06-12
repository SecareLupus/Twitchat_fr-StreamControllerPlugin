"""
WhisperNotify — shows the number of unread whispers.
Subscribes to MESSAGE_WHISPER events. Displays count on the key.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class WhisperNotify(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unread: int = 0
        self._last_sender: str = ""

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("MESSAGE_WHISPER", self._on_whisper)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("MESSAGE_WHISPER", self._on_whisper)

    def on_key_down(self):
        # Mark all whispers read
        self.plugin_base.twitchat.send_action("GREET_FEED_READ_ALL")
        self._unread = 0
        self._last_sender = ""
        self._update_display()

    def _on_whisper(self, data):
        if data:
            self._unread = data.get("unreadCount", self._unread)
            user = data.get("user", {})
            self._last_sender = user.get("displayName", user.get("login", ""))
            self._update_display()

    def _update_display(self):
        if self._unread > 0:
            self.set_center_label(str(self._unread))
            self.set_bottom_label(f"Whispers")
            self.set_background_color([100, 0, 180, 255])
        else:
            self.set_background_color([40, 40, 40, 255])
            self.set_center_label("0")
            self.set_bottom_label("Whispers")
