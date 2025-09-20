from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from .obs_connection import (
    OBSConnectionManager,
    OBSNotConnectedError,
    OBSRequestError,
    OBSResponseTimeoutError,
)


class TwitchatEventBroadcaster:
    """High level helper to emit Twitchat custom events through OBS."""

    def __init__(self, connection: OBSConnectionManager, namespace: str = "twitchat") -> None:
        self._connection = connection
        self._namespace = namespace

    @property
    def namespace(self) -> str:
        return self._namespace

    def set_namespace(self, namespace: str) -> None:
        if not namespace:
            raise ValueError("Namespace cannot be empty")
        self._namespace = namespace

    def ensure_connection(self) -> None:
        self._connection.ensure_connection()

    def broadcast(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Send a Twitchat-specific BroadcastCustomEvent via OBS."""

        if not action:
            raise ValueError("Action identifier must be provided")

        event_type = self._format_event_type(action)
        event_data = payload or {}
        logger.debug("Broadcasting Twitchat event {} with payload {}", event_type, event_data)

        response = self._connection.send_request(
            "BroadcastCustomEvent",
            {
                "eventType": event_type,
                "eventData": event_data,
            },
            timeout=timeout,
        )
        return response

    def safe_broadcast(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> bool:
        """Broadcast and swallow expected runtime errors, returning success state."""

        try:
            self.broadcast(action, payload, timeout=timeout)
        except (OBSNotConnectedError, OBSRequestError, OBSResponseTimeoutError) as exc:
            logger.error("Failed to broadcast Twitchat event {}: {}", action, exc)
            return False
        return True

    def _format_event_type(self, action: str) -> str:
        action = action.strip()
        if ":" in action:
            # Allow callers to supply fully qualified event types.
            return action
        return f"{self._namespace}:{action}"


__all__ = [
    "TwitchatEventBroadcaster",
]
