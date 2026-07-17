"""Thread-safe latest JPEG, flow and last-frame facts for all directions."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

DIRECTIONS = ("N", "S", "E", "W")


def normalize_direction(value: str) -> str | None:
    direction = str(value).split(".")[0].strip().upper()
    return direction if direction in DIRECTIONS else None


def _empty_flow() -> dict[str, int]:
    return {direction: 0 for direction in DIRECTIONS}


def _empty_traffic() -> dict[str, dict]:
    return {
        direction: {
            "flow_per_min": 0,
            "total": 0,
            "counts_by_direction": {"up": 0, "down": 0},
            "counts_by_class": {},
            "active_tracks": 0,
            "processing_fps": 0.0,
            "target_infer_fps": 0.0,
            "frame_received": False,
            "last_frame_age_s": None,
        }
        for direction in DIRECTIONS
    }


@dataclass
class SharedState:
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _flow: dict[str, int] = field(default_factory=_empty_flow)
    _traffic: dict[str, dict] = field(default_factory=_empty_traffic)
    _jpeg: dict[str, bytes] = field(default_factory=dict)
    _last_frame_monotonic: dict[str, float] = field(default_factory=dict)

    def set_flow(self, direction: str, rpm: int) -> None:
        with self._lock:
            self._flow[direction] = int(rpm)

    def flow_snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._flow)

    def set_traffic(self, direction: str, snapshot: dict) -> None:
        with self._lock:
            self._traffic[direction] = dict(snapshot)
            self._flow[direction] = int(snapshot.get("flow_per_min", 0))

    def traffic_snapshot(self) -> dict[str, dict]:
        now = time.monotonic()
        with self._lock:
            result: dict[str, dict] = {}
            for direction, value in self._traffic.items():
                row = dict(value)
                last = self._last_frame_monotonic.get(direction)
                row["frame_received"] = last is not None
                row["last_frame_age_s"] = round(max(0.0, now - last), 2) if last is not None else None
                result[direction] = row
            return result

    def stream_snapshot(self, stale_after_s: float = 5.0) -> dict[str, dict]:
        now = time.monotonic()
        with self._lock:
            return {
                direction: {
                    "frame_received": (last := self._last_frame_monotonic.get(direction)) is not None,
                    "fresh": last is not None and now - last <= stale_after_s,
                    "last_frame_age_s": round(max(0.0, now - last), 2) if last is not None else None,
                }
                for direction in DIRECTIONS
            }

    def set_jpeg(self, direction: str, data: bytes) -> None:
        with self._lock:
            self._jpeg[direction] = data
            self._last_frame_monotonic[direction] = time.monotonic()

    def get_jpeg(self, direction: str) -> bytes | None:
        with self._lock:
            return self._jpeg.get(direction)


shared_state = SharedState()
