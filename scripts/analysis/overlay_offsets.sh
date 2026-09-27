#!/usr/bin/env bash
# One overlay video per offset (or start:end ramp), to pick the best sync by eye.
# Run from the RT-COSMIK root: bash overlay_offsets.sh output/demo_03 "0 0.5 1 1.5 2"
set -euo pipefail
run="${1:-output/demo_03}"
offsets="${2:-0 0.5 1 1.5 2}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for o in ${offsets}; do
  python3 "${here}/overlay_video.py" "${run}" "${o}" 2>&1 | grep -v "File ended prematurely"
done
ls -lh "${run}"/overlay_off*.mp4
