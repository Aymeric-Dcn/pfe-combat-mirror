# PFE Combat Mirror — capture de mouvement du boxeur

Projet de fin d'études, Polytech Montpellier (MEA), en collaboration avec le département de Biomedical Engineering de CSULB, l'entreprise australienne [Combat Mirror](https://combatmirror.com/) et le LAAS-CNRS (équipe Gepetto).

**Objectif :** instrumenter un miroir de boxe avec des capteurs de pression (intensité et position des impacts), synchroniser ces données avec la cinématique articulaire du boxeur mesurée par caméras RGB avec [RT-COSMIK](https://github.com/Gepetto/rt-cosmik), puis évaluer l'entraînement par IA (Transformer).

| Livrable | État (27/09/2026) |
|---|---|
| 1. Installation de RT-COSMIK | ✅ Chaîne complète fonctionnelle avec 1 webcam : détection, squelette, modèle biomécanique, angles articulaires en CSV |
| 2. Instrumentation du miroir | ⬜ À démarrer |
| 3. Synchronisation + CSV | 🟡 Côté caméra prêt (`joint_angles.csv`, `markers.csv` avec compteur d'images) |
| 4. Traitement des données (IA) | ⬜ À démarrer |

Le rapport en cours est dans [`docs/rapport/`](docs/rapport/) (LaTeX, PDF compilé inclus).

## Contenu

```
config/cam_params/intrinsics/   calibration de la webcam (format lu par RT-COSMIK main)
rtcosmik/patches/               modifications apportées à RT-COSMIK (à appliquer avec git apply)
scripts/tests/                  tests unitaires : webcam, YOLO, squelette NLF, en-tête des moteurs
scripts/calibration/            calibration intrinsèque (damier sur écran) + recalcul
scripts/analysis/               analyse qualité d'une prise + vidéo avec squelette superposé
scripts/tools/                  export de tout ce qui vit dans le conteneur Docker
results/                        résultats des prises (CSV, graphes ; vidéos hors git)
docs/                           rapport LaTeX, aide-mémoire de session, notes Docker
```

## Démarrage rapide

Environnement : conteneur Docker de [cosmik-dev-container](https://github.com/MaximeSabbah/cosmik-dev-container) (CUDA 12.1, Ubuntu 22.04, ROS 2 Humble, torch 2.4.1), RT-COSMIK `main` du dépôt Gepetto. Voir [`docs/aide_memoire_session.md`](docs/aide_memoire_session.md) pour la procédure complète sous Windows/WSL2.

```bash
# dans le conteneur
cd ~/workspace/ros_ws
git clone https://github.com/Gepetto/rt-cosmik.git RT-COSMIK-main && cd RT-COSMIK-main
git apply /chemin/vers/pfe-combat-mirror/rtcosmik/patches/*.patch     # import torchvision + settings
BATCHES="1" bash scripts/bash/fetch_models.sh                           # poids NLF/YOLO + moteur batch 1
apt-get install -y ffmpeg
cp /chemin/vers/pfe-combat-mirror/config/cam_params/intrinsics/camera_0_intrinsics.yaml \
   config/cam_params/intrinsics/
export YOLO_VERBOSE=False
python3 scripts/python/core/run_pipeline.py --online --cameras 0
```

Puis, sur la prise enregistrée :

```bash
python3 /chemin/vers/pfe-combat-mirror/scripts/analysis/analyze_take.py output/demo_03
bash    /chemin/vers/pfe-combat-mirror/scripts/analysis/overlay_offsets.sh   output/demo_03 "-3 0 3 6 9 12"
```

## Références

- RT-COSMIK : https://github.com/Gepetto/rt-cosmik
- Calibration caméras (LAAS) : https://github.com/Gepetto/cams_calibration
- Publication ROS 2 : https://github.com/Gepetto/rtcosmik_ros
- Conteneur de développement : https://github.com/MaximeSabbah/cosmik-dev-container
