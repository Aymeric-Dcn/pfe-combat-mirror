# PFE Combat Mirror — boxer motion capture

*[Version française](README.fr.md)*

Final-year project at Polytech Montpellier (MEA), with the Biomedical Engineering department of CSULB, the Australian company [Combat Mirror](https://combatmirror.com/) and LAAS-CNRS (Gepetto team).

**Goal:** fit a boxing mirror with pressure sensors (impact strength and location), synchronize them with the boxer's joint kinematics measured by RGB cameras with [RT-COSMIK](https://github.com/Gepetto/rt-cosmik), then score the training session with a learned model (Transformer).

| Deliverable | Status (2026-11-20) |
|---|---|
| 1. RT-COSMIK setup | **Done.** Full pipeline with one webcam (detection, skeleton, biomechanical model, joint angles to CSV); real time at 30 fps on the Polytech Debian machine |
| 2. Mirror instrumentation | **In progress.** 4-sensor FlexiForce force plate prototype: corner module (3D), conditioning (schematic, simulations, breadboard-validated), Nucleo firmware and PC script working; sensors on order |
| 3. Synchronization + CSV | **In progress.** Camera side ready; force plate frames carry a 2 kHz sample counter; hardware camera trigger planned (Nucleo TIM1) |
| 4. Data processing (ML) | Not started |

The progress report (French, LaTeX + compiled PDF) is in [`docs/rapport/`](docs/rapport/).

## Layout

```
config/cam_params/intrinsics/   webcam calibration (format read by RT-COSMIK main)
rtcosmik/patches/               our changes to RT-COSMIK (git apply)
scripts/tests/                  webcam, YOLO engine, NLF skeleton, engine header checks
scripts/calibration/            intrinsic calibration (checkerboard on a screen) + recompute
scripts/analysis/               take quality check + skeleton overlay video
scripts/tools/                  RT-COSMIK main setup + export from the container
scripts/forceplate/             force plate acquisition, live view and calibration (PC)
docker/                         image built on top of cosmik-dev-container's
results/                        takes (csv, plots; videos stay out of git)
hardware/3d/                    force plate parts (OpenSCAD): corner module, 4-sensor test rig
hardware/simulation/            sensor conditioning simulation (ngspice)
hardware/electronics/           sensor conditioning schematic (KiCad)
hardware/firmware/              Nucleo F072RB acquisition firmware (4 sensors, 2 kHz)
docs/                           setup guide (EN/FR), progress report and calibration protocol (FR)
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

## Force plate (prototype)

Four FlexiForce A201 sensors, one under each corner of a plate, give the impact force (sum) and location (centre of pressure).

```
FlexiForce -> op-amp conditioning (MCP6004, 3.3 V) -> RC filter 480 Hz -> Nucleo F072RB ADC (2 kHz) -> USB -> forceplate.py
```

| Part | Where |
|---|---|
| Corner module and 300 mm test rig (OpenSCAD, parametric) | [`hardware/3d/`](hardware/3d/) |
| Conditioning schematic (KiCad) and bench test sheets | [`hardware/electronics/`](hardware/electronics/) |
| Circuit simulations (ngspice) | [`hardware/simulation/`](hardware/simulation/) |
| Acquisition firmware (STM32CubeIDE, register level) | [`hardware/firmware/nucleo_acq/`](hardware/firmware/nucleo_acq/) |
| PC acquisition, live view and calibration | [`scripts/forceplate/`](scripts/forceplate/) |
| Calibration protocol (FR) | [`docs/protocole_etalonnage.md`](docs/protocole_etalonnage.md) |

Quick start: import `hardware/firmware/nucleo_acq` in STM32CubeIDE and flash it (Run), then:

```bash
pip install pyserial numpy matplotlib
cd scripts/forceplate
python forceplate.py -p COM4 monitor     # or /dev/ttyACM0; --sim to try without the board
python forceplate.py -p COM4 live
```

## Changes to RT-COSMIK

- `0001-nlf-import-torchvision.patch`: the NLF TorchScript model calls `torchvision::nms`, which is only registered once `torchvision` is imported. Without it the pipeline process crashes at startup.
- `0002-settings-single-webcam.patch`: 640x480 at 30 fps, one camera, `sbs` inverse kinematics, subject height and weight.

## References

- RT-COSMIK: https://github.com/Gepetto/rt-cosmik
- Camera calibration (LAAS): https://github.com/Gepetto/cams_calibration
- ROS 2 bridge: https://github.com/Gepetto/rtcosmik_ros
- Dev container: https://github.com/MaximeSabbah/cosmik-dev-container
