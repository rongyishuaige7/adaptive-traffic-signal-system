#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d /tmp/adaptive-traffic-verify.XXXXXX)"
CACHE="$(mktemp -d /tmp/adaptive-traffic-pycache.XXXXXX)"
cleanup(){ rm -rf -- "$WORK" "$CACHE"; }
trap cleanup EXIT

if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 && [[ -n "$(git -C "$ROOT" ls-files)" ]]; then
  git -C "$ROOT" archive HEAD | tar -x -C "$WORK"
else
  tar -C "$ROOT" --exclude=.git --exclude=.pio --exclude=node_modules --exclude=dist --exclude=.venv --exclude=__pycache__ -cf - . | tar -x -C "$WORK"
fi

export PYTHONPYCACHEPREFIX="$CACHE"
python3 "$WORK/scripts/secret_scan.py" --root "$WORK"
python3 "$WORK/scripts/check_repo.py" --root "$WORK"
python3 -m py_compile "$WORK"/backend/app/*.py "$WORK"/backend/app/api/*.py "$WORK"/backend/app/control/*.py "$WORK"/backend/app/video/*.py "$WORK"/simulator/*.py "$WORK"/tests/*.py
(cd "$WORK" && VIDEO_WORKERS_ENABLED=false SIGNAL_ENGINE_ENABLED=false python3 -m pytest tests -q)
(cd "$WORK/frontend" && npm ci --no-audit --no-fund && npm run build)
PLATFORMIO_BUILD_FLAGS='-DWIFI_SSID=\"CI_TEST_SSID\" -DWIFI_PASS=\"CI_TEST_PASSWORD\"' pio run -d "$WORK/firmware/esp32_cam"
PLATFORMIO_BUILD_FLAGS='-DWIFI_SSID=\"CI_TEST_SSID\" -DWIFI_PASS=\"CI_TEST_PASSWORD\" -DPC_HOST=\"127.0.0.1\"' pio run -d "$WORK/firmware/esp32_main"

echo "Verification: PASS"
