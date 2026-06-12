"""
Current Track display — shows the currently playing Spotify track name.
Subscribes to CURRENT_TRACK events from Twitchat.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class TrackDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._track_name: str = ""
        self._artist_name: str = ""

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("CURRENT_TRACK", self._on_track)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("CURRENT_TRACK", self._on_track)

    def on_key_down(self):
        # Request current track info
        self.plugin_base.twitchat.send_action("GET_CURRENT_TRACK")

    def _on_track(self, data):
        if data and "trackName" in data:
            self._track_name = data.get("trackName", "")
            self._artist_name = data.get("artistName", "")
            self._update_display()
        else:
            # Playback stopped
            self._track_name = ""
            self._artist_name = ""
            self._update_display()

    def _update_display(self):
        if self._track_name:
            self.set_center_label(self._track_name[:8])
            self.set_bottom_label(self._artist_name[:8] if self._artist_name else "Playing")
        else:
            self.set_center_label("No track")
            self.set_bottom_label("playing")
