"""
RecordState — shows whether OBS is currently recording.
Subscribes to OBS_RECORD_STATE events relayed by Twitchat.
Red dot + "REC" when recording, dark when stopped.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

from ..backend.obs_connection import OBSConnection


class RecordState(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._recording: bool = False

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "record.svg")
        self.set_media(media_path=icon_path, size=0.75)
        OBSConnection.get().add_event_listener("OBS_RECORD_STATE", self._on_record_state)
        self._update_display()

    def on_remove(self):
        OBSConnection.get().remove_event_listener("OBS_RECORD_STATE", self._on_record_state)

    def _on_record_state(self, data):
        if not data:
            return
        state = data.get("outputState", "")
        self._recording = (state == "OBS_WEBSOCKET_OUTPUT_STARTED")
        self._update_display()

    def _update_display(self):
        if self._recording:
            self.set_background_color([180, 0, 0, 255])
            self.set_center_label("REC")
        else:
            self.set_background_color([40, 40, 40, 255])
            self.set_center_label("STOP")
