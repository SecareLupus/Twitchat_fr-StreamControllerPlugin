"""
Twitchat event broadcaster — sends actions and dispatches received events
through the OBS WebSocket connection using the correct Twitchat envelope.

Envelope format: {origin: "twitchat", type: ACTION, data: {...}}
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, Optional

from .obs_connection import OBSConnectionManager

logger = logging.getLogger("TwitchatPlugin")


class TwitchatAPI:
    """
    Sends Twitchat actions via OBS BroadcastCustomEvent and dispatches
    incoming Twitchat CustomEvents to registered listeners.
    """

    def __init__(self, connection: OBSConnectionManager) -> None:
        self._connection = connection
        self._listeners: Dict[str, list[Callable]] = {}

    # ------------------------------------------------------------------
    # Sending actions
    # ------------------------------------------------------------------
    def send_action(self, action_type: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Send a Twitchat action via OBS BroadcastCustomEvent."""
        if not action_type:
            raise ValueError("Action type must be provided")

        event_data = {
            "origin": "twitchat",
            "type": action_type,
            "data": data or {},
        }

        try:
            self._connection.send_request(
                "BroadcastCustomEvent",
                {"eventData": event_data},
            )
            logger.debug("Sent action: %s", action_type)
            return True
        except Exception as exc:
            logger.error("Failed to send action %s: %s", action_type, exc)
            return False

    # ------------------------------------------------------------------
    # Receiving events
    # ------------------------------------------------------------------
    def add_listener(self, event_type: str, callback: Callable[[Optional[dict]], None]) -> None:
        """Register a callback for a Twitchat event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def remove_listener(self, event_type: str, callback: Callable[[Optional[dict]], None]) -> None:
        """Remove a previously registered event callback."""
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass

    def handle_raw_message(self, message: str) -> None:
        """
        Process a raw OBS WebSocket message, dispatching Twitchat events.
        Called by OBSConnectionManager's receiver loop.
        """
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return

        op = payload.get("op")
        if op != 5:  # Not an event
            return

        event = payload.get("d", {})
        if event.get("eventType") != "CustomEvent":
            return

        event_data = event.get("eventData", {})
        if event_data.get("origin") != "twitchat":
            return

        twitchat_type = event_data.get("type", "")
        twitchat_data = event_data.get("data")

        logger.debug("Twitchat event: %s", twitchat_type)
        self._dispatch(twitchat_type, twitchat_data)

    def _dispatch(self, event_type: str, data: Optional[dict]) -> None:
        listeners = self._listeners.get(event_type, [])
        for callback in listeners:
            try:
                callback(data)
            except Exception as exc:
                logger.error("Error in event listener for %s: %s", event_type, exc)
