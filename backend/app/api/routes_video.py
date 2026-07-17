"""MJPEG re-stream of annotated frames."""

from __future__ import annotations

import asyncio

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.video.shared_state import normalize_direction, shared_state

router = APIRouter(prefix="/api", tags=["video"])

BOUNDARY = b"trafficframe"

_blank_jpeg: bytes | None = None


def _placeholder_jpeg() -> bytes:
    global _blank_jpeg
    if _blank_jpeg is None:
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.putText(
            img,
            "waiting for stream",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (200, 200, 200),
            2,
            cv2.LINE_AA,
        )
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        _blank_jpeg = buf.tobytes() if ok else b""
    return _blank_jpeg or b""


async def _mjpeg_chunk(direction: str) -> bytes:
    jpg = shared_state.get_jpeg(direction)
    if not jpg:
        jpg = _placeholder_jpeg()
    header = (
        b"--" + BOUNDARY + b"\r\n"
        b"Content-Type: image/jpeg\r\n"
        + f"Content-Length: {len(jpg)}\r\n\r\n".encode()
        + jpg
        + b"\r\n"
    )
    return header


async def mjpeg_stream(direction: str):
    d = normalize_direction(direction)
    if d is None:
        raise ValueError(f"invalid direction: {direction}")
    delay = 1.0 / max(1.0, settings.stream_fps)
    while True:
        chunk = await _mjpeg_chunk(d)
        yield chunk
        await asyncio.sleep(delay)


@router.get("/video/{direction}.mjpg")
async def video_mjpg(direction: str):
    if normalize_direction(direction) is None:
        raise HTTPException(status_code=404, detail="direction must be N, S, E or W")
    ct = f"multipart/x-mixed-replace; boundary={BOUNDARY.decode()}"
    return StreamingResponse(mjpeg_stream(direction), media_type=ct)
