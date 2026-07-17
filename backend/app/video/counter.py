"""Virtual line crossing counter + vehicles/min rolling window."""

from __future__ import annotations

import time
from collections import deque
from collections import defaultdict
from typing import Literal

from app.video.detector import Track

CrossDirection = Literal["up", "down"]


class LineCounter:
    """
    Count a track_id once when its foot point (mid_x, bottom_y) crosses
    line_y from above to below (y increases downward in image).
    """

    def __init__(
        self,
        line_ratio: float = 0.6,
        window_s: float = 60.0,
        count_direction: str = "both",
    ) -> None:
        self.line_ratio = line_ratio
        self.window_s = window_s
        normalized_direction = count_direction.strip().lower()
        self.count_direction = (
            normalized_direction if normalized_direction in {"up", "down", "both"} else "both"
        )
        self._last_point: dict[int, tuple[float, float]] = {}
        self._seen_ids: set[int] = set()
        self._cross_times: deque[float] = deque()
        self._counts_by_class: dict[str, int] = defaultdict(int)
        self._counts_by_direction: dict[CrossDirection, int] = {"up": 0, "down": 0}
        self._active_tracks = 0

    def _trim(self, now: float) -> None:
        cutoff = now - self.window_s
        while self._cross_times and self._cross_times[0] < cutoff:
            self._cross_times.popleft()

    def vehicles_per_minute(self) -> int:
        now = time.monotonic()
        self._trim(now)
        if not self._cross_times:
            return 0
        # events in last window_s seconds scaled to per-minute
        return int(round(len(self._cross_times) * (60.0 / self.window_s)))

    def snapshot(self) -> dict:
        return {
            "flow_per_min": self.vehicles_per_minute(),
            "total": int(sum(self._counts_by_direction.values())),
            "window_s": float(self.window_s),
            "line_ratio": float(self.line_ratio),
            "count_direction": self.count_direction,
            "counts_by_direction": dict(self._counts_by_direction),
            "counts_by_class": dict(sorted(self._counts_by_class.items())),
            "active_tracks": int(self._active_tracks),
        }

    def _should_count(self, direction: CrossDirection) -> bool:
        return self.count_direction == "both" or self.count_direction == direction

    def update(
        self,
        tracks: list[Track],
        frame_h: int,
        frame_w: int,
    ) -> int:
        """
        tracks: tracked vehicle boxes in pixel coords.
        Returns number of new crossings this frame.
        """
        line_y = self.line_ratio * frame_h
        now = time.monotonic()
        self._trim(now)
        new_cross = 0
        active: set[int] = set()
        for track in tracks:
            tid = track.track_id
            active.add(tid)
            foot_x = float((track.x1 + track.x2) / 2.0)
            foot_y = float(track.y2)
            prev = self._last_point.get(tid)
            self._last_point[tid] = (foot_x, foot_y)
            if prev is None:
                continue
            prev_y = prev[1]
            direction: CrossDirection | None = None
            if prev_y < line_y <= foot_y:
                direction = "down"
            elif prev_y > line_y >= foot_y:
                direction = "up"
            if direction is None or not self._should_count(direction):
                continue
            if tid not in self._seen_ids:
                self._seen_ids.add(tid)
                self._cross_times.append(now)
                self._counts_by_direction[direction] += 1
                self._counts_by_class[track.class_name] += 1
                new_cross += 1
        self._active_tracks = len(active)
        # drop stale track ids to allow recount if same physical id wraps (best-effort)
        stale = [tid for tid in self._last_point if tid not in active]
        for tid in stale[:200]:
            self._last_point.pop(tid, None)
            self._seen_ids.discard(tid)
        return new_cross
