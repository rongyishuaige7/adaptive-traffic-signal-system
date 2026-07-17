# Verification

## One-command local gate

```bash
bash scripts/verify.sh
```

The gate creates an isolated source copy, then checks:

1. credential and private-LAN patterns;
2. required files, generated-output exclusions, file size, SVG/BOM and claim contracts;
3. Python compile and backend/simulator tests without model downloads or hardware;
4. a Vue 3 production build using `npm ci`;
5. four ESP32-CAM direction firmware builds and one ESP32 main build with non-secret compile-time test values.

## Current verified result

On 2026-07-17 the candidate passed:

```text
Secret scan: PASS
Repository check: PASS
Python pytest: 11 passed
Vue production build: PASS
ESP32-CAM N/S/E/W builds: PASS
ESP32 main build: PASS
```

This is build and contract evidence. CI does not download YOLO model weights, run inference, connect to real camera streams, flash an ESP32, inspect LEDs/OLEDs or control a physical intersection model.

## Current hardware re-test checklist

Bind any future result to an exact commit and date, then record:

1. the exact main ESP32, four ESP32-CAM boards and camera sensor models;
2. power supplies, boot stability and real wiring against `HARDWARE.md`;
3. four independent camera boots, addresses and sustained MJPEG streams;
4. backend model setup and all four stream-freshness facts;
5. detection and tracking on controlled test clips, with a separate accuracy evaluation if accuracy is claimed;
6. crossing counts for N/S/E/W and timing calculation inputs/outputs;
7. WebSocket state reaching the physical controller;
8. each of 12 LEDs and four OLEDs matching the commanded phases;
9. WebSocket interruption causing an observable all-red prototype state;
10. recovery, frame loss, latency, stability and any untested item.

Do not turn a simulator run or an Actions build into current hardware or road-safety evidence.
