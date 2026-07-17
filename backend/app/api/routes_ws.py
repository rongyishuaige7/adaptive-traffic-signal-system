from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.control.ws_hub import ws_hub

log = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/ui")
async def ws_ui(websocket: WebSocket) -> None:
    await ws_hub.register_ui(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        log.info("UI WS disconnected")
    finally:
        await ws_hub.unregister(websocket)


@router.websocket("/ws/device")
async def ws_device(websocket: WebSocket) -> None:
    await ws_hub.register_device(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            log.debug("device msg: %s", msg[:200])
    except WebSocketDisconnect:
        log.info("Device WS disconnected")
    finally:
        await ws_hub.unregister(websocket)
