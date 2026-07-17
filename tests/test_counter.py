from __future__ import annotations

from app.video.counter import LineCounter
from app.video.detector import Track


def track(track_id: int, bottom: float, name: str = "car") -> Track:
    return Track(track_id, 2, name, 0.9, 10, bottom - 20, 30, bottom)


def test_line_counter_counts_each_active_track_once() -> None:
    counter = LineCounter(line_ratio=0.5, window_s=60, count_direction="both")
    assert counter.update([track(7, 40)], 100, 100) == 0
    assert counter.update([track(7, 60)], 100, 100) == 1
    assert counter.update([track(7, 40)], 100, 100) == 0
    snapshot = counter.snapshot()
    assert snapshot["total"] == 1
    assert snapshot["counts_by_direction"] == {"up": 0, "down": 1}
    assert snapshot["counts_by_class"] == {"car": 1}


def test_line_counter_direction_filter_and_id_reuse_after_disappearance() -> None:
    counter = LineCounter(line_ratio=0.5, count_direction="up")
    counter.update([track(1, 60)], 100, 100)
    assert counter.update([track(1, 40)], 100, 100) == 1
    counter.update([], 100, 100)
    counter.update([track(1, 60)], 100, 100)
    assert counter.update([track(1, 40)], 100, 100) == 1
    assert counter.snapshot()["counts_by_direction"]["up"] == 2


def test_invalid_count_direction_normalizes_to_both() -> None:
    assert LineCounter(count_direction="sideways").count_direction == "both"
