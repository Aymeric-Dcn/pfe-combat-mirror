"""Take a picture after a 10 s countdown and draw the NLF 2D skeleton (24 SMPL joints).

Run from the RT-COSMIK root: python3 test_skeleton_nlf.py
"""
import glob
import time

import cv2
import torch
import torchvision  # noqa: F401  registers torchvision::nms, needed by the NLF TorchScript model

SMPL_PARENTS = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21]

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
assert cap.isOpened(), "camera not opened"

for s in range(10, 0, -1):
    print(f"Picture in {s} s...", flush=True)
    t = time.time()
    while time.time() - t < 1:  # keep draining the buffer so the picture is fresh
        cap.read()
ok, frame = cap.read()
cap.release()
cv2.imwrite("standing_raw.jpg", frame)

model = torch.jit.load(sorted(glob.glob("weights/nlf/*.torchscript"))[0]).cuda().eval()
img = torch.from_numpy(frame[..., ::-1].copy()).permute(2, 0, 1).cuda()
with torch.inference_mode(), torch.device("cuda"):
    pred = model.detect_smpl_batched(img.unsqueeze(0))
joints = pred["joints2d"][0].cpu().numpy()
print(f"{len(joints)} person(s) detected")

for person in joints:
    for j, p in enumerate(SMPL_PARENTS):
        if p >= 0:
            cv2.line(frame, tuple(map(int, person[j])), tuple(map(int, person[p])), (0, 255, 0), 3)
    for x, y in person:
        cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
cv2.imwrite("standing_skeleton.jpg", frame)
print("saved standing_skeleton.jpg")
