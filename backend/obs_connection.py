"""
OBS Websocket v5 connection backend for the StreamController Twitchat plugin.

Handles WebSocket connection to OBS, authentication, sending Twitchat actions
via BroadcastCustomEvent, and receiving Twitchat events via CustomEvent.

Singleton pattern — one connection shared across all plugin actions.
"""
import asyncio
import base64
import hashlib
import json
import threading
import time
import logging
from typing import Callable, Optional

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib

try:
    import websockets
except ImportError:
    websockets = None

logger = logging.getLogger("TwitchatPlugin")
logging.basicConfig(level=logging.INFO)


class OBSConnection:
    """
    Singleton WebSocket client for OBS Websocket v5.

    Usage:
        conn = OBSConnection.get()
        conn.set_credentials("127.0.0.1", 4455, "")
        conn.add_event_listener("FOLLOW", my_handler)
        conn.send_action("GREET_FEED_READ", {"count": 1})
        conn.connect()
    """

    _instance: Optional["OBSConnection"] = None

    @classmethod
    def get(cls) -> "OBSConnection":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._host: str = "127.0.0.1"
        self._port: int = 4455
        self._password: str = ""
        self._ws = None
        self._connected: bool = False
        self._should_reconnect: bool = True
        self._reconnect_delay: float = 1.0
        self._max_reconnect_delay: float = 30.0
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._event_listeners: dict[str, list[Callable]] = {}
        self._connection_listeners: list[Callable[[bool], None]] = []

    def set_credentials(self, host: str, port: int, password: str = ""):
        """Set OBS connection credentials. Call before connect()."""
        self._host = host or "127.0.0.1"
        self._port = port or 4455
        self._password = password or ""

    def add_event_listener(self, event_type: str, callback: Callable):
        """Register a callback for a Twitchat event type."""
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(callback)

    def remove_event_listener(self, event_type: str, callback: Callable):
        """Remove a previously registered event callback."""
        if event_type in self._event_listeners:
            try:
                self._event_listeners[event_type].remove(callback)
            except ValueError:
                pass

    def add_connection_listener(self, callback: Callable[[bool], None]):
        """Register a callback for connection state changes. Called with (connected: bool)."""
        self._connection_listeners.append(callback)

    def remove_connection_listener(self, callback: Callable[[bool], None]):
        try:
            self._connection_listeners.remove(callback)
        except ValueError:
            pass

    def send_action(self, action_type: str, data: Optional[dict] = None):
        """
        Send a Twitchat action via OBS BroadcastCustomEvent.
        This is thread-safe — it schedules the send on the event loop.
        """
        if self._event_loop and self._event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._send_action_async(action_type, data),
                self._event_loop
            )

    async def _send_action_async(self, action_type: str, data: Optional[dict] = None):
        if not self._ws:
            logger.warning("Cannot send action: not connected")
            return

        event_data = {
            "origin": "twitchat",
            "type": action_type,
        }
        if data is not None:
            event_data["data"] = data

        request = {
            "op": 6,
            "d": {
                "requestId": f"twitchat-{action_type}",
                "requestType": "BroadcastCustomEvent",
                "requestData": {
                    "eventData": event_data
                }
            }
        }
        try:
            await self._ws.send(json.dumps(request))
            logger.debug(f"Sent action: {action_type}")
        except Exception as e:
            logger.error(f"Failed to send action {action_type}: {e}")

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self):
        """Start the connection in a background thread. Restarts if already running."""
        # Signal old thread to stop
        self._should_reconnect = False
        if self._event_loop and self._event_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self._disconnect_async(), self._event_loop)
            except Exception:
                pass
        # Wait briefly for old thread to wrap up
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        # Start fresh
        self._should_reconnect = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def disconnect(self):
        """Stop the connection and background thread."""
        self._should_reconnect = False
        if self._event_loop and self._event_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self._disconnect_async(), self._event_loop)
            except Exception:
                pass

    def _run_event_loop(self):
        """Run the asyncio event loop in a dedicated thread."""
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._event_loop.run_until_complete(self._connection_loop())

    async def _connection_loop(self):
        """Main connection loop with auto-reconnect."""
        if websockets is None:
            logger.error("websockets library not installed. Install with: pip install websockets")
            return

        while self._should_reconnect:
            try:
                url = f"ws://{self._host}:{self._port}"
                logger.info(f"Connecting to OBS at {url}")

                async with websockets.connect(url, ping_interval=5) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1.0

                    # OBS v5 handshake: wait for Hello, send Identify
                    hello_raw = await ws.recv()
                    hello = json.loads(hello_raw)
                    if hello.get("op") != 0:
                        logger.error(f"Expected Hello (op 0), got {hello.get('op')}")
                        continue

                    identify = {
                        "op": 1,
                        "d": {"rpcVersion": 1}
                    }

                    # OBS v5 authentication (RFC 6455 challenge-response)
                    auth_info = hello.get("d", {}).get("authentication")
                    if self._password and auth_info:
                        challenge = auth_info.get("challenge", "")
                        salt = auth_info.get("salt", "")
                        secret = base64.b64encode(
                            hashlib.sha256((self._password + salt).encode()).digest()
                        ).decode()
                        auth_string = base64.b64encode(
                            hashlib.sha256((secret + challenge).encode()).digest()
                        ).decode()
                        identify["d"]["authentication"] = auth_string
                        logger.info("Authenticating with password")
                    elif self._password and not auth_info:
                        logger.warning("Password set but server did not request authentication")

                    await ws.send(json.dumps(identify))
                    identified_raw = await ws.recv()
                    identified = json.loads(identified_raw)

                    if identified.get("op") == 2:
                        self._connected = True
                        logger.info("Connected to OBS Websocket")
                        self._notify_connection(True)
                    else:
                        logger.error(f"Identification failed: {identified}")
                        continue

                    # Message receive loop
                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                            self._handle_message(msg)
                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                logger.warning(f"OBS connection error: {e}")

            self._connected = False
            self._ws = None
            self._notify_connection(False)

            if self._should_reconnect:
                logger.info(f"Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay
                )

    async def _disconnect_async(self):
        if self._ws:
            await self._ws.close()
            self._ws = None

    def _handle_message(self, msg: dict):
        """Process incoming OBS messages, filtering for Twitchat events."""
        op = msg.get("op")

        # op 5 = Event
        if op == 5:
            event = msg.get("d", {})
            event_type = event.get("eventType")

            # Only handle CustomEvent from Twitchat
            if event_type == "CustomEvent":
                event_data = event.get("eventData", {})
                if event_data.get("origin") != "twitchat":
                    return

                twitchat_type = event_data.get("type", "")
                twitchat_data = event_data.get("data")

                logger.debug(f"Twitchat event: {twitchat_type}")
                self._dispatch_event(twitchat_type, twitchat_data)

    def _dispatch_event(self, event_type: str, data):
        """Call registered listeners for an event type on the GTK main thread."""
        listeners = self._event_listeners.get(event_type, [])
        for callback in listeners:
            GLib.idle_add(self._safe_invoke, callback, data, event_type)

    def _notify_connection(self, connected: bool):
        for callback in self._connection_listeners:
            GLib.idle_add(self._safe_invoke, callback, connected, "connection")

    @staticmethod
    def _safe_invoke(callback, data, event_type="unknown"):
        """Invoke a callback and log errors. Runs on the GTK main thread via GLib.idle_add."""
        try:
            callback(data)
        except Exception as e:
            logger.error(f"Error in listener for {event_type}: {e}")
        return False  # don't repeat
