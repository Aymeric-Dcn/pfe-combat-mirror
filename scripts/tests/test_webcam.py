"""Check the webcam frame rate and run YOLO person detection on one frame.

Run from the RT-COSMIK root: python3 test_webcam.py
"""
import time

import cv2
from ultralytics import YOLO

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)
assert cap.isOpened(), "camera not opened"

for _ in range(10):  # let auto exposure settle
    cap.read()

t0, n = time.time(), 0
while n < 60:
    ok, frame = cap.read()
    if ok:
        n += 1
fps = n / (time.time() - t0)
print(f"{frame.shape[1]}x{frame.shape[0]} @ {fps:.1f} fps")
cv2.imwrite("webcam_raw.jpg", frame)

model = YOLO("weights/yolo/yolov10n.pt")
res = model.predict(frame, classes=0, conf=0.3, device=0, verbose=False)[0]
print(f"{len(res.boxes)} person(s) detected")
cv2.imwrite("webcam_yolo.jpg", res.plot())
cap.release()
