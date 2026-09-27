"""Quality check of an RT-COSMIK take (markers.csv + joint_angles.csv).

Run from the RT-COSMIK root: python3 analyze_take.py output/demo_03
Prints a summary and writes <run>/analysis.png.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

run = sys.argv[1] if len(sys.argv) > 1 else "output/demo_03"
COUNTER_HZ = 30.0    # Frame_0 advances at the fps requested from ffmpeg
JUMP_M = 0.30        # wrist displacement between two rows counted as a jump

mk = pd.read_csv(f"{run}/markers.csv")
ja = pd.read_csv(f"{run}/joint_angles.csv")
frame_col = [c for c in mk.columns if c.startswith("Frame")][0]
t = (mk[frame_col].to_numpy(float) - mk[frame_col].iloc[0]) / COUNTER_HZ


def marker(name):
    return mk[[f"{name}_x", f"{name}_y", f"{name}_z"]].to_numpy(float)


def column(df, key):
    cols = [c for c in df.columns if key in c]
    return df[cols[0]].to_numpy(float) if cols else np.full(len(df), np.nan)


print(f"=== {run} ===")
print(f"{len(mk)} rows, ~{t[-1]:.1f} s, pipeline rate ~{len(mk) / max(t[-1], 1e-6):.1f} Hz")
missing = mk.drop(columns=[frame_col]).isna().mean().max() * 100
print(f"Missing values (worst marker): {missing:.1f} %")

print("\nSegment lengths (rigid segments should stay constant):")
segments = [("R upper arm", "RSHO", "RELB"), ("L upper arm", "LSHO", "LELB"),
            ("R forearm", "RELB", "RWRI"), ("L forearm", "LELB", "LWRI"),
            ("R thigh", "RASI", "RKNE"), ("R shank", "RKNE", "RANK")]
for label, a, b in segments:
    length = np.linalg.norm(marker(a) - marker(b), axis=1)
    cv = np.nanstd(length) / np.nanmean(length) * 100
    verdict = "ok" if cv < 10 else ("fair" if cv < 20 else "unstable")
    print(f"  {label:12s} {np.nanmedian(length) * 100:5.1f} cm   cv {cv:5.1f} %   {verdict}")

pelvis_z = (marker("RASI")[:, 2] + marker("LASI")[:, 2]) / 2
print(f"\nPelvis-camera distance: {np.nanmedian(pelvis_z):.2f} m (std {np.nanstd(pelvis_z) * 100:.1f} cm)")

steps = {}
for side, name in (("R", "RWRI"), ("L", "LWRI")):
    d = np.r_[np.nan, np.linalg.norm(np.diff(marker(name), axis=0), axis=1)]
    steps[side] = d
    jumps = int(np.nansum(d > JUMP_M))
    print(f"{side} wrist jumps > {JUMP_M * 100:.0f} cm: {jumps} ({jumps / len(d) * 100:.1f} % of rows)")

elbow_r = np.degrees(column(ja, "Right_Elbow_Flexion"))
elbow_l = np.degrees(column(ja, "Left_Elbow_Flexion"))
n = min(len(t), len(elbow_r))

BLUE, ORANGE, INK, GRID = "#2a78d6", "#eb6834", "#3a3a38", "#e4e3dc"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.titlecolor": INK})
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
panels = [
    ("Elbow flexion (RT-COSMIK inverse kinematics)", "deg", elbow_r[:n], elbow_l[:n], None),
    ("Wrist to camera distance (drops during a straight punch)", "m",
     marker("RWRI")[:n, 2], marker("LWRI")[:n, 2], None),
    ("Wrist displacement between consecutive rows (spikes = jumps)", "m",
     steps["R"][:n], steps["L"][:n], JUMP_M),
]
for ax, (title, unit, right, left, threshold) in zip(axes, panels):
    ax.plot(t[:n], right, color=BLUE, lw=1.5, label="Right")
    ax.plot(t[:n], left, color=ORANGE, lw=1.5, label="Left")
    if threshold is not None:
        ax.axhline(threshold, color=INK, lw=1, ls="--")
        ax.text(t[n - 1], threshold, f"threshold {threshold * 100:.0f} cm",
                ha="right", va="bottom", color=INK)
    ax.set_title(title, loc="left", fontsize=10)
    ax.set_ylabel(unit)
    ax.grid(True, color=GRID, lw=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
axes[0].legend(loc="lower right", bbox_to_anchor=(1, 1.0), frameon=False, ncol=2)
axes[-1].set_xlabel("time since first row (s)")
fig.tight_layout()
fig.savefig(f"{run}/analysis.png", dpi=120)
print(f"\nsaved {run}/analysis.png")
