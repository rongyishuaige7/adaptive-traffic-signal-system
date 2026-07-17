# YOLO model setup

Model weights are intentionally not stored in Git.

The backend default is `YOLO_MODEL=yolov8n.pt`. With Ultralytics installed, first use may download the matching upstream weight into the local cache/current environment. You can instead set `YOLO_MODEL` in ignored `backend/.env` to a locally reviewed path.

Before downloading or redistributing weights:

1. review the current [Ultralytics license](https://www.ultralytics.com/license);
2. record the exact Ultralytics version, model filename, source URL and file hash used in an experiment;
3. keep weights out of commits and release assets unless their terms and provenance have been independently cleared;
4. do not treat an upstream pretrained model as evidence of accuracy on this tabletop scene.

CI uses mocked/hardware-free contracts and never downloads a weight file.
