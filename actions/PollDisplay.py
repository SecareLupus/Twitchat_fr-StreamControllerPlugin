"""
PollDisplay — shows the current Twitch poll status on a key.
Subscribes to POLL_PROGRESS events. Shows poll title and leading choice.
Clears when poll ends (empty data).
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class PollDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title: str = ""
        self._leader: str = ""
        self._leader_votes: int = 0
        self._active: bool = False

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("POLL_PROGRESS", self._on_poll)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("POLL_PROGRESS", self._on_poll)

    def _on_poll(self, data):
        if not data or not data.get("poll"):
            # Poll ended or no poll data
            self._active = False
            self._title = ""
            self._leader = ""
            self._leader_votes = 0
            self._update_display()
            return

        poll = data["poll"]
        self._active = True
        self._title = poll.get("title", "")
        choices = poll.get("choices", [])

        if choices:
            best = max(choices, key=lambda c: c.get("votes", 0))
            self._leader = best.get("label", "")
            self._leader_votes = best.get("votes", 0)

        self._update_display()

    def _update_display(self):
        if self._active and self._title:
            self.set_center_label(self._title[:8])
            self.set_bottom_label(f"{self._leader[:5]} {self._leader_votes}" if self._leader else "")
        else:
            self.set_center_label("No poll")
            self.set_bottom_label("active")
