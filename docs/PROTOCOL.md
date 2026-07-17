# WebSocket 与状态契约

## UI WebSocket

- 端点：`/ws/ui`
- 服务端到 UI：重复发送 `state` JSON
- 当前后端忽略客户端消息

## 设备 WebSocket

- 端点：`/ws/device`
- 服务端到设备：发送相同的 `state` JSON
- 设备到服务端：当前固件会发送心跳 JSON 供调试，但不会被当作已认证 ACK

状态示例：

```json
{
  "type": "state",
  "phase": "NS_GREEN",
  "remain_s": 8,
  "total_s": 10,
  "yellow_s": 3,
  "flow_per_min": {"N": 0, "S": 0, "E": 0, "W": 0},
  "traffic": {},
  "ws_clients": {"ui": 1, "device": 0},
  "green_ns_next": 10,
  "green_ew_next": 10
}
```

`ws_clients.device > 0` 只表示存在一个或多个 WebSocket 连接；它不能证明客户端身份、ESP32 已正确启动、JSON 已执行、LED 已变化、OLED 已更新或系统处于安全信号状态。

## HTTP 事实

| 端点 | 准确含义 |
|:--|:--|
| `GET /health` | 只表示 FastAPI 进程存活并响应 |
| `GET /api/status` | 当前进程内状态机载荷与已观察计数 |
| `GET /api/runtime` | 配置开关、各方向近期视频帧事实与 WebSocket 连接数量 |
| `GET /api/traffic` | 各方向最新的内存计数快照 |
| `GET /api/video/{N,S,E,W}.mjpg` | 标注视频流，或明确的等待占位图 |

本教学协议没有认证、TLS、设备身份、消息签名、防重放、命令确认或实体反馈。
