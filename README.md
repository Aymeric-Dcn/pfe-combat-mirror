# PFE Combat Mirror — boxer motion capture

*[Version française](README.fr.md)*

Final-year project at Polytech Montpellier (MEA), with the Biomedical Engineering department of CSULB, the Australian company [Combat Mirror](https://combatmirror.com/) and LAAS-CNRS (Gepetto team).

**Goal:** fit a boxing mirror with pressure sensors (impact strength and location), synchronize them with the boxer's joint kinematics measured by RGB cameras with [RT-COSMIK](https://github.com/Gepetto/rt-cosmik), then score the training session with a learned model (Transformer).

| Deliverable | Status (2026-09-27) |
|---|---|
| 1. RT-COSMIK setup | ✅ Full pipeline running with one webcam: detection, skeleton, biomechanical model, joint angles to CSV |
| 2. Mirror instrumentation | ⬜ Not started |
| 3. Synchronization + CSV | 🟡 Camera side ready (`joint_angles.csv`, `markers.csv` with a frame counter) |
| 4. Data processing (ML) | ⬜ Not started |

The progress report (French, LaTeX + compiled PDF) is in [`docs/rapport/`](docs/rapport/).

## Layout

```
config/cam_params/intrinsics/   webcam calibration (format read by RT-COSMIK main)
rtcosmik/patches/               our changes to RT-COSMIK (git apply)
scripts/tests/                  webcam, YOLO engine, NLF skeleton, engine header checks
scripts/calibration/            intrinsic calibration (checkerboard on a screen) + recompute
scripts/analysis/               take quality check + skeleton overlay video
scripts/tools/                  RT-COSMIK main setup + export from the container
docker/                         image built on top of cosmik-dev-container's
results/                        takes (csv, plots; videos stay out of git)
docs/                           setup guide (EN/FR), progress report (FR)
```

## Quick start

Environment: the Docker image from [cosmik-dev-container](https://github.com/MaximeSabbah/cosmik-dev-container) (CUDA 12.1, Ubuntu 22.04, ROS 2 Humble, torch 2.4.1) plus Gepetto's RT-COSMIK `main`. Full setup, Windows/WSL 2 notes and troubleshooting: [`docs/SETUP.md`](docs/SETUP.md).

```bash
# inside the container
git clone https://github.com/Aymeric-Dcn/pfe-combat-mirror.git /root/pfe-combat-mirror
bash /root/pfe-combat-mirror/scripts/tools/setup_rtcosmik_main.sh
cd ~/workspace/ros_ws/RT-COSMIK-main
export YOLO_VERBOSE=False
python3 scripts/python/core/run_pipeline.py --online --cameras 0
```

Stand still and fully visible until `Model calibration finished`, then press `q` and `Ctrl+C` to stop. Results go to `output/<no_trial>/`.

On a recorded take:

```bash
python3 /root/pfe-combat-mirror/scripts/analysis/analyze_take.py output/demo_03
bash    /root/pfe-combat-mirror/scripts/analysis/overlay_offsets.sh output/demo_03 "0 0.5 1 1.5 2"
```

## Changes to RT-COSMIK

- `0001-nlf-import-torchvision.patch`: the NLF TorchScript model calls `torchvision::nms`, which is only registered once `torchvision` is imported. Without it the pipeline process crashes at startup.
- `0002-settings-single-webcam.patch`: 640x480 at 30 fps, one camera, `sbs` inverse kinematics, subject height and weight.

## References

- RT-COSMIK: https://github.com/Gepetto/rt-cosmik
- Camera calibration (LAAS): https://github.com/Gepetto/cams_calibration
- ROS 2 bridge: https://github.com/Gepetto/rtcosmik_ros
- Dev container: https://github.com/MaximeSabbah/cosmik-dev-container
