from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.control.signal_fsm import signal_engine
from app.control.ws_hub import ws_hub
from app.video.shared_state import shared_state

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
def get_status() -> dict:
    return signal_engine.payload()


@router.get("/traffic")
def get_traffic() -> dict:
    return shared_state.traffic_snapshot()


@router.get("/runtime")
def get_runtime() -> dict:
    """Report observed process/stream/client facts without claiming system health."""
    return {
        "service": "responding",
        "video_workers_enabled": settings.video_workers_enabled,
        "signal_engine_enabled": settings.signal_engine_enabled,
        "streams": shared_state.stream_snapshot(),
        "ws_clients": ws_hub.counts_snapshot(),
    }
