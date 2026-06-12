"""
DonationDisplay — shows the latest donation/tip on a key.
Subscribes to DONATION_EVENT events from Twitchat.
"""
import os
from src.backend.PluginManager.ActionBase import ActionBase



class DonationDisplay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._latest_donor: str = ""
        self._latest_amount: str = ""
        self._total_amount: float = 0.0

    def on_ready(self):
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "display.svg")
        self.set_media(media_path=icon_path, size=0.75)
        self.plugin_base.twitchat.add_listener("DONATION_EVENT", self._on_donation)
        self._update_display()

    def on_remove(self):
        self.plugin_base.twitchat.remove_listener("DONATION_EVENT", self._on_donation)

    def on_key_down(self):
        self._latest_donor = ""
        self._latest_amount = ""
        self._total_amount = 0.0
        self._update_display()

    def _on_donation(self, data):
        if data:
            self._latest_donor = data.get("username", "")
            self._latest_amount = data.get("amount", "0")
            try:
                self._total_amount += float(self._latest_amount)
            except ValueError:
                pass
            self._update_display()

    def _update_display(self):
        if self._latest_donor:
            amount_str = f"${self._latest_amount}"
            self.set_center_label(f"{self._latest_donor[:6]}")
            self.set_bottom_label(amount_str[:8])
        else:
            self.set_center_label("No tips")
            self.set_bottom_label("yet")
