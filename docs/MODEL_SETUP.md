# YOLO 模型配置

模型权重有意不存入 Git。

后端默认使用 `YOLO_MODEL=yolov8n.pt`。安装 Ultralytics 后，首次使用可能会将对应上游权重下载到本地缓存或当前环境；也可以在被忽略的 `backend/.env` 中把 `YOLO_MODEL` 指向本地已核验文件。

下载或再分发权重前：

1. 核对当前 [Ultralytics 许可证](https://www.ultralytics.com/license)；
2. 记录实验所用 Ultralytics 精确版本、模型文件名、来源 URL 与文件哈希；
3. 除非许可和来源已经独立核清，否则不要把权重提交到 Git 或 Release；
4. 不要把上游预训练模型当成本桌面场景检测准确率的证据。

CI 只运行模拟与硬件无关的契约，不会下载权重文件。
