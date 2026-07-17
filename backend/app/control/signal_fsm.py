"""Two-phase traffic signal async loop."""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

from app.config import settings
from app.control.adaptive import compute_green
from app.control.ws_hub import ws_hub
from app.video.shared_state import shared_state

log = logging.getLogger(__name__)

TICK_S = 0.2


class SignalEngine:
    def __init__(self) -> None:
        self.phase = "NS_GREEN"
        self.remain_s = float(settings.green_min_s)
        self.total_s = settings.green_min_s
        self.green_ns_next = settings.green_min_s
        self.green_ew_next = settings.green_min_s
        self._task: asyncio.Task[Any] | None = None

    def payload(self) -> dict[str, Any]:
        flow = shared_state.flow_snapshot()
        return {
            "type": "state",
            "phase": self.phase,
            "remain_s": max(0, int(math.ceil(self.remain_s - 1e-6))),
            "total_s": int(self.total_s),
            "yellow_s": settings.yellow_seconds,
            "flow_per_min": flow,
            "traffic": shared_state.traffic_snapshot(),
            "ws_clients": ws_hub.counts_snapshot(),
            "green_ns_next": self.green_ns_next,
            "green_ew_next": self.green_ew_next,
        }

    async def _wait_countdown(self, seconds: float) -> None:
        self.remain_s = float(seconds)
        self.total_s = int(math.ceil(seconds))
        while self.remain_s > 0:
            await ws_hub.broadcast_state(self.payload())
            await asyncio.sleep(TICK_S)
            self.remain_s -= TICK_S
        await ws_hub.broadcast_state(self.payload())

    async def run_forever(self) -> None:
        log.info("SignalEngine started")
        while True:
            flow = shared_state.flow_snapshot()
            ns_flow = int(flow.get("N", 0) + flow.get("S", 0))
            ew_flow = int(flow.get("E", 0) + flow.get("W", 0))
            self.green_ns_next = compute_green(ns_flow)
            self.green_ew_next = compute_green(ew_flow)

            self.phase = "NS_GREEN"
            await self._wait_countdown(float(self.green_ns_next))

            self.phase = "NS_YELLOW"
            await self._wait_countdown(float(settings.yellow_seconds))

            flow = shared_state.flow_snapshot()
            ns_flow = int(flow.get("N", 0) + flow.get("S", 0))
            ew_flow = int(flow.get("E", 0) + flow.get("W", 0))
            self.green_ns_next = compute_green(ns_flow)
            self.green_ew_next = compute_green(ew_flow)

            self.phase = "EW_GREEN"
            await self._wait_countdown(float(self.green_ew_next))

            self.phase = "EW_YELLOW"
            await self._wait_countdown(float(settings.yellow_seconds))


signal_engine = SignalEngine()


def start_signal_task() -> asyncio.Task[Any]:
    if signal_engine._task and not signal_engine._task.done():
        return signal_engine._task
    signal_engine._task = asyncio.create_task(signal_engine.run_forever(), name="signal_fsm")
    return signal_engine._task
