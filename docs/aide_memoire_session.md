# Aide-mémoire : démarrer une session (Windows + WSL2 + Docker Desktop)

## 1. Brancher la webcam dans WSL (PowerShell administrateur)

```powershell
wsl                                   # dans un 2e PowerShell, à laisser ouvert (WSL doit tourner)
usbipd list                           # la UGREEN Camera est en 5-2 (état "Shared")
usbipd attach --wsl --busid 5-2
```

Erreur `There is no WSL 2 distribution running` : Docker Desktop n'est pas démarré, ou aucune fenêtre `wsl` n'est ouverte.

## 2. Entrer dans le conteneur

```powershell
docker start 90034be366af
docker exec -it 90034be366af bash
```

## 3. Régler la caméra (à refaire à chaque branchement)

```bash
ls /dev/video*                                        # /dev/video0 attendu
v4l2-ctl -d /dev/video0 -c exposure_dynamic_framerate=0   # sinon le fps chute en faible lumière
```

## 4. Lancer RT-COSMIK

```bash
cd ~/workspace/ros_ws/RT-COSMIK-main
sed -i 's/^    no_trial = "demo_[0-9]*"/    no_trial = "demo_04"/' settings.py   # nouveau nom de prise
export YOLO_VERBOSE=False
python3 scripts/python/core/run_pipeline.py --online --cameras 0
```

- Rester immobile, entièrement visible (2,5 à 3 m), jusqu'à `Model calibration finished`.
- Viewer 3D : http://127.0.0.1:7000/static/ (via VS Code « Attach to Running Container » puis onglet PORTS, port 7000).
- Arrêt : `q`, puis `Ctrl+C`. Résultats : `output/<no_trial>/`.

## 5. Récupérer les fichiers sous Windows

```powershell
docker cp 90034be366af:/root/workspace/ros_ws/RT-COSMIK-main/output/demo_04 C:\pfe\demo_04
```

## 6. Sauvegarder l'état du conteneur

```powershell
docker commit 90034be366af cosmik-backup:AAAA-MM-JJ
```

## Messages sans gravité

- `UserWarning: A NumPy version >=1.17.3 and <1.25.0 is required for this version of SciPy` : SciPy système contre NumPy 1.26.4 épinglé par le Dockerfile, sans effet observé.
- `WARNING 'half' is deprecated` : Ultralytics, masqué par `export YOLO_VERBOSE=False`.
- `[matroska] File ended prematurely` : la vidéo a été coupée par `Ctrl+C`, elle reste lisible.
- `No world pose for reference camera 0` : pas de repère monde (ArUco), les positions sont dans le repère caméra. Les angles articulaires ne sont pas affectés.
