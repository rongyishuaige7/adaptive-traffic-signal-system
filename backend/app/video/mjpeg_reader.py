"""Pull JPEG frames from multipart MJPEG HTTP stream."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Final

import requests

log = logging.getLogger(__name__)

JPEG_START: Final[bytes] = b"\xff\xd8"
JPEG_END: Final[bytes] = b"\xff\xd9"
_MAX_BUF: Final[int] = 2 * 1024 * 1024


def iter_jpeg_frames(url: str, *, timeout: float = 10.0, chunk_size: int = 4096) -> Iterator[bytes]:
    """Yield complete JPEG byte strings from a multipart/x-mixed-replace stream."""
    with requests.get(url, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        buf = b""
        for chunk in resp.iter_content(chunk_size):
            if not chunk:
                continue
            buf += chunk
            if len(buf) > _MAX_BUF:
                buf = buf[-_MAX_BUF // 2 :]
            while True:
                a = buf.find(JPEG_START)
                if a == -1:
                    buf = buf[-1:] if buf else b""
                    break
                b = buf.find(JPEG_END, a + 2)
                if b == -1:
                    buf = buf[a:]
                    break
                frame = buf[a : b + 2]
                buf = buf[b + 2 :]
                yield frame
