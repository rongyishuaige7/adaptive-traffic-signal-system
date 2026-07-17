"""Linear mapping from aggregate flow (vehicles/min) to green time."""

from __future__ import annotations

from app.config import settings


def compute_green(flow_rpm: int) -> int:
    """Map flow to green seconds in [green_min_s, green_max_s]."""
    gmin = settings.green_min_s
    gmax = settings.green_max_s
    k = settings.green_k
    raw = gmin + float(flow_rpm) * k
    return int(max(gmin, min(gmax, round(raw))))
