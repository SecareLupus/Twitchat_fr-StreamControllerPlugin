from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
import uuid
from dataclasses import dataclass, replace
from typing import Any, Dict, Optional

from loguru import logger
from websocket import (
    WebSocket,
    WebSocketConnectionClosedException,
    WebSocketException,
    create_connection,
)


class OBSConnectionError(Exception):
    """Base class for OBS WebSocket related errors."""


class OBSAuthenticationError(OBSConnectionError):
    """Raised when authentication with OBS WebSocket fails."""


class OBSNotConnectedError(OBSConnectionError):
    """Raised when an operation requires an established connection."""


class OBSResponseTimeoutError(OBSConnectionError):
    """Raised when OBS does not answer a request within the timeout."""


class OBSRequestError(OBSConnectionError):
    """Raised when OBS returns an error response for a request."""

    def __init__(self, request_type: str, status: Dict[str, Any]):
        self.request_type = request_type
        self.status = status
        message = status.get("comment") or status.get("message") or "Unknown OBS request failure"
        code = status.get("code")
        super().__init__(f"{request_type} failed with code {code}: {message}")


@dataclass(frozen=True)
class OBSConnectionConfig:
    """User configurable parameters for the OBS WebSocket connection."""

    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""
    use_ssl: bool = False
    request_timeout: float = 5.0
    event_subscriptions: int = 0

    def as_url(self) -> str:
        scheme = "wss" if self.use_ssl else "ws"
        return f"{scheme}://{self.host}:{self.port}"


