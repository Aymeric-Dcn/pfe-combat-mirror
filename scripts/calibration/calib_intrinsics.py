"""Intrinsic calibration of a webcam with a checkerboard (printed or shown on a screen).

Run from the RT-COSMIK root:
    python3 calib_intrinsics.py --square-mm 25 --width 640 --height 480
Writes calib_images/*.jpg and config/cam_params/intrinsics/camera_0_intrinsics.yaml.
"""
import argparse
import os
import time

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--square-mm", type=float, default=25.0)
ap.add_argument("--cols", type=int, default=9, help="inner corners per row")
ap.add_argument("--rows", type=int, default=6, help="inner corners per column")
ap.add_argument("--width", type=int, default=640)
ap.add_argument("--height", type=int, default=480)
ap.add_argument("--n", type=int, default=25, help="number of views to keep")
ap.add_argument("--device", type=int, default=0)
ap.add_argument("--out", default="config/cam_params/intrinsics/camera_0_intrinsics.yaml")
args = ap.parse_args()

pattern, w, h = (args.cols, args.rows), args.width, args.height
os.makedirs(os.path.dirname(args.out), exist_ok=True)
os.makedirs("calib_images", exist_ok=True)

cap = cv2.VideoCapture(args.device, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
ok, frame = cap.read()
assert ok and frame.shape[:2] == (h, w), f"got {frame.shape[1]}x{frame.shape[0]} instead of {w}x{h}"

objp = np.zeros((pattern[0] * pattern[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:pattern[0], 0:pattern[1]].T.reshape(-1, 2) * args.square_mm / 1000.0
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
obj_points, img_points, last = [], [], 0.0

print("Move the board slowly: center, corners, near/far, tilted. Hold each pose ~1 s.")
while len(obj_points) < args.n:
    ok, frame = cap.read()
    if not ok or time.time() - last < 2.0:
        continue
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(
        gray, pattern, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
    if not found:
        continue
    # 5x5 window: at 640x480 an 11x11 window spills onto neighbouring squares
    corners = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), criteria)
    obj_points.append(objp)
    img_points.append(corners)
    last = time.time()
    cv2.imwrite(f"calib_images/calib_{len(obj_points):02d}.jpg", frame)
    print(f"  view {len(obj_points)}/{args.n}", flush=True)
cap.release()

rms, K, D, _, _ = cv2.calibrateCamera(obj_points, img_points, (w, h), None, None)
print(f"\nRMS reprojection error: {rms:.3f} px")
print("K =\n", K, "\nD =", D.ravel())

fs = cv2.FileStorage(args.out, cv2.FILE_STORAGE_WRITE)
fs.write("K", K)
fs.write("D", D)
fs.write("reproj", rms)
fs.release()
print("saved", args.out)
