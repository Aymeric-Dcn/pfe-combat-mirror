"""Draw the RT-COSMIK markers (markers.csv) on the recorded video.

Run from the RT-COSMIK root: python3 overlay_video.py output/demo_03 [offset]
Writes <run>/overlay_off<+N>.mp4. A positive offset moves the skeleton earlier.
"""
import sys

import cv2
import numpy as np
import pandas as pd

run = sys.argv[1] if len(sys.argv) > 1 else "output/demo_03"
offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
calib = "config/cam_params/intrinsics/camera_0_intrinsics.yaml"
out_path = f"{run}/overlay_off{offset:+03d}.mp4"

BONES = [("RSHO", "LSHO"), ("RSHO", "RELB"), ("RELB", "RWRI"), ("LSHO", "LELB"), ("LELB", "LWRI"),
         ("RASI", "LASI"), ("RSHO", "RASI"), ("LSHO", "LASI"), ("RASI", "RKNE"), ("RKNE", "RANK"),
         ("LASI", "LKNE"), ("LKNE", "LANK"), ("RANK", "RTOE"), ("LANK", "LTOE"), ("C7", "Head"),
         ("RWRI", "RMID"), ("LWRI", "LMID")]

fs = cv2.FileStorage(calib, cv2.FILE_STORAGE_READ)
K, D = fs.getNode("K").mat(), fs.getNode("D").mat()
fs.release()

mk = pd.read_csv(f"{run}/markers.csv")
ja = pd.read_csv(f"{run}/joint_angles.csv")
frame_col = [c for c in mk.columns if c.startswith("Frame")][0]
names = [c[:-2] for c in mk.columns if c.endswith("_x")]
bones = [b for b in BONES if b[0] in names and b[1] in names]
angle_cols = {label: next((c for c in ja.columns if key in c), None)
              for label, key in (("R elbow", "Right_Elbow_Flexion"), ("L elbow", "Left_Elbow_Flexion"))}

# The .mkv cut by Ctrl+C has no reliable index, so count frames by reading them.
cap = cv2.VideoCapture(f"{run}/camera_0.mkv")
n_video = 0
while cap.grab():
    n_video += 1
cap.release()

# Frame_0 counts every frame handed over by ffmpeg (duplicates included, ~30/s) while the
# video only holds the real camera frames. Map the counter linearly onto the video:
# counter 0 = first video frame, last counter value = last video frame.
counter = mk[frame_col].to_numpy(float)
row_frame = counter / counter.max() * (n_video - 1)
print(f"counter {counter.min():.0f} -> {counter.max():.0f} | video {n_video} frames | offset {offset:+d}")

cap = cv2.VideoCapture(f"{run}/camera_0.mkv")
fps = cap.get(cv2.CAP_PROP_FPS) or 30
w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

i = drawn = 0
while True:
    ok, img = cap.read()
    if not ok:
        break
    j = np.searchsorted(row_frame, i + offset, side="right") - 1
    if j >= 0:
        row = mk.iloc[j]
        P = np.array([[row[f"{n}_x"], row[f"{n}_y"], row[f"{n}_z"]] for n in names], dtype=np.float64)
        valid = np.isfinite(P).all(1) & (P[:, 2] > 0.1)
        uv, _ = cv2.projectPoints(np.nan_to_num(P), np.zeros(3), np.zeros(3), K, D)
        pts = {n: tuple(map(int, uv[k, 0])) for k, n in enumerate(names) if valid[k]}
        for a, b in bones:
            if a in pts and b in pts:
                cv2.line(img, pts[a], pts[b], (0, 255, 0), 2)
        for p in pts.values():
            cv2.circle(img, p, 3, (0, 0, 255), -1)
        y = 25
        for label, col in angle_cols.items():
            if col:
                value = np.degrees(ja.iloc[min(j, len(ja) - 1)][col])
                cv2.putText(img, f"{label}: {value:6.1f} deg", (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                y += 25
        drawn += 1
    cv2.putText(img, f"offset {offset:+d}", (w - 110, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    out.write(img)
    i += 1

cap.release()
out.release()
print(f"{i} video frames, {len(mk)} csv rows, skeleton drawn on {drawn} frames")
print("saved", out_path)
