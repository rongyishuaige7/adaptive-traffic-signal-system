#!/usr/bin/env python3
"""Simulate ESP32 main: connect to FastAPI /ws/device and render lights + OLED in terminal."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import websockets
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()


def render_panel(payload: dict) -> Panel:
    phase = payload.get("phase", "?")
    rem = payload.get("remain_s", 0)
    tot = payload.get("total_s", 0)
    flow = payload.get("flow_per_min", {})
    n, s, e, w = flow.get("N", 0), flow.get("S", 0), flow.get("E", 0), flow.get("W", 0)

    def tri(label: str) -> Text:
        t = Text()
        t.append(f"{label}\n", style="bold white")
        if phase.startswith("NS") and label in ("N", "S"):
            if "YELLOW" in phase:
                t.append(" ● YELLOW\n", style="bold yellow")
                t.append(" ○ RED\n", style="dim")
                t.append(" ○ GREEN\n", style="dim")
            else:
                t.append(" ○ YELLOW\n", style="dim")
                t.append(" ○ RED\n", style="dim")
                t.append(" ● GREEN\n", style="bold green")
        elif phase.startswith("EW") and label in ("E", "W"):
            if "YELLOW" in phase:
                t.append(" ● YELLOW\n", style="bold yellow")
                t.append(" ○ RED\n", style="dim")
                t.append(" ○ GREEN\n", style="dim")
            else:
                t.append(" ○ YELLOW\n", style="dim")
                t.append(" ○ RED\n", style="dim")
                t.append(" ● GREEN\n", style="bold green")
        else:
            t.append(" ○ YELLOW\n", style="dim")
            t.append(" ● RED\n", style="bold red")
            t.append(" ○ GREEN\n", style="dim")
        return t

    north = tri("N")
    south = tri("S")
    east = tri("E")
    west = tri("W")

    oled = Text()
    oled.append("OLED 128x32\n", style="cyan")
    oled.append(f"{phase} {rem}s/{tot}s\n", style="white")
    oled.append(f"rpm N{n} S{s} E{e} W{w}\n", style="dim")

    grid = Text()
    grid.append("        N\n", style="white")
    grid.append_text(north)
    grid.append("\n")
    row = Text()
    row.append_text(west)
    row.append("   +   ", style="bold white")
    row.append_text(east)
    grid.append_text(row)
    grid.append("\n")
    grid.append_text(south)
    grid.append("\n        S\n", style="white")

    body = Text()
    body.append_text(grid)
    body.append("\n")
    body.append_text(oled)
    return Panel(body, title="fake_mcu", border_style="green")


async def run_client(uri: str) -> None:
    last: dict = {"type": "state", "phase": "BOOT", "remain_s": 0, "total_s": 0}
    with Live(render_panel(last), refresh_per_second=8, console=console) as live:
        try:
            async with websockets.connect(uri) as ws:
                while True:
                    raw = await ws.recv()
                    if isinstance(raw, bytes):
                        continue
                    data = json.loads(raw)
                    if data.get("type") == "state":
                        last = data
                        live.update(render_panel(last))
        except websockets.exceptions.ConnectionClosed:
            console.print("[red]disconnected[/red]")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uri", default="ws://127.0.0.1:8000/ws/device")
    args = p.parse_args()
    try:
        asyncio.run(run_client(args.uri))
    except KeyboardInterrupt:
        print("bye")


if __name__ == "__main__":
    main()
    sys.exit(0)