class OBSConnectionManager:
    """Lightweight OBS WebSocket RPC client tailored for StreamController plugins."""

    def __init__(self, config: OBSConnectionConfig | None = None) -> None:
        self._config = config or OBSConnectionConfig()

        self._ws: Optional[WebSocket] = None
        self._rpc_version: int = 1

        self._connection_lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._responses: Dict[str, Dict[str, Any]] = {}
        self._response_condition = threading.Condition()
        self._receiver_thread: Optional[threading.Thread] = None
        self._receiver_running = threading.Event()
        self._identified = threading.Event()

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    @property
    def config(self) -> OBSConnectionConfig:
        return self._config

    def update_config(self, **kwargs: Any) -> OBSConnectionConfig:
        """Return a new configuration with updated values and schedule reconnection if needed."""

        new_config = replace(self._config, **kwargs)
        if new_config == self._config:
            return self._config

        reconnect_required = (
            new_config.host != self._config.host
            or new_config.port != self._config.port
            or new_config.use_ssl != self._config.use_ssl
            or new_config.password != self._config.password
        )

        was_connected = self.is_connected()
        self._config = new_config

        if was_connected and reconnect_required:
            logger.info("Reconnecting to OBS WebSocket after configuration change")
            try:
                self.disconnect()
                self.connect()
            except OBSConnectionError as exc:
                logger.error("Failed to reconnect to OBS: {}", exc)

        return self._config

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------
    def is_connected(self) -> bool:
        return self._ws is not None and self._identified.is_set()

    def connect(self, timeout: Optional[float] = None) -> None:
        """Establish the WebSocket connection and perform the OBS handshake."""

        with self._connection_lock:
            if self.is_connected():
                return

            try:
                self._do_connect(timeout)
            except OBSConnectionError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                self._safe_close()
                raise OBSConnectionError(str(exc)) from exc

    def ensure_connection(self) -> None:
        """Connect if not already connected."""

        if not self.is_connected():
            self.connect()

    def disconnect(self) -> None:
        """Close the connection and stop the receiver thread."""

        with self._connection_lock:
            self._stop_receiver()
            self._safe_close()
            self._identified.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def send_request(
        self,
        request_type: str,
        request_data: Optional[Dict[str, Any]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Send a RPC request to OBS and wait for the response."""

        if not self.is_connected():
            raise OBSNotConnectedError("OBS WebSocket is not connected")

        request_id = str(uuid.uuid4())
        payload = {
            "op": 6,
            "d": {
                "requestType": request_type,
                "requestId": request_id,
                "requestData": request_data or {},
            },
        }

        with self._send_lock:
            self._send(payload)

        response = self._wait_for_response(request_id, timeout)
        status = response.get("requestStatus", {})
        if not status.get("result", False):
            raise OBSRequestError(request_type, status)
        return response.get("responseData", {})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _do_connect(self, timeout: Optional[float]) -> None:
        connect_timeout = timeout or self._config.request_timeout
        logger.debug("Connecting to OBS WebSocket at {}", self._config.as_url())
        try:
            ws = create_connection(self._config.as_url(), timeout=connect_timeout)
        except Exception as exc:  # pragma: no cover - depends on env
            raise OBSConnectionError(f"Failed to connect to OBS at {self._config.as_url()}: {exc}") from exc

        self._ws = ws
        try:
            self._perform_handshake(connect_timeout)
        except Exception:
            self._safe_close()
            raise

        self._start_receiver()

    def _perform_handshake(self, timeout: float) -> None:
        hello = self._recv(timeout)
        if hello.get("op") != 0:
            raise OBSConnectionError("Did not receive OBS Hello message during handshake")

        hello_data = hello.get("d", {})
        self._rpc_version = int(hello_data.get("rpcVersion", 1))

        identify_payload = {
            "op": 1,
            "d": {
                "rpcVersion": self._rpc_version,
                "eventSubscriptions": self._config.event_subscriptions,
            },
        }

        auth = hello_data.get("authentication")
        if auth:
            if not self._config.password:
                raise OBSAuthenticationError("OBS WebSocket requires a password but none was provided")
            identify_payload["d"]["authentication"] = self._build_auth_response(auth)

        self._send(identify_payload)

        identified = self._recv(timeout)
        if identified.get("op") != 2:
            raise OBSConnectionError("OBS handshake failed: missing Identified acknowledgement")

        self._identified.set()
        if self._ws is not None:
            # Switch to blocking mode for the dedicated receiver thread.
            self._ws.settimeout(None)
        logger.debug("OBS WebSocket handshake completed (RPC version {})", self._rpc_version)

    def _start_receiver(self) -> None:
        if self._receiver_thread and self._receiver_thread.is_alive():
            return

        self._receiver_running.set()
        self._receiver_thread = threading.Thread(
            target=self._receiver_loop,
            name="obs-ws-receiver",
            daemon=True,
        )
        self._receiver_thread.start()

    def _stop_receiver(self) -> None:
        self._receiver_running.clear()
        if self._receiver_thread and self._receiver_thread.is_alive():
            if self._ws is not None:
                try:
                    self._ws.close()
                except WebSocketException:
                    pass
            self._receiver_thread.join(timeout=1.0)
        self._receiver_thread = None

    def _receiver_loop(self) -> None:
        while self._receiver_running.is_set():
            if self._ws is None:
                break
            try:
                message = self._ws.recv()
            except WebSocketConnectionClosedException:
                logger.warning("Lost connection to OBS WebSocket")
                break
            except OSError:
                logger.warning("OBS WebSocket recv interrupted")
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Unexpected OBS WebSocket error: {}", exc)
                break

            if message is None:
                continue

            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                logger.warning("Received malformed OBS payload: {}", message)
                continue

            self._handle_message(payload)

        self._identified.clear()
        self._receiver_running.clear()
        self._safe_close()

    def _handle_message(self, payload: Dict[str, Any]) -> None:
        op = payload.get("op")
        data = payload.get("d", {})

        if op == 0:
            # OBS requested re-identification (hot reload). Repeat handshake.
            logger.info("OBS WebSocket requested re-identification")
            try:
                self._perform_handshake(self._config.request_timeout)
            except Exception as exc:
                logger.error("Re-identification failed: {}", exc)
        elif op == 2:
            self._identified.set()
            logger.debug("OBS WebSocket identified again")
        elif op == 5:
            event_type = data.get("eventType")
            logger.debug("OBS Event received: {}", event_type)
        elif op == 7:
            request_id = data.get("requestId")
            if request_id:
                with self._response_condition:
                    self._responses[request_id] = data
                    self._response_condition.notify_all()
        elif op == 8:
            request_id = data.get("requestId")
            if request_id:
                with self._response_condition:
                    self._responses[request_id] = data
                    self._response_condition.notify_all()
        else:
            logger.debug("Unhandled OBS message op={}: {}", op, data)

    def _send(self, payload: Dict[str, Any]) -> None:
        if self._ws is None:
            raise OBSNotConnectedError("Cannot send payload, websocket is closed")
        message = json.dumps(payload)
        try:
            self._ws.send(message)
        except WebSocketException as exc:
            raise OBSConnectionError(f"Failed to send message to OBS: {exc}") from exc

    def _recv(self, timeout: float) -> Dict[str, Any]:
        if self._ws is None:
            raise OBSNotConnectedError("Cannot receive payload, websocket is closed")

        previous_timeout = self._ws.gettimeout()
        self._ws.settimeout(timeout)
        try:
            message = self._ws.recv()
        except WebSocketException as exc:
            raise OBSConnectionError(f"Failed to receive data from OBS: {exc}") from exc
        finally:
            self._ws.settimeout(previous_timeout)

        try:
            return json.loads(message)
        except json.JSONDecodeError as exc:
            raise OBSConnectionError("Received invalid JSON from OBS") from exc

    def _wait_for_response(self, request_id: str, timeout: Optional[float]) -> Dict[str, Any]:
        deadline = time.perf_counter() + (timeout or self._config.request_timeout)
        with self._response_condition:
            while True:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    raise OBSResponseTimeoutError(
                        f"Timeout waiting for OBS response to request {request_id}"
                    )

                if request_id in self._responses:
                    data = self._responses.pop(request_id)
                    return data

                self._response_condition.wait(timeout=remaining)

    def _safe_close(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            except WebSocketException:
                pass
        self._ws = None

    def _build_auth_response(self, auth_payload: Dict[str, Any]) -> str:
        challenge = auth_payload.get("challenge")
        salt = auth_payload.get("salt")
        if challenge is None or salt is None:
            raise OBSAuthenticationError("OBS authentication payload missing challenge or salt")

        secret = hashlib.sha256((self._config.password + salt).encode("utf-8")).digest()
        secret_b64 = base64.b64encode(secret)
        auth_response = hashlib.sha256(secret_b64 + challenge.encode("utf-8")).digest()
        return base64.b64encode(auth_response).decode("utf-8")


__all__ = [
    "OBSConnectionConfig",
    "OBSConnectionError",
    "OBSAuthenticationError",
    "OBSNotConnectedError",
    "OBSResponseTimeoutError",
    "OBSRequestError",
    "OBSConnectionManager",
]
