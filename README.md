# Twitchat Integration for StreamController

[StreamController](https://github.com/StreamController/StreamController) plugin that connects to [Twitchat](https://twitchat.fr) via OBS WebSocket v5, providing 35 Stream Deck actions for chat moderation, overlay control, event monitoring, and live stream management.

## Architecture

```
Stream Deck key press
    → Action.on_key_down()
    → PluginBase.twitchat.send_action(type, data)
    → OBSConnectionManager.send_request("BroadcastCustomEvent", {eventData: {origin: "twitchat", type, data}})
    → OBS WebSocket v5
    → Twitchat receives action

Reverse path (events):
    Twitchat emits event
    → OBS relays as CustomEvent
    → OBSConnectionManager receiver loop
    → TwitchatAPI.handle_raw_message() dispatches by event type
    → Action callback updates display
```

Envelope format: `{origin: "twitchat", type: "ACTION_NAME", data: {...}}`

## Actions

### Chat & Moderation

| Action | Press does | Config |
|--------|-----------|--------|
| **Chat Control** | Read, scroll, pause, merge toggle — 8 modes | Operation dropdown, count |
| **Chat: Previous Message** | Move selection cursor up | — |
| **Chat: Next Message** | Move selection cursor down | — |
| **Chat: Cancel Selection** | Deselect message | — |
| **Chat: Delete Message** | Delete selected message | — |
| **Chat: Ban User** | Ban selected message's author | — |
| **Chat: Pin Message** | Pin/unpin selected message | — |
| **Chat: Highlight Message** | Show selected message on overlay | — |
| **Chat: Shoutout User** | Shoutout selected message's author | — |
| **Send Chat Message** | Send pre-configured message | Message text |
| **AutoMod Accept** | Allow latest held message | — |
| **AutoMod Reject** | Reject latest held message | — |

### Overlay Toggles

| Action | Press toggles |
|--------|--------------|
| **Toggle Panel Visibility** | Poll, prediction, bingo, raffle, viewers count, mod tools, censor, merge — 8 targets |
| **Emergency Toggle** | Emergency mode on/off (displays current state) |
| **Clear Highlight** | Clear chat highlight overlay |
| **Hide Alert** | Dismiss notification overlay |
| **Stop TTS** | Stop text-to-speech playback |

### Triggers

| Action | Press does | Config |
|--------|-----------|--------|
| **Execute Trigger** | Fire trigger by ID | Trigger ID |
| **Toggle Trigger** | Enable/disable trigger by ID | Trigger ID, mode |

### Display Actions (read-only)

These show live data from Twitchat events on the Stream Deck key.

| Action | Shows |
|--------|-------|
| **Latest Follower** | Name + cumulative count |
| **Latest Subscriber** | Tier + name + count |
| **Latest Cheer** | Name + bits + total |
| **Latest Donation** | Donor name + amount |
| **Latest Reward** | Channel points reward + redeemer |
| **Current Track** | Track + artist (press to refresh) |
| **Poll Status** | Poll title + leading choice |
| **Whisper Count** | Unread whisper count (purple key, press to clear) |
| **Mention Alert** | Flashes red on @mention, shows name |

### Status Indicators

| Action | Shows |
|--------|-------|
| **Stream Status** | Green "LIVE" / dark "OFFLINE" |
| **Record Status** | Red "REC" / dark "STOP" |
| **Connection Status** | Green "OK" / red "OFF" — press to reconnect |

### Interactive Systems

| Action | Press does | Config |
|--------|-----------|--------|
| **Raffle Control** | Start / pick winner / end raffle | Mode, command, duration |
| **Timer / Countdown** | Start timer / start countdown / get current / stop | Mode, name, duration |
| **Counter Control** | Increment/decrement a counter | Counter ID, step |
| **Shoutout** | Shoutout latest raider | — |

## Plugin Settings

- **OBS Host** — IP/hostname (default `127.0.0.1`)
- **Port** — OBS WebSocket port (default `4455`)
- **Password** — OBS WebSocket password (leave empty if no auth)
- **Status** — Shows connection state
- **Reconnect Now** — Manual reconnect button

Settings changes trigger immediate reconnection with new credentials.

## ⚠️ Testing Status & Known Limitations

**This plugin requires extensive testing.** Many actions have been built against the documented Twitchat Public API but have not been validated against a live Twitchat instance + OBS setup.

### Known limitations

**Chat Highlight requires a selected chat message.** The flow is:
1. Press **Chat: Previous Message** or **Chat: Next Message** to navigate to a chat message (not a system notification like a follow/sub/bits entry)
2. Press **Chat: Highlight Message** within 5 seconds (selection times out)
3. The chat highlight overlay browser source must be active in Twitchat/OBS to see the result

The selection cursor distinguishes between message types — only user chat messages (type `MESSAGE`) can be highlighted. System events like subscriptions, follows, and bits are not highlightable.

**Chat selection times out after 5 seconds.** If you navigate to a message then wait, the selection expires. Press Prev/Next again to re-select.

### Testing gaps

- Connection lifecycle: initial connect, disconnect detection, reconnection after OBS restart
- Event display actions: timing, data shape validation under real event load
- Chat selection system: cursor behavior in multi-column layouts
- Auth: OBS v5 challenge-response with passwords
- StreamController compatibility: tested only with 1.5.0-beta.6 in development mode
- All 35 actions compile clean but need runtime validation with actual Twitchat state

## Installation

### From GitHub
```bash
git clone https://github.com/SecareLupus/Twitchat_fr-StreamControllerPlugin.git \
  ~/.var/app/com.core447.StreamController/data/plugins/com_secarelupus_twitchatintegration
pip install websocket-client
```

### From source (development)
```bash
cd StreamController
mkdir -p data/plugins
ln -s /path/to/Twitchat_fr-StreamControllerPlugin data/plugins/com_secarelupus_twitchatintegration
pip install websocket-client loguru
python3 main.py --devel --skip-load-hardware-decks
```

## Prerequisites

- OBS Studio 28+ with WebSocket server enabled
- [Twitchat](https://twitchat.fr) running with Public API enabled
- [StreamController](https://github.com/StreamController/StreamController) 1.5.0-beta.6+
- `websocket-client` Python package (`pip install websocket-client`)

## License

MIT — see [LICENSE](LICENSE)
