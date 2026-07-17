"""Per-direction video worker thread."""

from __future__ import annotations

import logging
import time
from typing import Literal

import cv2
import numpy as np

from app.config import settings
from app.video.counter import LineCounter
from app.video.detector import annotate_and_tracks, bgr_to_jpeg, draw_traffic_overlay
from app.video.mjpeg_reader import iter_jpeg_frames
from app.video.shared_state import shared_state

log = logging.getLogger(__name__)

Direction = Literal["N", "S", "E", "W"]


def _cam_url(direction: Direction) -> str:
    return {
        "N": settings.cam_url_n,
        "S": settings.cam_url_s,
        "E": settings.cam_url_e,
        "W": settings.cam_url_w,
    }[direction]


def run_direction_worker(direction: Direction, model_path: str) -> None:
    from ultralytics import YOLO

    infer_interval_s = 1.0 / max(0.1, settings.yolo_infer_fps)
    next_infer_at = 0.0
    last_done_at = 0.0
    processing_fps = 0.0
    counter = LineCounter(
        line_ratio=settings.vehicle_line_ratio,
        window_s=settings.flow_window_s,
        count_direction=settings.vehicle_count_direction,
    )
    log.info("Worker %s loading YOLO model=%s", direction, model_path)
    model = YOLO(model_path)
    model.to(settings.yolo_device)
    log.info("Worker %s starting, url=%s", direction, _cam_url(direction))
    while True:
        try:
            for jpeg in iter_jpeg_frames(_cam_url(direction)):
                arr = np.frombuffer(jpeg, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                now = time.monotonic()
                if now < next_infer_at:
                    continue
                next_infer_at = now + infer_interval_s
                h, w = frame.shape[:2]
                line_y = int(counter.line_ratio * h)
                annotated, tracks = annotate_and_tracks(
                    model,
                    frame,
                    classes=settings.vehicle_classes,
                    line_y=line_y,
                    conf=settings.yolo_conf,
                    iou=settings.yolo_iou,
                    imgsz=settings.yolo_imgsz,
                    tracker=settings.yolo_tracker,
                    device=settings.yolo_device,
                )
                counter.update(tracks, h, w)
                snapshot = counter.snapshot()
                done_at = time.monotonic()
                if last_done_at > 0:
                    instant_fps = 1.0 / max(1e-6, done_at - last_done_at)
                    processing_fps = (
                        instant_fps if processing_fps == 0.0 else processing_fps * 0.8 + instant_fps * 0.2
                    )
                last_done_at = done_at
                snapshot["processing_fps"] = round(processing_fps, 2)
                snapshot["target_infer_fps"] = float(settings.yolo_infer_fps)
                annotated = draw_traffic_overlay(annotated, snapshot)
                jpg_out = bgr_to_jpeg(annotated, quality=settings.yolo_jpeg_quality)
                shared_state.set_traffic(direction, snapshot)
                shared_state.set_jpeg(direction, jpg_out)
        except Exception as e:
            log.exception("Worker %s error: %s — retry in 2s", direction, e)
            time.sleep(2.0)
