"""Broadcast JSON state to UI + device WebSocket clients."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

log = logging.getLogger(__name__)


class WSHub:
    def __init__(self) -> None:
        self._ui: set[WebSocket] = set()
        self._device: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register_ui(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._ui.add(ws)
            ui_count = len(self._ui)
            device_count = len(self._device)
        log.info("UI WS connected: ui=%s device=%s", ui_count, device_count)

    async def register_device(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._device.add(ws)
            ui_count = len(self._ui)
            device_count = len(self._device)
        log.info("Device WS connected: ui=%s device=%s", ui_count, device_count)

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            self._ui.discard(ws)
            self._device.discard(ws)
            ui_count = len(self._ui)
            device_count = len(self._device)
        log.info("WS disconnected: ui=%s device=%s", ui_count, device_count)

    async def counts(self) -> dict[str, int]:
        async with self._lock:
            return {"ui": len(self._ui), "device": len(self._device)}

    def counts_snapshot(self) -> dict[str, int]:
        return {"ui": len(self._ui), "device": len(self._device)}

    async def broadcast_state(self, payload: dict[str, Any]) -> None:
        text = __import__("json").dumps(payload)
        async with self._lock:
            targets = list(self._ui) + list(self._device)
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._ui.discard(ws)
                    self._device.discard(ws)


ws_hub = WSHub()
