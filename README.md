# Adaptive Traffic Signal System

An educational tabletop prototype that combines four ESP32-CAM MJPEG streams, YOLOv8 tracking and vehicle counting, a FastAPI/Vue 3 workstation, and an ESP32 traffic-light controller.

[![Validate](https://github.com/rongyishuaige7/adaptive-traffic-signal-system/actions/workflows/validate.yml/badge.svg)](https://github.com/rongyishuaige7/adaptive-traffic-signal-system/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-f97316.svg)](LICENSE)

> **Evidence scope, 2026-07-17:** Source-confirmed · Backend tests passed · Frontend build-verified · Four ESP32-CAM direction builds and ESP32 main build-verified · Simulator contract-tested · Current five-board and end-to-end hardware re-test not run.

This repository shows how a multi-board computer-vision prototype fits together. It is **not road infrastructure, a certified signal controller or evidence of traffic optimization/detection accuracy**.

## What the prototype covers

- four N/S/E/W AI Thinker ESP32-CAM firmware builds with DHCP and MJPEG endpoints;
- four backend workers for YOLOv8/ByteTrack vehicle tracking and virtual-line counts;
- a two-phase N/S and E/W timing FSM with bounded linear green-time calculation;
- FastAPI status, MJPEG re-stream and UI/device WebSockets;
- a Vue 3 dashboard that separates UI connection, device-client count and recent-frame facts;
- an ESP32 main controller for 12 light outputs and four SSD1306 displays through TCA9548A;
- four synthetic MJPEG sources and a terminal MCU simulator for hardware-free teaching;
- source-derived BOM and wiring boundary.

## Architecture

```text
ESP32-CAM N/S/E/W ── MJPEG ──┐
                              ▼
                    FastAPI + YOLOv8/ByteTrack
                              │
                 ┌────────────┴────────────┐
                 │ UI WebSocket + MJPEG    │ device WebSocket
                 ▼                         ▼
              Vue 3 UI            ESP32 main controller
                                      │          │
                                 12 LED GPIO   TCA9548A
                                                  │
                                           4 × SSD1306
```

## Repository layout

```text
backend/                 FastAPI, counting, timing and WebSocket service
frontend/                Vue 3 / Element Plus / ECharts dashboard
firmware/esp32_cam/      N/S/E/W AI Thinker ESP32-CAM builds
firmware/esp32_main/     12-light + four-OLED ESP32 controller
simulator/               Local fake camera and fake MCU tools
tests/                   Hardware-free backend/simulator contracts
hardware/                Source-derived BOM and wiring diagram
docs/                    Setup, status, verification and provenance
scripts/                 Secret, repository and full verification gates
```

## Quick verification

The one-command gate avoids real credentials, model downloads and hardware:

```bash
bash scripts/verify.sh
```

It runs the secret/repository checks, Python tests, a clean Vue production build, N/S/E/W ESP32-CAM builds and the ESP32 main build. See [VERIFICATION.md](docs/VERIFICATION.md) for exact evidence boundaries.

## Local simulator

Create a virtual environment and install development dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements-dev.txt
python simulator/fake_cam.py
```

The default camera URLs are loopback ports `8181`–`8184`. In other terminals, start the backend from `backend/` and the frontend from `frontend/`:

```bash
# backend terminal
cd backend
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000

# frontend terminal
cd frontend
npm ci
npm run dev
```

Optional terminal device simulation:

```bash
python simulator/fake_mcu.py --uri ws://127.0.0.1:8000/ws/device
```

Synthetic frames prove only simulator/transport behavior. The full video worker also needs a locally obtained YOLO model; see [MODEL_SETUP.md](docs/MODEL_SETUP.md).

## Hardware configuration

Public firmware contains no real Wi-Fi credentials or private-LAN addresses. It compiles with empty/non-routable test values, then fails closed at runtime until local configuration is supplied.

- Copy the relevant `local-config.example.ini` values into an ignored local PlatformIO configuration or environment build flags.
- Keep ESP32-CAM on DHCP unless you have a documented local addressing plan.
- Set the main controller's `PC_HOST` to the actual backend host only in local configuration.
- Confirm the exact board revisions, voltages, current limiting, GPIO map and common-ground topology against [HARDWARE.md](HARDWARE.md).

## Accurate runtime semantics

- `GET /health` means only **the FastAPI process responded**.
- `GET /api/runtime` reports whether each direction has received a recent processed frame and how many UI/device WebSocket clients are connected.
- A device client count is not authenticated device identity or physical light feedback.
- A placeholder image remains explicitly `no fresh frame`; it is never counted as a healthy camera.
- The ESP32 main source requests all-red after WebSocket disconnect, but the current public commit has not been re-tested on the retained lights.

## Known limits

- Current four ESP32-CAM boards, main ESP32, 12 LEDs, TCA9548A and four OLEDs have not been re-tested end to end.
- No real product photo, demo video, current UI screenshot or EDA/manufacturing file is included.
- No YOLO model weight is distributed; upstream licensing applies.
- No current dataset, precision/recall, count error, latency, frame-loss or stability evaluation exists.
- HTTP, MJPEG and WebSocket endpoints have no authentication or TLS. Loopback is the default; real-hardware LAN use must be explicit and isolated.
- The device protocol has no authenticated identity, command ACK, physical light feedback, hardware interlock or conflict monitor.
- This project must never control real road signals.

## Documentation

- [Hardware and wiring boundary](HARDWARE.md)
- [Deployment and simulation](docs/DEPLOYMENT.md)
- [Model setup and license boundary](docs/MODEL_SETUP.md)
- [WebSocket protocol](docs/PROTOCOL.md)
- [Project status](docs/PROJECT_STATUS.md)
- [Source provenance](docs/SOURCE_PROVENANCE.md)
- [Verification](docs/VERIFICATION.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## License

Original repository material is available under the [MIT License](LICENSE). Dependencies and model weights retain their own terms. In particular, review the Ultralytics AGPL-3.0/Enterprise boundary in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
