# Security and safety boundary

This repository is an educational tabletop prototype, not road infrastructure.

- The HTTP, MJPEG and WebSocket interfaces have no authentication or TLS. The backend binds to loopback by default. Use LAN binding only on an isolated trusted teaching network.
- Wi-Fi credentials, camera addresses and the backend LAN address belong in ignored local configuration, never in Git.
- `/health` proves only that the FastAPI process responds. `/api/runtime` reports observed frame freshness and WebSocket client counts; neither endpoint certifies cameras, inference, the physical controller, light outputs, traffic optimization or road safety.
- A connected WebSocket client is not proof that a physical ESP32, LED or OLED is healthy. The current protocol has no authenticated device identity, command acknowledgement or light-state feedback.
- The ESP32 main firmware requests all-red when its WebSocket disconnects. This is a source-confirmed prototype behavior, not a certified safety mechanism. There is no hardware interlock, conflict monitor, watchdog relay or redundant controller.
- Do not expose the services to the public Internet and do not deploy this software to real road traffic.

Please report a vulnerability through GitHub's private security advisory feature rather than a public issue when possible. Do not include credentials or private network details in a report.
