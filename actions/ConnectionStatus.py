"""
ConnectionStatus — shows whether the plugin is connected to OBS/Twitchat.
Green = connected, red = disconnected. Press to reconnect.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class ConnectionStatus(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connected: bool = False

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "record.svg")
        self.set_media(media_path=icon_path, size=0.75)
        conn = self.plugin_base
        self._connected = conn.obs_manager.is_connected()
        conn.add_connection_listener(self._on_connection_change)
        self._update_display()

    def on_remove(self):
        self.plugin_base.remove_connection_listener(self._on_connection_change)

    def on_key_down(self):
        self.plugin_base.reconnect()

    def _on_connection_change(self, connected: bool):
        self._connected = connected
        self._update_display()

    def _update_display(self):
        if self._connected:
            self.set_background_color([0, 180, 0, 255])
            self.set_center_label("OK")
        else:
            self.set_background_color([180, 0, 0, 255])
            self.set_center_label("OFF")
