# Deployment and simulation

## Safe local simulation

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements-dev.txt
python simulator/fake_cam.py
```

In another terminal, from `backend/`:

```bash
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then start the frontend:

```bash
cd frontend
npm ci
npm run dev
```

The synthetic camera streams help exercise transport and UI plumbing. They are not labeled vehicle detections and are not hardware evidence. Running the full backend also requires a locally obtained YOLO weight as described in [MODEL_SETUP.md](MODEL_SETUP.md).

To observe device messages without an ESP32:

```bash
python simulator/fake_mcu.py --uri ws://127.0.0.1:8000/ws/device
```

## Real trusted-LAN setup

1. Copy `backend/.env.example` to ignored `backend/.env` and replace simulator URLs with the actual camera endpoints.
2. Keep backend binding on loopback for same-machine use. Opt into a LAN bind only when another physical device must connect, and limit it with a firewall on an isolated trusted network.
3. Supply Wi-Fi credentials and real backend/camera addresses through untracked PlatformIO build configuration or environment flags; never edit them into committed source.
4. Build and flash N/S/E/W cameras and the main controller, then follow the exact-commit checklist in [VERIFICATION.md](VERIFICATION.md).

The protocol has no authentication or TLS. Do not publish the backend, camera streams or WebSockets to the Internet. Never connect this prototype to real road signals.
