# Installation et utilisation

*[English version](SETUP.md)*

- [Prérequis](#prérequis)
- [Environnement](#environnement)
- [Lancer le conteneur](#lancer-le-conteneur)
- [Caméra](#caméra)
- [Enregistrer une prise](#enregistrer-une-prise)
- [Analyse](#analyse)
- [Messages connus](#messages-connus)

## Prérequis

| | Testé avec |
|---|---|
| Hôte | Linux (recommandé) ou Windows 11 + WSL 2 + Docker Desktop |
| GPU | NVIDIA RTX 4070 SUPER (12 Go), NVIDIA Container Toolkit |
| Caméra | Webcam USB avec sortie MJPEG (UGREEN, `0c45:2283`) |

## Environnement

L'ensemble tourne dans l'image de [cosmik-dev-container](https://github.com/MaximeSabbah/cosmik-dev-container) : CUDA 12.1, cuDNN 8, Ubuntu 22.04, ROS 2 Humble, PyTorch 2.4.1, Pinocchio 3.9 avec CasADi, acados. L'image se construit localement à partir de son Dockerfile ; aucune image prête à l'emploi n'est publiée.

```bash
git clone https://github.com/MaximeSabbah/cosmik-dev-container.git
cd cosmik-dev-container/.devcontainer
docker build -t mmpose_image .
```

Ce projet y ajoute RT-COSMIK `main` de [Gepetto](https://github.com/Gepetto/rt-cosmik), ffmpeg, deux petits patchs et la calibration de la webcam. Soit en image dérivée :

```bash
docker build -f docker/Dockerfile -t pfe_cosmik .
```

soit avec le script d'installation dans un conteneur existant :

```bash
git clone https://github.com/Aymeric-Dcn/pfe-combat-mirror.git /root/pfe-combat-mirror
bash /root/pfe-combat-mirror/scripts/tools/setup_rtcosmik_main.sh
```

Le script peut être relancé sans risque. Il télécharge les poids NLF et YOLO et construit le moteur TensorRT de YOLO (`BATCHES="1"`, une caméra). Un moteur est lié au GPU et à la version de TensorRT : il est toujours construit sur la machine cible et n'est jamais versionné.

## Lancer le conteneur

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

La webcam est partagée avec WSL via [usbipd-win](https://github.com/dorssel/usbipd-win), avec un terminal WSL laissé ouvert :

```powershell
usbipd list
usbipd attach --wsl --busid <BUSID>
```

Deux limites : USB/IP plafonne la webcam à environ 13 fps en 640x480 (4 fps en 1280x720), et le viewer Meshcat (port 7000) doit être redirigé, par exemple depuis VS Code (*Dev Containers: Attach to Running Container*, puis l'onglet *Ports*).

## Caméra

Garder une cadence constante en faible lumière (à refaire à chaque branchement) :

```bash
v4l2-ctl -d /dev/video0 -c exposure_dynamic_framerate=0
```

Calibration intrinsèque, à la résolution du pipeline (ici 640x480), avec un damier de 9x6 coins intérieurs imprimé ou affiché sur un écran ([`checkerboard_9x6.png`](../scripts/calibration/checkerboard_9x6.png)) :

```bash
cd ~/workspace/ros_ws/RT-COSMIK-main
python3 /root/pfe-combat-mirror/scripts/calibration/calib_intrinsics.py --square-mm 25
python3 /root/pfe-combat-mirror/scripts/calibration/recalib.py           # optionnel : écarte les vues aberrantes
python3 /root/pfe-combat-mirror/scripts/calibration/mask_calib_images.py calib_images calib_images_masked
```

Le résultat est écrit dans `config/cam_params/intrinsics/camera_0_intrinsics.yaml`. Seules les vues masquées (damier uniquement) sont conservées dans le dépôt.

## Enregistrer une prise

```bash
cd ~/workspace/ros_ws/RT-COSMIK-main
export YOLO_VERBOSE=False
python3 scripts/python/core/run_pipeline.py --online --cameras 0
```

Rester immobile et entièrement visible (2,5 à 3 m) jusqu'à `Model calibration finished`, puis bouger. Arrêt avec `q`, puis `Ctrl+C`. `no_trial` dans `settings.py` nomme la prise ; les sorties vont dans `output/<no_trial>/` :

| Fichier | Contenu |
|---|---|
| `joint_angles.csv` | pose du bassin + 36 angles articulaires (rad), une ligne par image traitée |
| `markers.csv` | 43 marqueurs anatomiques en 3D (m), repère caméra |
| `camera_0.mkv` | flux MJPEG brut de la caméra |

Les deux CSV commencent par `Frame_0`, le compteur d'images de la caméra.

## Analyse

```bash
python3 /root/pfe-combat-mirror/scripts/analysis/analyze_take.py output/demo_03
bash    /root/pfe-combat-mirror/scripts/analysis/overlay_offsets.sh output/demo_03 "-3 -2 -1 0"
```

- `analyze_take.py` contrôle une prise (valeurs manquantes, stabilité des segments, sauts de marqueurs) et trace la flexion des coudes, la profondeur et le déplacement des poignets dans `analysis.png`.
- `overlay_video.py` dessine les marqueurs sur la vidéo enregistrée. CSV et vidéo sont alignés par le compteur d'images ; un décalage constant (`-3`) ou une rampe linéaire (`1:-1`) compense le retard résiduel, en images vidéo.
- `collect_from_container.sh` exporte du conteneur la configuration, les modifications de RT-COSMIK, les résultats et les versions logicielles, avec l'arborescence du dépôt.

## Messages connus

| Message | Signification |
|---|---|
| `A NumPy version >=1.17.3 and <1.25.0 is required for this version of SciPy` | SciPy système contre NumPy 1.26.4 épinglé ; sans effet |
| `WARNING 'half' is deprecated` | Avertissement Ultralytics ; masqué par `YOLO_VERBOSE=False` |
| `No world pose for reference camera 0` | Pas d'ancrage monde (ArUco) : positions dans le repère caméra ; angles articulaires non affectés |
| `[matroska] File ended prematurely` | Vidéo coupée par `Ctrl+C` ; reste lisible |
| `Unknown builtin op: torchvision::nms` | Patch `0001` non appliqué |
| `usbipd: There is no WSL 2 distribution running` | Démarrer Docker Desktop et garder un terminal `wsl` ouvert |
