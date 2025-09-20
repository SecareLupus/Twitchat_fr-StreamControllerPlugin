# Twitchat Integration

StreamController plugin that forwards StreamController actions to [Twitchat.fr](https://twitchat.fr) by leveraging the OBS WebSocket `BroadcastCustomEvent` RPC.

## What it does today
- Manages an authenticated OBS WebSocket 5 connection (including optional TLS support).
- Exposes a high level broadcaster service ready for plugin actions to trigger Twitchat events via `BroadcastCustomEvent`.
- Persists plugin level settings (host, port, password, namespace) and provides a configuration UI inside StreamController.

## Getting started
1. Install and enable the OBS WebSocket 5 module in OBS (available out of the box since OBS 28).
2. Open the plugin settings in StreamController and configure the OBS host/port, password and preferred Twitchat namespace.
3. Build StreamController actions that call `plugin.broadcast(<action>, <payload>)` or use `plugin.get_broadcaster()` directly.

The plugin attempts to connect to OBS in the background and automatically reconnects when settings change. Errors are logged through StreamController's plugin logger.

## Next steps
Implement StreamController actions under `actions/` that compose Twitchat requests using the broadcaster service and expose them on your StreamController decks.
