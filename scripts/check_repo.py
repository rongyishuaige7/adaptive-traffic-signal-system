#!/usr/bin/env python3
"""Repository release checks that require no model download or hardware."""
from __future__ import annotations
import argparse,csv,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
REQUIRED=[".github/workflows/validate.yml",".gitignore",".markdownlint-cli2.jsonc","HARDWARE.md","LICENSE","Makefile","README.md","SECURITY.md","THIRD_PARTY_NOTICES.md","backend/.env.example","backend/app/main.py","backend/requirements-ci.txt","docs/DEPLOYMENT.md","docs/GITHUB_METADATA.md","docs/HARDWARE_LAB_CARD.md","docs/MODEL_SETUP.md","docs/PROJECT_STATUS.md","docs/PROTOCOL.md","docs/SOURCE_PROVENANCE.md","docs/VERIFICATION.md","firmware/esp32_cam/local-config.example.ini","firmware/esp32_main/local-config.example.ini","frontend/package-lock.json","hardware/BOM.csv","hardware/wiring-diagram.svg","scripts/secret_scan.py","scripts/verify.sh","simulator/fake_cam.py","simulator/fake_mcu.py","tests/test_backend_contracts.py","tests/test_counter.py","tests/test_simulator.py"]
CHINESE_DOCS=["README.md","HARDWARE.md","SECURITY.md","THIRD_PARTY_NOTICES.md","docs/DEPLOYMENT.md","docs/GITHUB_METADATA.md","docs/HARDWARE_LAB_CARD.md","docs/MODEL_SETUP.md","docs/PROJECT_STATUS.md","docs/PROTOCOL.md","docs/SOURCE_PROVENANCE.md","docs/VERIFICATION.md"]
FORBIDDEN_NAMES={".env","yolov8n.pt","yolov8l.pt","local-config.ini","id_rsa","id_ed25519"}
FORBIDDEN_DIRS={"__pycache__",".venv","venv","build","node_modules","dist",".pio",".vscode"}
FORBIDDEN_SUFFIXES={".pyc",".pyo",".pt",".bin",".elf",".zip",".7z",".db",".sqlite"}
MAX=5*1024*1024
def files(root):
 try:raw=subprocess.run(["git","-C",str(root),"ls-files","-z"],check=True,capture_output=True).stdout
 except (subprocess.CalledProcessError,FileNotFoundError):raw=b""
 if raw:return [root/x.decode("utf-8","surrogateescape") for x in raw.split(b"\0") if x]
 return sorted(p for p in root.rglob("*") if p.is_file() and not any(x in {".git","__pycache__","node_modules","dist",".pio"} for x in p.parts))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");root=Path(ap.parse_args().root).resolve();err=[]
 for rel in REQUIRED:
  if not (root/rel).is_file():err.append(f"missing required file: {rel}")
 checked=files(root)
 for p in checked:
  rel=p.relative_to(root)
  if p.name in FORBIDDEN_NAMES:err.append(f"forbidden local/generated file: {rel}")
  if any(x in FORBIDDEN_DIRS for x in rel.parts):err.append(f"forbidden generated directory: {rel}")
  if p.suffix.lower() in FORBIDDEN_SUFFIXES:err.append(f"forbidden generated artifact: {rel}")
  if p.stat().st_size>MAX:err.append(f"file exceeds 5 MiB: {rel}")
 contracts={
  "README.md":["当前五板硬件与端到端链路尚未重新真机复测","本项目绝不能用于控制真实道路信号灯","占位图始终明确表示 `no fresh frame`"],
  "docs/PROJECT_STATUS.md":["前端构建通过","当前五板硬件与端到端链路尚未重新真机复测"],
  "docs/SOURCE_PROVENANCE.md":["df48d6619b8558c23917f8735d54b4e7d19cb891f112edebd42314d74ec19e09","基于esp32s3交通摄像","backend/.env"],
  "backend/app/config.py":["127.0.0.1:8181","host: str = \"127.0.0.1\""],
  "backend/app/main.py":["process_liveness_only","allow_origins=settings.allowed_origins()"],
  "firmware/esp32_main/src/main.cpp":["WiFi/PC host not configured","digitalWrite(PIN_N_R, HIGH)"],
 }
 for rel,values in contracts.items():
  p=root/rel
  if p.is_file():
   text=p.read_text(encoding="utf-8")
   for value in values:
    if value not in text:err.append(f"fact contract missing in {rel}: {value}")
 for rel in CHINESE_DOCS:
  p=root/rel
  if p.is_file() and not any("\u4e00" <= ch <= "\u9fff" for ch in p.read_text(encoding="utf-8")):
   err.append(f"public documentation must retain a Chinese primary narrative: {rel}")
 claims=["system online","road safe","road-safe: pass","current hardware verified","four cameras online","traffic optimization verified","vehicle detection accuracy verified","production ready"]
 for rel in ["README.md","docs/PROJECT_STATUS.md","docs/HARDWARE_LAB_CARD.md"]:
  text=(root/rel).read_text(encoding="utf-8").lower() if (root/rel).is_file() else ""
  for claim in claims:
   positive = [line for line in text.splitlines() if claim in line and not any(marker in line for marker in ("unsupported", "not ", "no claim", "不能", "不成立"))]
   if positive:err.append(f"unsupported claim in {rel}: {claim}")
 try:ET.parse(root/"hardware/wiring-diagram.svg")
 except (ET.ParseError,OSError) as exc:err.append(f"invalid wiring SVG: {exc}")
 try:
  rows=list(csv.DictReader((root/"hardware/BOM.csv").open(newline="",encoding="utf-8")))
  if len(rows)<9:err.append("BOM must contain at least 9 component rows")
 except (OSError,csv.Error) as exc:err.append(f"invalid BOM.csv: {exc}")
 if err:
  print("Repository check: FAIL",file=sys.stderr)
  for e in sorted(set(err)):print(f"- {e}",file=sys.stderr)
  return 1
 print(f"Repository check: PASS ({len(checked)} files checked)");return 0
if __name__=="__main__":raise SystemExit(main())
