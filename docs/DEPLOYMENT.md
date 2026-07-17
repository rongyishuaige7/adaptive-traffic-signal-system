# 部署与模拟

## 安全的本地模拟

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements-dev.txt
python simulator/fake_cam.py
```

在另一个终端进入 `backend/`：

```bash
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

然后启动前端：

```bash
cd frontend
npm ci
npm run dev
```

合成摄像头用于验证传输和界面链路，它不包含已标注车辆，也不能作为硬件证据。完整后端还需要按 [MODEL_SETUP.md](MODEL_SETUP.md) 在本地提供 YOLO 权重。

如需在没有 ESP32 的情况下观察设备消息：

```bash
python simulator/fake_mcu.py --uri ws://127.0.0.1:8000/ws/device
```

## 可信局域网真机联调

1. 将 `backend/.env.example` 复制为被忽略的 `backend/.env`，再把模拟地址替换为真实摄像头端点；
2. 同机使用时继续让后端绑定本机。只有其他实体设备确实需要连接时才启用局域网绑定，并通过防火墙限制在隔离可信网络；
3. 通过未跟踪的 PlatformIO 本地配置或环境构建参数提供 Wi-Fi 凭据及真实后端 / 摄像头地址，绝不能写入已提交源码；
4. 分别构建并烧录东南西北四路摄像头和主控制器，再按 [VERIFICATION.md](VERIFICATION.md) 对精确提交执行真机检查清单。

当前协议没有认证和 TLS。不要把后端、摄像头流或 WebSocket 暴露到公网，也绝不能连接真实道路信号灯。
