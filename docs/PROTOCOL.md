# WebSocket and status contracts

## UI WebSocket

- Endpoint: `/ws/ui`
- Server to UI: repeated `state` JSON payloads
- Client messages are ignored by the current backend.

## Device WebSocket

- Endpoint: `/ws/device`
- Server to device: the same repeated `state` payload
- Device to server: current firmware sends heartbeat JSON for debugging; it is not used as an authenticated ACK.

Example state:

```json
{
  "type": "state",
  "phase": "NS_GREEN",
  "remain_s": 8,
  "total_s": 10,
  "yellow_s": 3,
  "flow_per_min": {"N": 0, "S": 0, "E": 0, "W": 0},
  "traffic": {},
  "ws_clients": {"ui": 1, "device": 0},
  "green_ns_next": 10,
  "green_ew_next": 10
}
```

`ws_clients.device > 0` means one or more WebSocket connections exist. It does not prove client identity, an ESP32 booted correctly, JSON was applied, LEDs changed, OLEDs updated or a safe signal state exists.

## HTTP facts

| Endpoint | Exact meaning |
|:--|:--|
| `GET /health` | FastAPI process liveness response only |
| `GET /api/status` | Current in-process FSM payload and observed counts |
| `GET /api/runtime` | Configuration switches, per-direction recent-frame facts and WebSocket connection counts |
| `GET /api/traffic` | Latest in-memory per-direction counter snapshots |
| `GET /api/video/{N,S,E,W}.mjpg` | Annotated frame stream or an explicit waiting placeholder |

There is no authentication, TLS, device identity, message signature, replay protection, command acknowledgement or physical feedback in this teaching protocol.
