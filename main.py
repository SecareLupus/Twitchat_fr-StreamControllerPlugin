"""
StreamController plugin for Twitchat integration.

Connects to OBS WebSocket v5 to send actions and receive events from
the Twitchat public API. Provides 35+ Stream Deck actions for chat
control, moderation, overlays, and live stream monitoring.
"""
from __future__ import annotations

import threading
from typing import Any, List

from loguru import logger

from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from .services import (
    OBSConnectionConfig,
    OBSConnectionManager,
    TwitchatAPI,
)
from .settings import TwitchatSettings

# ── Actions ──────────────────────────────────────────────────────────
from .actions.ChatControl import ChatControl
from .actions.EmergencyToggle import EmergencyToggle
from .actions.ToggleVisibility import ToggleVisibility
from .actions.TriggerExecute import TriggerExecute
from .actions.FollowDisplay import FollowDisplay
from .actions.SubDisplay import SubDisplay
from .actions.TrackDisplay import TrackDisplay
from .actions.SendMessage import SendMessage
from .actions.BitsDisplay import BitsDisplay
from .actions.MentionAlert import MentionAlert
from .actions.RaffleControl import RaffleControl
from .actions.TimerControl import TimerControl
from .actions.CounterControl import CounterControl
from .actions.DonationDisplay import DonationDisplay
from .actions.AutomodAccept import AutomodAccept
from .actions.AutomodReject import AutomodReject
from .actions.TriggerToggle import TriggerToggle
from .actions.StreamState import StreamState
from .actions.RecordState import RecordState
from .actions.RewardDisplay import RewardDisplay
from .actions.ClearHighlight import ClearHighlight
from .actions.StopTTS import StopTTS
from .actions.HideAlert import HideAlert
from .actions.PollDisplay import PollDisplay
from .actions.WhisperNotify import WhisperNotify
from .actions.ChatSelectUp import ChatSelectUp
from .actions.ChatSelectDown import ChatSelectDown
from .actions.ChatSelectCancel import ChatSelectCancel
from .actions.ChatSelectDelete import ChatSelectDelete
from .actions.ChatSelectBan import ChatSelectBan
from .actions.ChatSelectPin import ChatSelectPin
from .actions.ChatSelectHighlight import ChatSelectHighlight
from .actions.ChatSelectShoutout import ChatSelectShoutout
from .actions.ChatColumnUp import ChatColumnUp
from .actions.ChatColumnDown import ChatColumnDown
from .actions.ConnectionStatus import ConnectionStatus


