# Source provenance

## Authoritative-copy decision

| Object | Role | Evidence | Rule |
|:--|:--|:--|:--|
| `/mnt/shared/2026项目/车流量自适应的交通信号控制系统_源码.tar.gz` | Read-only historical baseline | SHA-256 `df48d6619b8558c23917f8735d54b4e7d19cb891f112edebd42314d74ec19e09`; modified 2026-05-06 | Never edited or repacked |
| `/home/rongyi/桌面/车流量自适应的交通信号控制系统` | Newer authoritative source | Files dated through 2026-05-16 and a later deployment guide; top-level `.git` was empty | Read-only source; not cleaned in place |
| `/home/rongyi/桌面/adaptive-traffic-signal-system` | Clean publication candidate | Explicit copy exclusions and fresh public Git history | All public hardening occurs here |

A similarly named `/home/rongyi/桌面/基于esp32s3交通摄像` project is a different ESP32-S3 dual-board project and was not merged.

## Merge and exclusion record

Included from the newer desktop source:

- FastAPI backend, Vue 3 frontend and both firmware projects;
- protocol and source-derived wiring information;
- package lock and PlatformIO dependency declarations.

Added only from the historical archive after review:

- `simulator/fake_cam.py` and `simulator/fake_mcu.py`;
- the empty `samples/.gitkeep` placeholder.

Excluded before the first commit:

- the empty `.git/` directory and all editor configuration;
- `backend/.env`, which contained historical camera addresses;
- all model weights, including the approximately 6.5 MB nano and 87.8 MB large weights;
- `frontend/node_modules/`, `frontend/dist/`, Python caches and bytecode;
- any historical Wi-Fi credentials present in the archive firmware;
- generated PlatformIO output and private static-address configuration.

## Public hardening changes

- loopback backend, simulator and CORS defaults;
- local-only environment/build configuration for credentials and real LAN endpoints;
- DHCP camera firmware in the public matrix;
- no model weights committed;
- narrow process liveness and observed frame/client facts rather than an overall `ok` state;
- visible frontend distinction between UI WebSocket connectivity, device client count and stream freshness;
- invalid video directions fail closed;
- tests for timing bounds, counting, status semantics, simulated images and WebSocket counts.

These changes are source/build verified. They do not establish present-day five-board hardware behavior or real-road suitability.
