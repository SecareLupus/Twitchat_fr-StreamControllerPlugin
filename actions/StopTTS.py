"""
StopTTS — immediately stops any text-to-speech audio playing in Twitchat.
Sends STOP_TTS with no parameters. Panic button for rogue TTS.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class StopTTS(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "alert.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.set_bottom_label("Stop TTS")

    def on_key_down(self):
        self.plugin_base.twitchat.send_action("STOP_TTS")
