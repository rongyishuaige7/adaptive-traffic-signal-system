from __future__ import annotations

import cv2
import numpy as np

from simulator.fake_cam import _synthetic_frame
from simulator.fake_mcu import render_panel


def test_fake_camera_produces_decodable_jpeg() -> None:
    jpeg = _synthetic_frame(3, 320, 240)
    frame = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert frame is not None
    assert frame.shape == (240, 320, 3)


def test_fake_mcu_accepts_state_payload() -> None:
    panel = render_panel({
        "type": "state",
        "phase": "EW_YELLOW",
        "remain_s": 2,
        "total_s": 3,
        "flow_per_min": {"N": 1, "S": 2, "E": 3, "W": 4},
    })
    assert panel.title == "fake_mcu"
