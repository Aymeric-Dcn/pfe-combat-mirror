# Setup and usage

*[Version française](SETUP.fr.md)*

- [Requirements](#requirements)
- [Environment](#environment)
- [Running the container](#running-the-container)
- [Camera](#camera)
- [Recording a take](#recording-a-take)
- [Analysis](#analysis)
- [Known messages](#known-messages)

## Requirements

| | Tested with |
|---|---|
| Host | Linux (recommended) or Windows 11 + WSL 2 + Docker Desktop |
| GPU | NVIDIA RTX 4070 SUPER (12 GB), NVIDIA Container Toolkit |
| Camera | USB webcam with MJPEG output (UGREEN, `0c45:2283`) |

## Environment

The stack runs in the image from [cosmik-dev-container](https://github.com/MaximeSabbah/cosmik-dev-container): CUDA 12.1, cuDNN 8, Ubuntu 22.04, ROS 2 Humble, PyTorch 2.4.1, Pinocchio 3.9 with CasADi, acados. The image is built locally from its Dockerfile; no prebuilt image is published.

```bash
git clone https://github.com/MaximeSabbah/cosmik-dev-container.git
cd cosmik-dev-container/.devcontainer
docker build -t mmpose_image .
```

This project adds Gepetto's [RT-COSMIK](https://github.com/Gepetto/rt-cosmik) `main`, ffmpeg, two small patches and the webcam calibration. Either build a derived image:

```bash
docker build -f docker/Dockerfile -t pfe_cosmik .
```

or run the setup script in an existing container:

```bash
git clone https://github.com/Aymeric-Dcn/pfe-combat-mirror.git /root/pfe-combat-mirror
bash /root/pfe-combat-mirror/scripts/tools/setup_rtcosmik_main.sh
```

The script is idempotent. It downloads the NLF and YOLO weights and builds the YOLO TensorRT engine (`BATCHES="1"`, one camera). Engines are tied to the GPU and TensorRT version, so they are always built on the target machine and never committed.

## Running the container

**Linux**

```bash
xhost +local:
docker run -it --net=host --gpus all --privileged \
  --device-cgroup-rule "c 81:* rmw" --device-cgroup-rule "c 189:* rmw" \
  -e DISPLAY=$DISPLAY -v /dev:/dev -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $HOME/pfe-combat-mirror:/root/pfe-combat-mirror \
  pfe_cosmik
```

**Windows (WSL 2)**

`scripts/tools/start_session.ps1` does the whole start-up: Docker Desktop, webcam attached to WSL, container started, camera configured, shell opened in RT-COSMIK.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\tools\start_session.ps1
```

Manually, the webcam is shared with WSL through [usbipd-win](https://github.com/dorssel/usbipd-win), with a WSL shell kept open:

```powershell
usbipd list
usbipd attach --wsl --busid <BUSID>
```

Two limits apply: USB/IP caps the webcam at about 13 fps at 640x480 (4 fps at 1280x720), and the Meshcat viewer (port 7000) needs to be forwarded, for instance from VS Code (*Dev Containers: Attach to Running Container*, then the *Ports* tab).

## Camera

Keep the frame rate constant in low light (reset every time the camera is plugged in):

```bash
v4l2-ctl -d /dev/video0 -c exposure_dynamic_framerate=0
```

Intrinsic calibration, at the resolution used by the pipeline (640x480 here), with a 9x6 inner-corner checkerboard printed or shown on a screen ([`checkerboard_9x6.png`](../scripts/calibration/checkerboard_9x6.png)):

```bash
cd ~/workspace/ros_ws/RT-COSMIK-main
python3 /root/pfe-combat-mirror/scripts/calibration/calib_intrinsics.py --square-mm 25
python3 /root/pfe-combat-mirror/scripts/calibration/recalib.py           # optional: drop outlier views
python3 /root/pfe-combat-mirror/scripts/calibration/mask_calib_images.py calib_images calib_images_masked
```

The result goes to `config/cam_params/intrinsics/camera_0_intrinsics.yaml`. Only masked views (board only) are stored in the repository.

## Recording a take

```bash
cd ~/workspace/ros_ws/RT-COSMIK-main
export YOLO_VERBOSE=False
python3 scripts/python/core/run_pipeline.py --online --cameras 0
```

Stand still and fully visible (2.5 to 3 m) until `Model calibration finished`, then move. Stop with `q`, then `Ctrl+C`. Set `no_trial` in `settings.py` to name the take; outputs go to `output/<no_trial>/`:

| File | Content |
|---|---|
| `joint_angles.csv` | pelvis pose + 36 joint angles (rad), one row per processed frame |
| `markers.csv` | 43 anatomical markers in 3D (m), camera frame |
| `camera_0.mkv` | raw MJPEG stream from the camera |

Both CSV files start with `Frame_0`, the camera frame counter.

## Analysis

```bash
python3 /root/pfe-combat-mirror/scripts/analysis/analyze_take.py output/demo_03
bash    /root/pfe-combat-mirror/scripts/analysis/overlay_offsets.sh output/demo_03 "-3 -2 -1 0"
```

- `analyze_take.py` checks a take (missing values, segment length stability, marker jumps) and plots elbow flexion, wrist depth and wrist displacement to `analysis.png`.
- `overlay_video.py` draws the markers on the recorded video. The CSV and the video are aligned by frame counter; a constant offset (`-3`) or a linear ramp (`1:-1`) compensates the residual lag, in video frames.
- `collect_from_container.sh` exports config, RT-COSMIK changes, results and software versions from the container into the repository layout.

## Known messages

| Message | Meaning |
|---|---|
| `A NumPy version >=1.17.3 and <1.25.0 is required for this version of SciPy` | System SciPy vs the pinned NumPy 1.26.4; harmless |
| `WARNING 'half' is deprecated` | Ultralytics deprecation; hidden by `YOLO_VERBOSE=False` |
| `No world pose for reference camera 0` | No world anchor (ArUco): positions are in the camera frame; joint angles are unaffected |
| `[matroska] File ended prematurely` | Video cut by `Ctrl+C`; still readable |
| `Unknown builtin op: torchvision::nms` | Patch `0001` not applied |
| `usbipd: There is no WSL 2 distribution running` | Start Docker Desktop and keep a `wsl` shell open |
