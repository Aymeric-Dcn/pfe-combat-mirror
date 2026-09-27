"""Print the Ultralytics metadata stored at the start of an exported .engine file.

Layout: 4-byte little-endian length, JSON metadata, then the raw TensorRT engine.
This header is why `trtexec --loadEngine` rejects the file while Ultralytics loads it.

Usage: python3 engine_metadata.py weights/yolo/yolov10n_b1.engine
"""
import json
import struct
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "weights/yolo/yolov10n.engine"
with open(path, "rb") as f:
    size = struct.unpack("<I", f.read(4))[0]
    meta = json.loads(f.read(size))

for key in ("description", "batch", "imgsz", "half", "task"):
    print(f"{key}: {meta.get(key)}")
