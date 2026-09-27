#!/usr/bin/env bash
# Run inside the container. Gathers everything that only lives there (actual config,
# RT-COSMIK changes, scripts, results, versions) into /root/pfe_export, using the repo
# layout, so it can be copied back on the host:
#   docker cp <container>:/root/pfe_export/. C:\pfe\pfe-combat-mirror\
#
# Usage: bash collect_from_container.sh [RT-COSMIK main dir] [old RT-COSMIK dir]
set -uo pipefail
main="${1:-/root/workspace/ros_ws/RT-COSMIK-main}"
old="${2:-/root/workspace/ros_ws/RT-COSMIK}"
out=/root/pfe_export

rm -rf "${out}"
mkdir -p "${out}"/{rtcosmik,config/cam_params/intrinsics,results,docs}

echo "[1/4] RT-COSMIK commits and local changes"
{
  echo "== RT-COSMIK main (${main}) =="
  git -C "${main}" remote get-url origin
  git -C "${main}" log -1 --format='%H  %ad  %s' --date=iso
  echo
  echo "== previous install (${old}) =="
  git -C "${old}" remote get-url origin 2>/dev/null
  git -C "${old}" log -1 --format='%H  %ad  %s' --date=iso 2>/dev/null
  git -C "${old}" branch --show-current 2>/dev/null
} > "${out}/rtcosmik/commits.txt"
git -C "${main}" diff > "${out}/rtcosmik/local_changes.diff"
cp "${main}/settings.py" "${out}/rtcosmik/settings_used.py"

echo "[2/4] Camera calibration"
cp "${main}"/config/cam_params/intrinsics/*.yaml "${out}/config/cam_params/intrinsics/" 2>/dev/null
if [ -d "${main}/calib_images" ]; then
  # only the checkerboard is kept, so no face or room ends up in the repo
  python3 "$(dirname "${BASH_SOURCE[0]}")/../calibration/mask_calib_images.py" \
    "${main}/calib_images" "${out}/config/calib_images"
fi

echo "[3/4] Results (csv and png only; videos and pictures of people are left out)"
for d in "${main}"/output/demo_*; do
  [ -d "$d" ] || continue
  r="${out}/results/$(basename "$d")"
  mkdir -p "$r"
  cp "$d"/*.csv "$d"/*.png "$r"/ 2>/dev/null
  ls -la "$d" > "$r/listing.txt"
done

echo "[4/4] Software versions and hardware"
{
  echo "== system =="; (lsb_release -ds 2>/dev/null || grep PRETTY_NAME /etc/os-release); uname -r
  echo "== gpu ==";    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null
  echo "== ffmpeg =="; ffmpeg -version 2>/dev/null | head -1
  echo "== camera =="; v4l2-ctl --list-devices 2>/dev/null
  v4l2-ctl -d /dev/video0 -C exposure_dynamic_framerate,auto_exposure 2>/dev/null
  echo "== python =="
  python3 - <<'PY'
import importlib, sys
print("python", sys.version.split()[0])
for m in ["numpy", "torch", "torchvision", "ultralytics", "tensorrt", "cv2", "pinocchio",
          "casadi", "quadprog", "meshcat", "pandas", "scipy", "example_robot_data"]:
    try:
        print(f"{m:20s} {getattr(importlib.import_module(m), '__version__', 'ok')}")
    except Exception as e:
        print(f"{m:20s} missing ({type(e).__name__})")
import torch
print("torch cuda", torch.version.cuda, "| gpu available:", torch.cuda.is_available())
PY
} > "${out}/docs/container_versions.txt" 2>&1

echo
echo "Export ready in ${out}:"
find "${out}" -maxdepth 4 | sort | sed "s|${out}|  .|"
echo
echo "On Windows (PowerShell):"
echo "  docker cp $(hostname):${out}/. C:\\pfe\\pfe-combat-mirror\\"
