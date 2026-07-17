"""YOLOv8 + ByteTrack per frame."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from ultralytics import YOLO

log = logging.getLogger(__name__)

PALETTE: tuple[tuple[int, int, int], ...] = (
    (222, 82, 175),
    (0, 204, 255),
    (0, 149, 255),
    (85, 45, 255),
)


@dataclass(frozen=True)
class Track:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


def _color_for_class(class_id: int) -> tuple[int, int, int]:
    return PALETTE[class_id % len(PALETTE)]


def annotate_and_tracks(
    model: "YOLO",
    frame_bgr: np.ndarray,
    *,
    classes: tuple[int, ...],
    line_y: int,
    conf: float,
    iou: float,
    imgsz: int,
    tracker: str,
    device: str,
) -> tuple[np.ndarray, list[Track]]:
    """
    Run tracking on frame; draw boxes + line; return tracks
    with track id, class, confidence and box coordinates.
    """
    results = model.track(
        frame_bgr,
        persist=True,
        verbose=False,
        classes=list(classes),
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        tracker=tracker,
        device=device,
    )
    tracks: list[Track] = []
    out = frame_bgr.copy()
    h, w = out.shape[:2]
    cv2.line(out, (0, line_y), (w, line_y), (0, 255, 255), 2)

    if not results:
        return out, tracks

    r0 = results[0]
    if r0.boxes is None or len(r0.boxes) == 0:
        return out, tracks

    xyxy = r0.boxes.xyxy.cpu().numpy()
    ids = r0.boxes.id
    if ids is None:
        return out, tracks
    ids_np = ids.cpu().numpy().astype(int)
    cls_np = r0.boxes.cls.cpu().numpy().astype(int)
    conf_np = r0.boxes.conf.cpu().numpy()
    names = getattr(model, "names", {}) or {}

    for (x1, y1, x2, y2), tid, class_id, score in zip(xyxy, ids_np, cls_np, conf_np):
        class_name = str(names.get(int(class_id), int(class_id)))
        track = Track(
            track_id=int(tid),
            class_id=int(class_id),
            class_name=class_name,
            confidence=float(score),
            x1=float(x1),
            y1=float(y1),
            x2=float(x2),
            y2=float(y2),
        )
        tracks.append(track)
        color = _color_for_class(track.class_id)
        label = f"#{track.track_id} {track.class_name} {track.confidence:.2f}"
        cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.putText(
            out,
            label,
            (int(x1), int(y1) - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )

    return out, tracks


def draw_traffic_overlay(frame_bgr: np.ndarray, snapshot: dict) -> np.ndarray:
    out = frame_bgr
    flow = int(snapshot.get("flow_per_min", 0))
    total = int(snapshot.get("total", 0))
    up = int(snapshot.get("counts_by_direction", {}).get("up", 0))
    down = int(snapshot.get("counts_by_direction", {}).get("down", 0))
    active = int(snapshot.get("active_tracks", 0))
    processing_fps = float(snapshot.get("processing_fps", 0.0))
    lines = [
        f"flow: {flow}/min",
        f"total: {total}  up: {up}  down: {down}",
        f"active: {active}  fps: {processing_fps:.1f}",
    ]
    by_class = snapshot.get("counts_by_class", {})
    if isinstance(by_class, dict) and by_class:
        class_text = "  ".join(f"{k}:{v}" for k, v in sorted(by_class.items()))
        lines.append(class_text[:54])

    pad = 8
    line_h = 22
    width = 360
    height = pad * 2 + line_h * len(lines)
    overlay = out.copy()
    cv2.rectangle(overlay, (8, 8), (8 + width, 8 + height), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.62, out, 0.38, 0, out)
    for idx, text in enumerate(lines):
        cv2.putText(
            out,
            text,
            (8 + pad, 8 + pad + 16 + idx * line_h),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (245, 245, 245),
            1,
            cv2.LINE_AA,
        )
    return out


def bgr_to_jpeg(frame_bgr: np.ndarray, quality: int = 75) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("jpeg encode failed")
    return buf.tobytes()
