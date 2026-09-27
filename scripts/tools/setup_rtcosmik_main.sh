#!/usr/bin/env bash
# Install Gepetto's RT-COSMIK main next to the container's own copy and apply our changes.
# Meant to run in the image built from MaximeSabbah/cosmik-dev-container. Safe to re-run.
#
# Usage: bash setup_rtcosmik_main.sh [--no-models] [install dir]
set -euo pipefail

models=1
if [[ "${1:-}" == "--no-models" ]]; then models=0; shift; fi
dest="${1:-/root/workspace/ros_ws/RT-COSMIK-main}"
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if ! command -v ffmpeg >/dev/null; then
  echo "[setup] installing ffmpeg"
  apt-get update -q && apt-get install -y -q ffmpeg
fi

if [[ ! -d "${dest}/.git" ]]; then
  echo "[setup] cloning Gepetto/rt-cosmik into ${dest}"
  git clone -q https://github.com/Gepetto/rt-cosmik.git "${dest}"
fi

for p in "${repo}"/rtcosmik/patches/*.patch; do
  if git -C "${dest}" apply --reverse --check "$p" 2>/dev/null; then
    echo "[setup] already applied: $(basename "$p")"
  else
    git -C "${dest}" apply --whitespace=nowarn "$p"
    echo "[setup] applied: $(basename "$p")"
  fi
done

calib="${dest}/config/cam_params/intrinsics/camera_0_intrinsics.yaml"
if [[ ! -f "${calib}" ]]; then
  mkdir -p "$(dirname "${calib}")"
  cp "${repo}/config/cam_params/intrinsics/camera_0_intrinsics.yaml" "${calib}"
  echo "[setup] copied webcam calibration"
fi

if [[ "${models}" == 1 ]]; then
  # needs the GPU: the TensorRT engine is built for this card and TensorRT version
  (cd "${dest}" && BATCHES="1" bash scripts/bash/fetch_models.sh)
else
  echo "[setup] models skipped; later run: cd ${dest} && BATCHES=\"1\" bash scripts/bash/fetch_models.sh"
fi

echo "[setup] done: ${dest}"
