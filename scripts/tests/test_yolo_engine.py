"""Load a YOLO TensorRT engine through Ultralytics and run it on an image.

Usage: python3 test_yolo_engine.py [engine] [image]
"""
import sys

from ultralytics import YOLO

engine = sys.argv[1] if len(sys.argv) > 1 else "weights/yolo/yolov10n_b1.engine"
image = sys.argv[2] if len(sys.argv) > 2 else "standing_raw.jpg"

r = YOLO(engine, task="detect").predict(image, classes=0, device=0, verbose=False)[0]
print(len(r.boxes), "person(s)", r.boxes.xyxy.tolist())
