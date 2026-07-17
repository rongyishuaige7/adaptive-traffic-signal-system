#!/usr/bin/env python3
"""
Four MJPEG HTTP servers on ports 8181–8184 (paths /stream), compatible with backend CAM_URL_*.

Place optional videos at samples/N.mp4 … samples/W.mp4; otherwise synthetic frames are used.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import aiohttp.web
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"

BOUNDARY = b"frame"


def _synthetic_frame(seed: int, w: int = 640, h: int = 480) -> bytes:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    x = (seed * 17) % (w - 80)
    y = (seed * 23) % (h - 60)
    cv2.rectangle(img, (x, y), (x + 80, y + 40), (60, 120, 200), -1)
    cv2.putText(
        img,
        f"SYN-{seed % 1000}",
        (x + 4, y + 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
    return buf.tobytes() if ok else b""


def _produce_jpeg(
    direction: str, cap_holder: list[cv2.VideoCapture | None], counter: list[int]
) -> bytes:
    path = SAMPLES / f"{direction}.mp4"
    if cap_holder[0] is None and path.exists():
        cap = cv2.VideoCapture(str(path))
        cap_holder[0] = cap if cap.isOpened() else None
        if cap_holder[0] is None and cap is not None:
            cap.release()

    if cap_holder[0] is not None:
        ok, frame = cap_holder[0].read()
        if not ok:
            cap_holder[0].set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap_holder[0].read()
        if ok:
            ok2, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ok2:
                counter[0] += 1
                return buf.tobytes()
    counter[0] += 1
    return _synthetic_frame(counter[0])


def make_stream_handler(direction: str):
    cap_holder: list[cv2.VideoCapture | None] = [None]
    counter = [0]

    async def stream(request: aiohttp.web.Request) -> aiohttp.web.StreamResponse:
        resp = aiohttp.web.StreamResponse(
            status=200,
            headers={
                "Content-Type": f"multipart/x-mixed-replace; boundary={BOUNDARY.decode()}",
                "Cache-Control": "no-cache",
                "Connection": "close",
                "Access-Control-Allow-Origin": "*",
            },
        )
        await resp.prepare(request)

        try:
            while True:
                jpg = await asyncio.to_thread(
                    _produce_jpeg, direction, cap_holder, counter
                )
                part = (
                    b"--" + BOUNDARY + b"\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    + f"Content-Length: {len(jpg)}\r\n\r\n".encode()
                    + jpg
                    + b"\r\n"
                )
                await resp.write(part)
                await asyncio.sleep(1.0 / 12.0)
        finally:
            if cap_holder[0] is not None:
                cap_holder[0].release()
                cap_holder[0] = None
        return resp

    return stream


async def start_site(port: int, direction: str) -> aiohttp.web.AppRunner:
    app = aiohttp.web.Application()
    app.router.add_get("/stream", make_stream_handler(direction))
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    print(f"[fake_cam] {direction}: http://127.0.0.1:{port}/stream")
    return runner


async def main_async() -> None:
    tasks = [
        start_site(8181, "N"),
        start_site(8182, "S"),
        start_site(8183, "E"),
        start_site(8184, "W"),
    ]
    await asyncio.gather(*tasks)
    stop = asyncio.Event()
    await stop.wait()


def main() -> None:
    print("fake_cam: samples dir", SAMPLES)
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("bye")


if __name__ == "__main__":
    main()
    sys.exit(0)
