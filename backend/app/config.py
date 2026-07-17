"""Application settings loaded from environment variables and an optional local .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Loopback simulator endpoints are safe defaults. Real camera addresses belong in .env.
    cam_url_n: str = "http://127.0.0.1:8181/stream"
    cam_url_s: str = "http://127.0.0.1:8182/stream"
    cam_url_e: str = "http://127.0.0.1:8183/stream"
    cam_url_w: str = "http://127.0.0.1:8184/stream"

    # Ultralytics can resolve a model name on first use. Model weights are never committed.
    yolo_model: str = "yolov8n.pt"
    yolo_conf: float = 0.35
    yolo_iou: float = 0.45
    yolo_imgsz: int = 416
    yolo_tracker: str = "bytetrack.yaml"
    yolo_device: str = "cpu"
    yolo_infer_fps: float = 4.0
    yolo_jpeg_quality: int = 68
    vehicle_classes: tuple[int, ...] = (2, 3, 5, 7)
    vehicle_line_ratio: float = 0.6
    vehicle_count_direction: str = "both"

    yellow_seconds: int = 3
    green_min_s: int = 10
    green_max_s: int = 40
    green_k: float = 0.6
    stream_fps: float = 5.0
    flow_window_s: float = 60.0

    # Startup switches make hardware-free contract testing possible without model downloads.
    video_workers_enabled: bool = True
    signal_engine_enabled: bool = True
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    host: str = "127.0.0.1"
    port: int = 8000

    def allowed_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


settings = Settings()
