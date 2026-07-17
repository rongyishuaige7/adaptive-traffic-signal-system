from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.config import settings
from app.control.adaptive import compute_green
from app.control.signal_fsm import signal_engine
from app.control.ws_hub import ws_hub
from app.main import app
from app.video.shared_state import SharedState, normalize_direction


def test_safe_defaults_use_loopback_and_narrow_cors() -> None:
    assert settings.host == "127.0.0.1"
    assert settings.cam_url_n.startswith("http://127.0.0.1:")
    assert "*" not in settings.allowed_origins()
    assert settings.video_workers_enabled is False


def test_compute_green_clamps_and_rounds() -> None:
    assert compute_green(-99) == settings.green_min_s
    assert compute_green(0) == settings.green_min_s
    assert compute_green(5) == settings.green_min_s + round(5 * settings.green_k)
    assert compute_green(100000) == settings.green_max_s


def test_direction_normalization_fails_closed() -> None:
    assert normalize_direction("n.mjpg") == "N"
    assert normalize_direction(" W ") == "W"
    assert normalize_direction("north") is None
    assert normalize_direction("../N") is None


def test_stream_facts_never_treat_missing_frame_as_healthy() -> None:
    state = SharedState()
    before = state.stream_snapshot(stale_after_s=0.01)
    assert before["N"] == {
        "frame_received": False,
        "fresh": False,
        "last_frame_age_s": None,
    }
    state.set_jpeg("N", b"jpeg")
    assert state.stream_snapshot(stale_after_s=1.0)["N"]["fresh"] is True
    time.sleep(0.02)
    assert state.stream_snapshot(stale_after_s=0.001)["N"]["fresh"] is False


def test_liveness_and_runtime_are_narrow_facts() -> None:
    with TestClient(app) as client:
        liveness = client.get("/health")
        assert liveness.status_code == 200
        assert liveness.json() == {
            "service": "responding",
            "scope": "process_liveness_only",
        }
        runtime = client.get("/api/runtime").json()
        assert runtime["service"] == "responding"
        assert runtime["video_workers_enabled"] is False
        assert all(not row["fresh"] for row in runtime["streams"].values())
        assert client.get("/api/video/NORTH.mjpg").status_code == 404


def test_state_payload_exposes_real_websocket_client_counts() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws/ui"):
            deadline = time.time() + 1.0
            payload = signal_engine.payload()
            while payload["ws_clients"]["ui"] != 1 and time.time() < deadline:
                time.sleep(0.01)
                payload = signal_engine.payload()
            assert payload["type"] == "state"
            assert payload["ws_clients"]["ui"] == 1
            assert payload["ws_clients"]["device"] == 0
        assert ws_hub.counts_snapshot()["ui"] == 0
