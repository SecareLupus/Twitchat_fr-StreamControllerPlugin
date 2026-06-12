"""
DonationDisplay — shows the latest tip donor + amount.
Requests GET_SUMMARY_DATA on startup for current state.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase


class DonationDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_donor: str = ""
        self._latest_amount: str = ""

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("DONATION_EVENT", self._on_donation)
        self.plugin_base.twitchat.add_listener("SUMMARY_DATA", self._on_summary)
        self._request_data()
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("DONATION_EVENT", self._on_donation)
        self.plugin_base.twitchat.remove_listener("SUMMARY_DATA", self._on_summary)

    def on_key_down(self):
        self._request_data()

    def _request_data(self):
        self.plugin_base.twitchat.send_action("GET_SUMMARY_DATA")

    def _on_summary(self, data):
        if not data:
            return
        tips = data.get("tips", [])
        if tips:
            latest = tips[-1]
            self._latest_donor = latest.get("login", "")
            self._latest_amount = str(latest.get("amount", ""))
            self._update_display()

    def _on_donation(self, data):
        if data:
            self._latest_donor = data.get("username", "")
            self._latest_amount = str(data.get("amount", ""))
            self._update_display()

    def _update_display(self):
        if self._latest_donor:
            self.set_center_label(self._latest_donor[:6])
            self.set_bottom_label(f"${self._latest_amount}")
        else:
            self.set_center_label("No tips")
            self.set_bottom_label("yet")
