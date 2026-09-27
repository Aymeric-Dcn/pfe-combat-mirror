"""Recompute the calibration from the saved views in calib_images/,
dropping the worst view until the RMS error is low enough.

Run from the RT-COSMIK root: python3 recalib.py
The square size does not affect K and D, so it is not needed here.
"""
import argparse
import glob

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--cols", type=int, default=9)
ap.add_argument("--rows", type=int, default=6)
ap.add_argument("--width", type=int, default=640)
ap.add_argument("--height", type=int, default=480)
ap.add_argument("--target-rms", type=float, default=0.8)
ap.add_argument("--min-views", type=int, default=12)
ap.add_argument("--out", default="config/cam_params/intrinsics/camera_0_intrinsics.yaml")
args = ap.parse_args()

pattern, size = (args.cols, args.rows), (args.width, args.height)
objp = np.zeros((pattern[0] * pattern[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:pattern[0], 0:pattern[1]].T.reshape(-1, 2) * 0.025
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)

names, img_points = [], []
for path in sorted(glob.glob("calib_images/*.jpg")):
    gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(
        gray, pattern, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
    if found:
        names.append(path)
        img_points.append(cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), criteria))


def calibrate(idx):
    pts = [img_points[k] for k in idx]
    rms, K, D, rvecs, tvecs = cv2.calibrateCamera([objp] * len(idx), pts, size, None, None)
    errors = []
    for p, rv, tv in zip(pts, rvecs, tvecs):
        proj, _ = cv2.projectPoints(objp, rv, tv, K, D)
        errors.append(cv2.norm(p, proj, cv2.NORM_L2) / np.sqrt(len(objp)))
    return rms, K, D, errors


idx = list(range(len(names)))
while True:
    rms, K, D, errors = calibrate(idx)
    worst = int(np.argmax(errors))
    print(f"{len(idx)} views  RMS={rms:.3f}  worst={names[idx[worst]]} ({errors[worst]:.2f} px)")
    if rms < args.target_rms or len(idx) <= args.min_views:
        break
    idx.pop(worst)

print(f"\nFinal: {len(idx)} views, RMS = {rms:.3f} px")
print("K =\n", K, "\nD =", D.ravel())

fs = cv2.FileStorage(args.out, cv2.FILE_STORAGE_WRITE)
fs.write("K", K)
fs.write("D", D)
fs.write("reproj", rms)
fs.release()
print("saved", args.out)
