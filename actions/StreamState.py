"""
StreamState — shows whether OBS is currently streaming.
Subscribes to OBS_STREAM_STATE events relayed by Twitchat.
Green key = live, dark key = offline.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class StreamState(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._live: bool = False

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "record.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("OBS_STREAM_STATE", self._on_stream_state)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("OBS_STREAM_STATE", self._on_stream_state)

    def _on_stream_state(self, data):
        if not data:
            return
        state = data.get("outputState", "")
        self._live = (state == "OBS_WEBSOCKET_OUTPUT_STARTED")
        self._update_display()

    def _update_display(self):
        if self._live:
            self.set_background_color([0, 180, 0, 255])
            self.set_center_label("LIVE")
        else:
            self.set_background_color([40, 40, 40, 255])
            self.set_center_label("OFFLINE")