class TwitchatIntegrationPlugin(PluginBase):
    """StreamController plugin entry point for Twitchat integration."""

    def __init__(self) -> None:
        super().__init__(use_legacy_locale=False)

        self.settings = TwitchatSettings.from_dict(self.get_settings())
        self.obs_manager = OBSConnectionManager(self.settings.to_obs_config())
        self.twitchat = TwitchatAPI(self.obs_manager)
        self._connection_listeners: list = []

        # Route raw OBS messages through the Twitchat API for event dispatch
        self.obs_manager.add_raw_handler(self.twitchat.handle_raw_message)

        self.has_plugin_settings = True

        # ── Register all 35 actions ──────────────────────────────────
        self._register_all_actions()

        self.register(
            plugin_name="Twitchat Integration",
            github_repo="https://github.com/SecareLupus/Twitchat_fr-StreamControllerPlugin",
            plugin_version="1.0.0",
            app_version="1.5.0-beta.6",
        )

        self._persist_settings()
        self._connect_in_background()

    # ------------------------------------------------------------------
    # Public API for actions
    # ------------------------------------------------------------------
    def broadcast(self, action: str, payload: dict | None = None) -> bool:
        """Send a Twitchat action. Convenience wrapper for actions."""
        return self.twitchat.send_action(action, payload)

    def add_connection_listener(self, callback) -> None:
        """Register for connection state changes. callback(connected: bool)."""
        self._connection_listeners.append(callback)

    def remove_connection_listener(self, callback) -> None:
        try:
            self._connection_listeners.remove(callback)
        except ValueError:
            pass

    def reconnect(self) -> None:
        """Public method to trigger a manual reconnection."""
        self._connect_in_background()

    @property
    def chat_column(self) -> int:
        """The Twitchat chat column index to target (0-based)."""
        return self.settings.chat_column

    # ------------------------------------------------------------------
    # Plugin lifecycle
    # ------------------------------------------------------------------
    def on_disconnect(self, conn) -> None:
        try:
            self.obs_manager.disconnect()
        finally:
            super().on_disconnect(conn)

    # ------------------------------------------------------------------
    # Settings UI
    # ------------------------------------------------------------------
    def get_config_rows(self) -> list[Adw.PreferencesRow]:
        rows: list[Adw.PreferencesRow] = []

        host_row = Adw.EntryRow()
        host_row.set_title("OBS Host")
        host_row.set_text(self.settings.host)
        host_row.connect("changed", self._on_host_changed)
        rows.append(host_row)

        port_row = Adw.EntryRow()
        port_row.set_title("Port")
        port_row.set_input_purpose(Gtk.InputPurpose.DIGITS)
        port_row.set_text(str(self.settings.port))
        port_row.connect("changed", self._on_port_changed)
        rows.append(port_row)

        password_row = Adw.PasswordEntryRow()
        password_row.set_title("Password")
        password_row.set_text(self.settings.password)
        password_row.connect("changed", self._on_password_changed)
        rows.append(password_row)

        col_row = Adw.ComboRow(title="Chat Column")
        col_model = Gtk.StringList()
        for i in range(8):
            col_model.append(f"Column {i}")
        col_row.set_model(col_model)
        col_row.set_selected(self.settings.chat_column)
        col_row.connect("notify::selected", lambda r, _: self._on_chat_column_changed(r.get_selected()))
        rows.append(col_row)

        return rows

    def get_settings_area(self) -> Adw.PreferencesGroup:
        from GtkHelper.GtkHelper import BetterPreferencesGroup

        group = BetterPreferencesGroup(title="OBS Connection")
        for row in self.get_config_rows():
            group.add(row)

        # Status label
        status_row = Adw.ActionRow(title="Status")
        status_label = Gtk.Label(
            label="Connected" if self.obs_manager.is_connected() else "Disconnected",
            xalign=1,
        )
        self.add_connection_listener(
            lambda connected: status_label.set_text(
                "Connected" if connected else "Disconnected"
            )
        )
        status_row.add_suffix(status_label)
        group.add(status_row)

        # Reconnect button
        reconnect_row = Adw.ActionRow(title="Reconnect")
        reconnect_btn = Gtk.Button(label="Reconnect Now")
        reconnect_btn.connect("clicked", lambda b: self._connect_in_background())
        reconnect_row.add_suffix(reconnect_btn)
        group.add(reconnect_row)

        return group

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------
    def _persist_settings(self) -> None:
        self.set_settings(self.settings.to_dict())

    def _update_settings(self, **changes: Any) -> None:
        new_settings = self.settings.update(**changes)
        if new_settings == self.settings:
            return

        logger.info("Updating Twitchat plugin settings: {}", changes)
        self.settings = new_settings
        self.obs_manager.update_config(
            host=self.settings.host,
            port=self.settings.port,
            password=self.settings.password,
        )
        self._persist_settings()

        if not self.obs_manager.is_connected():
            self._connect_in_background()

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------
    def _on_host_changed(self, row: Adw.EntryRow) -> None:
        self._update_settings(host=row.get_text())

    def _on_port_changed(self, row: Adw.EntryRow) -> None:
        text = row.get_text().strip()
        if not text:
            return
        try:
            port = int(text)
        except ValueError:
            logger.warning("Invalid OBS port entered: {}", text)
            return
        self._update_settings(port=port)

    def _on_password_changed(self, row: Adw.PasswordEntryRow) -> None:
        self._update_settings(password=row.get_text())

    def _on_chat_column_changed(self, column: int) -> None:
        self._update_settings(chat_column=column)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def _connect_in_background(self) -> None:
        def worker() -> None:
            try:
                self.obs_manager.ensure_connection()
                connected = self.obs_manager.is_connected()
                self._notify_connection(connected)
            except Exception as exc:
                logger.warning("OBS connection attempt failed: {}", exc)
                self._notify_connection(False)

        t = threading.Thread(target=worker, name="twitchat-obs-connect", daemon=True)
        t.start()

    def _notify_connection(self, connected: bool) -> None:
        for cb in self._connection_listeners:
            try:
                cb(connected)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Action registration
    # ------------------------------------------------------------------
    def _register_all_actions(self) -> None:
        self._ah("Chat Control", ChatControl, "ChatControl")
        self._ah("Emergency Toggle", EmergencyToggle, "EmergencyToggle")
        self._ah("Toggle Panel Visibility", ToggleVisibility, "ToggleVisibility")
        self._ah("Execute Trigger", TriggerExecute, "TriggerExecute")
        self._ah("Latest Follower", FollowDisplay, "FollowDisplay")
        self._ah("Latest Subscriber", SubDisplay, "SubDisplay")
        self._ah("Current Track", TrackDisplay, "TrackDisplay")
        self._ah("Send Chat Message", SendMessage, "SendMessage")
        self._ah("Latest Cheer", BitsDisplay, "BitsDisplay")
        self._ah("Mention Alert", MentionAlert, "MentionAlert")
        self._ah("Raffle Control", RaffleControl, "RaffleControl")
        self._ah("Timer / Countdown", TimerControl, "TimerControl")
        self._ah("Counter Control", CounterControl, "CounterControl")
        self._ah("Latest Donation", DonationDisplay, "DonationDisplay")
        self._ah("AutoMod Accept", AutomodAccept, "AutomodAccept")
        self._ah("AutoMod Reject", AutomodReject, "AutomodReject")
        self._ah("Toggle Trigger", TriggerToggle, "TriggerToggle")
        self._ah("Stream Status", StreamState, "StreamState")
        self._ah("Record Status", RecordState, "RecordState")
        self._ah("Latest Reward", RewardDisplay, "RewardDisplay")
        self._ah("Clear Highlight", ClearHighlight, "ClearHighlight")
        self._ah("Stop TTS", StopTTS, "StopTTS")
        self._ah("Hide Alert", HideAlert, "HideAlert")
        self._ah("Poll Status", PollDisplay, "PollDisplay")
        self._ah("Whisper Count", WhisperNotify, "WhisperNotify")
        self._ah("Chat: Previous Message", ChatSelectUp, "ChatSelectUp")
        self._ah("Chat: Next Message", ChatSelectDown, "ChatSelectDown")
        self._ah("Chat: Cancel Selection", ChatSelectCancel, "ChatSelectCancel")
        self._ah("Chat: Delete Message", ChatSelectDelete, "ChatSelectDelete")
        self._ah("Chat: Ban User", ChatSelectBan, "ChatSelectBan")
        self._ah("Chat: Pin Message", ChatSelectPin, "ChatSelectPin")
        self._ah("Chat: Highlight Message", ChatSelectHighlight, "ChatSelectHighlight")
        self._ah("Chat: Shoutout User", ChatSelectShoutout, "ChatSelectShoutout")
        self._ah("Chat: Next Column", ChatColumnUp, "ChatColumnUp")
        self._ah("Chat: Previous Column", ChatColumnDown, "ChatColumnDown")
        self._ah("Connection Status", ConnectionStatus, "ConnectionStatus")

    def _ah(self, name: str, action_cls, action_id: str) -> None:
        holder = ActionHolder(
            plugin_base=self,
            action_base=action_cls,
            action_id=f"com_secarelupus_twitchatintegration::{action_id}",
            action_name=f"Twitchat: {name}",
        )
        self.add_action_holder(holder)
