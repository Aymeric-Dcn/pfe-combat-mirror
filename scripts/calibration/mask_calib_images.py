"""Black out everything but the checkerboard in calibration images (removes faces and the room).

Usage: python3 mask_calib_images.py calib_images calib_images_masked [--margin 40]
Images where the board is not found are skipped, so nothing unmasked is written.
"""
import argparse
import glob
import os

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--cols", type=int, default=9)
ap.add_argument("--rows", type=int, default=6)
ap.add_argument("--margin", type=int, default=40, help="pixels kept around the board")
args = ap.parse_args()

os.makedirs(args.dst, exist_ok=True)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * args.margin + 1, 2 * args.margin + 1))
kept = skipped = 0

for path in sorted(glob.glob(os.path.join(args.src, "*.jpg"))):
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(
        gray, (args.cols, args.rows), cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
    if not found:
        print("board not found, skipped:", path)
        skipped += 1
        continue
    mask = np.zeros(gray.shape, np.uint8)
    cv2.fillConvexPoly(mask, cv2.convexHull(corners.astype(np.int32)), 255)
    mask = cv2.dilate(mask, kernel)
    out = np.zeros_like(img)
    out[mask > 0] = img[mask > 0]
    cv2.imwrite(os.path.join(args.dst, os.path.basename(path)), out)
    kept += 1

print(f"{kept} masked, {skipped} skipped -> {args.dst}")
