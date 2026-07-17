from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("VIDEO_WORKERS_ENABLED", "false")
os.environ.setdefault("SIGNAL_ENGINE_ENABLED", "false")
