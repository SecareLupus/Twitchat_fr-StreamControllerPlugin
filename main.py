"""
Twitchat StreamController Plugin

Connects to OBS Websocket v5 to send actions and receive events from Twitchat.
Provides Stream Deck actions for common Twitchat controls.
"""
import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

from .actions.ChatControl import ChatControl
from .actions.EmergencyToggle import EmergencyToggle
from .actions.ToggleVisibility import ToggleVisibility
from .actions.TriggerExecute import TriggerExecute
from .actions.FollowDisplay import FollowDisplay
from .actions.SubDisplay import SubDisplay
from .actions.TrackDisplay import TrackDisplay
from .actions.Shoutout import Shoutout
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
from .actions.ConnectionStatus import ConnectionStatus

from .backend.obs_connection import OBSConnection


class TwitchatPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.obs_connection = OBSConnection.get()
        self.has_plugin_settings = True

        # Chat feed control actions
        self.chat_control_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatControl,
            action_id="com_secarelupus_twitchatintegration::ChatControl",
            action_name="Chat Control",
        )
        self.add_action_holder(self.chat_control_holder)

        # Emergency toggle
        self.emergency_toggle_holder = ActionHolder(
            plugin_base=self,
            action_base=EmergencyToggle,
            action_id="com_secarelupus_twitchatintegration::EmergencyToggle",
            action_name="Emergency Toggle",
        )
        self.add_action_holder(self.emergency_toggle_holder)

        # Visibility toggles (poll, prediction, bingo, etc.)
        self.toggle_visibility_holder = ActionHolder(
            plugin_base=self,
            action_base=ToggleVisibility,
            action_id="com_secarelupus_twitchatintegration::ToggleVisibility",
            action_name="Toggle Panel Visibility",
        )
        self.add_action_holder(self.toggle_visibility_holder)

        # Trigger execution
        self.trigger_execute_holder = ActionHolder(
            plugin_base=self,
            action_base=TriggerExecute,
            action_id="com_secarelupus_twitchatintegration::TriggerExecute",
            action_name="Execute Trigger",
        )
        self.add_action_holder(self.trigger_execute_holder)

        # Event display actions
        self.follow_display_holder = ActionHolder(
            plugin_base=self,
            action_base=FollowDisplay,
            action_id="com_secarelupus_twitchatintegration::FollowDisplay",
            action_name="Latest Follower",
        )
        self.add_action_holder(self.follow_display_holder)

        self.sub_display_holder = ActionHolder(
            plugin_base=self,
            action_base=SubDisplay,
            action_id="com_secarelupus_twitchatintegration::SubDisplay",
            action_name="Latest Subscriber",
        )
        self.add_action_holder(self.sub_display_holder)

        self.track_display_holder = ActionHolder(
            plugin_base=self,
            action_base=TrackDisplay,
            action_id="com_secarelupus_twitchatintegration::TrackDisplay",
            action_name="Current Track",
        )
        self.add_action_holder(self.track_display_holder)

        # Priority 1 — high-value adds
        self.shoutout_holder = ActionHolder(
            plugin_base=self,
            action_base=Shoutout,
            action_id="com_secarelupus_twitchatintegration::Shoutout",
            action_name="Shoutout",
        )
        self.add_action_holder(self.shoutout_holder)

        self.send_message_holder = ActionHolder(
            plugin_base=self,
            action_base=SendMessage,
            action_id="com_secarelupus_twitchatintegration::SendMessage",
            action_name="Send Chat Message",
        )
        self.add_action_holder(self.send_message_holder)

        self.bits_display_holder = ActionHolder(
            plugin_base=self,
            action_base=BitsDisplay,
            action_id="com_secarelupus_twitchatintegration::BitsDisplay",
            action_name="Latest Cheer",
        )
        self.add_action_holder(self.bits_display_holder)

        self.mention_alert_holder = ActionHolder(
            plugin_base=self,
            action_base=MentionAlert,
            action_id="com_secarelupus_twitchatintegration::MentionAlert",
            action_name="Mention Alert",
        )
        self.add_action_holder(self.mention_alert_holder)

        # Priority 2 — grouped systems
        self.raffle_control_holder = ActionHolder(
            plugin_base=self,
            action_base=RaffleControl,
            action_id="com_secarelupus_twitchatintegration::RaffleControl",
            action_name="Raffle Control",
        )
        self.add_action_holder(self.raffle_control_holder)

        self.timer_control_holder = ActionHolder(
            plugin_base=self,
            action_base=TimerControl,
            action_id="com_secarelupus_twitchatintegration::TimerControl",
            action_name="Timer / Countdown",
        )
        self.add_action_holder(self.timer_control_holder)

        self.counter_control_holder = ActionHolder(
            plugin_base=self,
            action_base=CounterControl,
            action_id="com_secarelupus_twitchatintegration::CounterControl",
            action_name="Counter Control",
        )
        self.add_action_holder(self.counter_control_holder)

        self.donation_display_holder = ActionHolder(
            plugin_base=self,
            action_base=DonationDisplay,
            action_id="com_secarelupus_twitchatintegration::DonationDisplay",
            action_name="Latest Donation",
        )
        self.add_action_holder(self.donation_display_holder)

        # AutoMod
        self.automod_accept_holder = ActionHolder(
            plugin_base=self,
            action_base=AutomodAccept,
            action_id="com_secarelupus_twitchatintegration::AutomodAccept",
            action_name="AutoMod Accept",
        )
        self.add_action_holder(self.automod_accept_holder)

        self.automod_reject_holder = ActionHolder(
            plugin_base=self,
            action_base=AutomodReject,
            action_id="com_secarelupus_twitchatintegration::AutomodReject",
            action_name="AutoMod Reject",
        )
        self.add_action_holder(self.automod_reject_holder)

        # Priority 3 — nice-to-have
        self.trigger_toggle_holder = ActionHolder(
            plugin_base=self,
            action_base=TriggerToggle,
            action_id="com_secarelupus_twitchatintegration::TriggerToggle",
            action_name="Toggle Trigger",
        )
        self.add_action_holder(self.trigger_toggle_holder)

        self.stream_state_holder = ActionHolder(
            plugin_base=self,
            action_base=StreamState,
            action_id="com_secarelupus_twitchatintegration::StreamState",
            action_name="Stream Status",
        )
        self.add_action_holder(self.stream_state_holder)

        self.record_state_holder = ActionHolder(
            plugin_base=self,
            action_base=RecordState,
            action_id="com_secarelupus_twitchatintegration::RecordState",
            action_name="Record Status",
        )
        self.add_action_holder(self.record_state_holder)

        self.reward_display_holder = ActionHolder(
            plugin_base=self,
            action_base=RewardDisplay,
            action_id="com_secarelupus_twitchatintegration::RewardDisplay",
            action_name="Latest Reward",
        )
        self.add_action_holder(self.reward_display_holder)

        self.clear_highlight_holder = ActionHolder(
            plugin_base=self,
            action_base=ClearHighlight,
            action_id="com_secarelupus_twitchatintegration::ClearHighlight",
            action_name="Clear Highlight",
        )
        self.add_action_holder(self.clear_highlight_holder)

        # Priority 4 — panic buttons / niche
        self.stop_tts_holder = ActionHolder(
            plugin_base=self,
            action_base=StopTTS,
            action_id="com_secarelupus_twitchatintegration::StopTTS",
            action_name="Stop TTS",
        )
        self.add_action_holder(self.stop_tts_holder)

        self.hide_alert_holder = ActionHolder(
            plugin_base=self,
            action_base=HideAlert,
            action_id="com_secarelupus_twitchatintegration::HideAlert",
            action_name="Hide Alert",
        )
        self.add_action_holder(self.hide_alert_holder)

        self.poll_display_holder = ActionHolder(
            plugin_base=self,
            action_base=PollDisplay,
            action_id="com_secarelupus_twitchatintegration::PollDisplay",
            action_name="Poll Status",
        )
        self.add_action_holder(self.poll_display_holder)

        self.whisper_notify_holder = ActionHolder(
            plugin_base=self,
            action_base=WhisperNotify,
            action_id="com_secarelupus_twitchatintegration::WhisperNotify",
            action_name="Whisper Count",
        )
        self.add_action_holder(self.whisper_notify_holder)

        # Chat message selection (cursor-based moderation system)
        self.chat_select_up_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectUp,
            action_id="com_secarelupus_twitchatintegration::ChatSelectUp",
            action_name="Chat: Previous Message",
        )
        self.add_action_holder(self.chat_select_up_holder)

        self.chat_select_down_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectDown,
            action_id="com_secarelupus_twitchatintegration::ChatSelectDown",
            action_name="Chat: Next Message",
        )
        self.add_action_holder(self.chat_select_down_holder)

        self.chat_select_cancel_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectCancel,
            action_id="com_secarelupus_twitchatintegration::ChatSelectCancel",
            action_name="Chat: Cancel Selection",
        )
        self.add_action_holder(self.chat_select_cancel_holder)

        self.chat_select_delete_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectDelete,
            action_id="com_secarelupus_twitchatintegration::ChatSelectDelete",
            action_name="Chat: Delete Message",
        )
        self.add_action_holder(self.chat_select_delete_holder)

        self.chat_select_ban_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectBan,
            action_id="com_secarelupus_twitchatintegration::ChatSelectBan",
            action_name="Chat: Ban User",
        )
        self.add_action_holder(self.chat_select_ban_holder)

        self.chat_select_pin_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectPin,
            action_id="com_secarelupus_twitchatintegration::ChatSelectPin",
            action_name="Chat: Pin Message",
        )
        self.add_action_holder(self.chat_select_pin_holder)

        self.chat_select_highlight_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectHighlight,
            action_id="com_secarelupus_twitchatintegration::ChatSelectHighlight",
            action_name="Chat: Highlight Message",
        )
        self.add_action_holder(self.chat_select_highlight_holder)

        self.chat_select_shoutout_holder = ActionHolder(
            plugin_base=self,
            action_base=ChatSelectShoutout,
            action_id="com_secarelupus_twitchatintegration::ChatSelectShoutout",
            action_name="Chat: Shoutout User",
        )
        self.add_action_holder(self.chat_select_shoutout_holder)

        # Connection status indicator
        self.connection_status_holder = ActionHolder(
            plugin_base=self,
            action_base=ConnectionStatus,
            action_id="com_secarelupus_twitchatintegration::ConnectionStatus",
            action_name="Connection Status",
        )
        self.add_action_holder(self.connection_status_holder)

        # Register plugin
        self.register(
            plugin_name="Twitchat",
            github_repo="https://github.com/lupi/Twitchat-StreamController",
            plugin_version="1.0.0",
            app_version="1.5.0-beta.6"
        )

    def on_ready(self):
        """Called after plugin registration. Set up OBS connection."""
        super().on_ready()
        self._apply_credentials()
        self.obs_connection.connect()

    def get_settings_area(self):
        """Return the settings UI for OBS connection configuration."""
        from GtkHelper.GtkHelper import BetterPreferencesGroup

        settings = self.get_settings()

        host = settings.get("obs_host", "127.0.0.1")
        port = str(settings.get("obs_port", 4455))
        password = settings.get("obs_password", "")

        group = BetterPreferencesGroup(title="OBS Connection")

        # Host
        host_row = Adw.ActionRow(title="OBS Host")
        host_entry = Gtk.Entry()
        host_entry.set_text(host)
        host_entry.set_placeholder_text("127.0.0.1")
        host_entry.connect("changed", lambda e: self._save_setting("obs_host", e.get_text()))
        host_row.add_suffix(host_entry)
        group.add(host_row)

        # Port
        port_row = Adw.ActionRow(title="OBS Port")
        port_entry = Gtk.Entry()
        port_entry.set_text(port)
        port_entry.set_placeholder_text("4455")
        port_entry.connect("changed", lambda e: self._save_setting("obs_port", int(e.get_text() or 4455)))
        port_row.add_suffix(port_entry)
        group.add(port_row)

        # Password
        pass_row = Adw.ActionRow(title="OBS Password")
        pass_entry = Gtk.Entry()
        pass_entry.set_visibility(False)
        pass_entry.set_text(password)
        pass_entry.set_placeholder_text("Leave empty if no password")
        pass_entry.connect("changed", lambda e: self._save_setting("obs_password", e.get_text()))
        pass_row.add_suffix(pass_entry)
        group.add(pass_row)

        # Status
        status_row = Adw.ActionRow(title="Status")
        status_label = Gtk.Label(
            label="Connected" if self.obs_connection.connected else "Disconnected",
            xalign=1
        )
        self.obs_connection.add_connection_listener(
            lambda connected: status_label.set_text("Connected" if connected else "Disconnected")
        )
        status_row.add_suffix(status_label)
        group.add(status_row)

        # Reconnect button
        reconnect_row = Adw.ActionRow(title="Reconnect")
        reconnect_btn = Gtk.Button(label="Reconnect Now")
        reconnect_btn.connect("clicked", lambda b: self.obs_connection.connect())
        reconnect_row.add_suffix(reconnect_btn)
        group.add(reconnect_row)

        return group

    def _save_setting(self, key: str, value):
        settings = self.get_settings()
        settings[key] = value
        self.set_settings(settings)
        self._apply_credentials()
        # Reconnect with new credentials
        self.obs_connection.connect()

    def _apply_credentials(self):
        settings = self.get_settings()
        host = settings.get("obs_host", "127.0.0.1")
        port = settings.get("obs_port", 4455)
        password = settings.get("obs_password", "")
        self.obs_connection.set_credentials(host, port, password)

    def on_unload(self):
        """Called when plugin is unloaded."""
        self.obs_connection.disconnect()
