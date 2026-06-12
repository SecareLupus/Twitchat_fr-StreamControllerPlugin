"""
Toggle Visibility action — toggles Twitchat panel visibility (polls, predictions, bingo, etc.).
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw



TOGGLE_TARGETS = {
    "poll": {"label": "Poll", "action": "POLL_TOGGLE"},
    "prediction": {"label": "Prediction", "action": "PREDICTION_TOGGLE"},
    "bingo": {"label": "Bingo", "action": "BINGO_TOGGLE"},
    "raffle": {"label": "Raffle", "action": "RAFFLE_TOGGLE"},
    "viewers": {"label": "Viewer Count", "action": "VIEWERS_COUNT_TOGGLE"},
    "modtools": {"label": "Mod Tools", "action": "MOD_TOOLS_TOGGLE"},
    "censor": {"label": "Censor Deleted", "action": "CENSOR_DELETED_MESSAGES_TOGGLE"},
    "merge": {"label": "Merge Panels", "action": "MERGE_TOGGLE"},
}


class ToggleVisibility(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "toggle.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self._update_icon()

    def on_key_down(self):
        settings = self.get_settings()
        target_key = settings.get("target", "poll")
        target = TOGGLE_TARGETS.get(target_key, TOGGLE_TARGETS["poll"])
        self.plugin_base.twitchat.send_action(target["action"])
        self._update_icon()

    def _update_icon(self):
        settings = self.get_settings()
        target_key = settings.get("target", "poll")
        target = TOGGLE_TARGETS.get(target_key, TOGGLE_TARGETS["poll"])
        self.set_bottom_label(target["label"][:8])

    def get_config_rows(self) -> list:
        settings = self.get_settings()
        current_target = settings.get("target", "poll")

        combo = Gtk.ComboBoxText()
        for key, target in TOGGLE_TARGETS.items():
            combo.append(key, target["label"])
        combo.set_active_id(current_target)
        combo.connect("changed", lambda c: self._on_target_changed(c.get_active_id()))

        row = Adw.ActionRow(title="Toggle Target")
        row.add_suffix(combo)

        return [row]

    def _on_target_changed(self, key: str):
        settings = self.get_settings()
        settings["target"] = key
        self.set_settings(settings)
        self._update_icon()
