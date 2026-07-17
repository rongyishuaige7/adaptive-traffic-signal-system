#!/usr/bin/env python3
"""Fail on likely credentials, private keys, or concrete private-LAN literals."""
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path
SKIP_DIRS={".git",".pio",".venv","venv","node_modules","dist","__pycache__","build"}
TEXT_SUFFIXES={"",".c",".cc",".cpp",".h",".hpp",".ini",".md",".py",".ts",".vue",".json",".csv",".svg",".sh",".yml",".yaml",".example"}
PATTERNS=[
 ("private key",re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
 ("GitHub token",re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
 ("AWS access key",re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
 ("private LAN literal",re.compile(r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")),
 ("generic assigned secret",re.compile(r"(?ix)\b(api[_-]?key|access[_-]?token|auth[_-]?token|secret|password|passwd|pwd)\b\s*[:=]\s*[\"']?(?!YOUR_|EXAMPLE|REPLACE|CHANGEME|REDACTED|<YOUR_)([A-Za-z0-9+/=_!@#$%^&*.-]{8,})")),
]
ALLOWED={"YOUR_WIFI_SSID","YOUR_WIFI_PASSWORD","YOUR_CAMERA_ADDRESS","YOUR_GATEWAY_ADDRESS","YOUR_BACKEND_LAN_ADDRESS","[REDACTED]"}
def files(root:Path):
 try: raw=subprocess.run(["git","-C",str(root),"ls-files","-z"],check=True,capture_output=True).stdout
 except (subprocess.CalledProcessError,FileNotFoundError): raw=b""
 if raw:return [root/x.decode("utf-8","surrogateescape") for x in raw.split(b"\0") if x]
 return sorted(p for p in root.rglob("*") if p.is_file() and not any(part in SKIP_DIRS for part in p.parts))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");root=Path(ap.parse_args().root).resolve();bad=[]
 for path in files(root):
  if not path.exists() or path.stat().st_size>3_000_000 or (path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Makefile",".gitignore"}):continue
  try:text=path.read_text(encoding="utf-8")
  except (UnicodeDecodeError,OSError):continue
  for n,line in enumerate(text.splitlines(),1):
   if any(x in line for x in ALLOWED):continue
   for label,pattern in PATTERNS:
    if label=="generic assigned secret" and path.name=="secret_scan.py":continue
    if pattern.search(line):bad.append(f"{path.relative_to(root)}:{n}: {label}")
 if bad:print("Secret scan: FAIL\n"+"\n".join(sorted(set(bad))),file=sys.stderr);return 1
 print("Secret scan: PASS");return 0
if __name__=="__main__":raise SystemExit(main())
