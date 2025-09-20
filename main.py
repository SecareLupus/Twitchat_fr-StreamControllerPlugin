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
    OBSConnectionError,
    OBSConnectionManager,
    TwitchatEventBroadcaster,
)
from .settings import TwitchatSettings

from .actions.GreetFeedReadAll.GreetFeedReadAll import GreetFeedReadAllAction


class TwitchatIntegrationPlugin(PluginBase):
    """StreamController plugin entry point for Twitchat integration."""

    def __init__(self) -> None:
        super().__init__(use_legacy_locale=False)

        self.settings = TwitchatSettings.from_dict(self.get_settings())
        self.obs_manager = OBSConnectionManager(self.settings.to_obs_config())
        self.broadcast_service = TwitchatEventBroadcaster(
            self.obs_manager, namespace=self.settings.namespace
        )
        self._initial_connect_thread: threading.Thread | None = None

        self.greet_feed_action_holder = ActionHolder(
            plugin_base=self,
            action_base=GreetFeedReadAllAction,
            action_id="com.secarelupus.twitchatintegration::GreetFeedReadAll",
            action_name="Twitchat: Mark Greet Feed Read",
        )
        self.add_action_holder(self.greet_feed_action_holder)

        self.register(
            plugin_name="Twitchat Integration",
            github_repo="https://github.com/SecareLupus/StreamControllerTwitchatIntegration",
            plugin_version="0.1.0",
            app_version="1.1.1-alpha",
        )

        # Persist defaults on first launch so users can tweak them.
        self._persist_settings()
        self._connect_in_background()

    # ------------------------------------------------------------------
    # Plugin lifecycle helpers
    # ------------------------------------------------------------------
    def on_disconnect(self, conn) -> None:  # noqa: D401 - conforms to PluginBase
        """Disconnect from OBS when the plugin is torn down."""

        try:
            self.obs_manager.disconnect()
        finally:
            super().on_disconnect(conn)

    # ------------------------------------------------------------------
    # Configuration & persistence
    # ------------------------------------------------------------------
    def get_config_rows(self) -> List[Adw.PreferencesRow]:
        rows: List[Adw.PreferencesRow] = []

        host_row = Adw.EntryRow(title="OBS Host", subtitle="Hostname or IP address")
        host_row.set_text(self.settings.host)
        host_row.connect("changed", self._on_host_changed)
        rows.append(host_row)

        port_row = Adw.EntryRow(title="Port", subtitle="OBS WebSocket port")
        port_row.set_input_purpose(Gtk.InputPurpose.DIGITS)
        port_row.set_text(str(self.settings.port))
        port_row.connect("changed", self._on_port_changed)
        rows.append(port_row)

        password_row = Adw.PasswordEntryRow(title="Password")
        password_row.set_text(self.settings.password)
        password_row.connect("changed", self._on_password_changed)
        rows.append(password_row)

        ssl_row = Adw.SwitchRow(title="Use secure WebSocket (wss)")
        ssl_row.set_active(self.settings.use_ssl)
        ssl_row.connect("notify::active", self._on_ssl_toggled)
        rows.append(ssl_row)

        namespace_row = Adw.EntryRow(title="Event namespace")
        namespace_row.set_text(self.settings.namespace)
        namespace_row.connect("changed", self._on_namespace_changed)
        rows.append(namespace_row)

        return rows

    def _persist_settings(self) -> None:
        self.set_settings(self.settings.to_dict())

    def _update_settings(self, **changes: Any) -> None:
        new_settings = self.settings.update(**changes)
        if new_settings == self.settings:
            return

        logger.info("Updating Twitchat plugin settings: {}", changes)
        self.settings = new_settings
        self.broadcast_service.set_namespace(self.settings.namespace)
        self.obs_manager.update_config(
            host=self.settings.host,
            port=self.settings.port,
            password=self.settings.password,
            use_ssl=self.settings.use_ssl,
            request_timeout=self.settings.request_timeout,
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

    def _on_ssl_toggled(self, row: Adw.SwitchRow, _param) -> None:
        self._update_settings(use_ssl=row.get_active())

    def _on_namespace_changed(self, row: Adw.EntryRow) -> None:
        namespace = row.get_text().strip()
        if not namespace:
            return
        self._update_settings(namespace=namespace)

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    def _connect_in_background(self) -> None:
        if self._initial_connect_thread and self._initial_connect_thread.is_alive():
            return

        def worker() -> None:
            try:
                self.obs_manager.ensure_connection()
            except OBSConnectionError as exc:
                logger.warning("OBS connection attempt failed: {}", exc)

        self._initial_connect_thread = threading.Thread(
            target=worker,
            name="twitchat-obs-connect",
            daemon=True,
        )
        self._initial_connect_thread.start()

    # ------------------------------------------------------------------
    # Public helpers for actions
    # ------------------------------------------------------------------
    def get_broadcaster(self) -> TwitchatEventBroadcaster:
        return self.broadcast_service

    def broadcast(self, action: str, payload: Any | None = None) -> bool:
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary or None")
        return self.broadcast_service.safe_broadcast(action, payload)
