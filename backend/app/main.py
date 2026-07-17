"""FastAPI entry: video workers + signal FSM + routes."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_status import router as status_router
from app.api.routes_video import router as video_router
from app.api.routes_ws import router as ws_router
from app.config import settings
from app.control.signal_fsm import start_signal_task
from app.video.worker import run_direction_worker

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_workers: list[threading.Thread] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.video_workers_enabled:
        Path("models").mkdir(parents=True, exist_ok=True)
        model_path = settings.yolo_model
        log.info("Starting video workers with YOLO model=%s", model_path)
        for d in ("N", "S", "E", "W"):
            t = threading.Thread(
                target=run_direction_worker,
                args=(d, model_path),
                name=f"video-{d}",
                daemon=True,
            )
            t.start()
            _workers.append(t)
    else:
        log.info("Video workers disabled by configuration")

    if settings.signal_engine_enabled:
        start_signal_task()
    yield
    log.info("Shutdown (workers are daemon threads)")


app = FastAPI(title="Traffic Adaptive Signal", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router)
app.include_router(video_router)
app.include_router(ws_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness only: this does not assert camera, model, device, or light health."""
    return {"service": "responding", "scope": "process_liveness_only"}
