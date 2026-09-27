# PFE Combat Mirror — capture de mouvement du boxeur

*[English version](README.md)*

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
scripts/tools/                  installation de RT-COSMIK main + export du conteneur
docker/                         image dérivée de celle de cosmik-dev-container
results/                        résultats des prises (CSV, graphes ; vidéos hors git)
docs/                           guide d'installation (EN/FR), rapport d'avancement (FR)
```

## Démarrage rapide

Environnement : conteneur Docker de [cosmik-dev-container](https://github.com/MaximeSabbah/cosmik-dev-container) (CUDA 12.1, Ubuntu 22.04, ROS 2 Humble, torch 2.4.1), RT-COSMIK `main` du dépôt Gepetto. Installation complète, particularités Windows/WSL 2 et dépannage : [`docs/SETUP.fr.md`](docs/SETUP.fr.md).

```bash
# dans le conteneur
git clone https://github.com/Aymeric-Dcn/pfe-combat-mirror.git /root/pfe-combat-mirror
bash /root/pfe-combat-mirror/scripts/tools/setup_rtcosmik_main.sh
cd ~/workspace/ros_ws/RT-COSMIK-main
export YOLO_VERBOSE=False
python3 scripts/python/core/run_pipeline.py --online --cameras 0
```

Puis, sur la prise enregistrée :

```bash
python3 /root/pfe-combat-mirror/scripts/analysis/analyze_take.py output/demo_03
bash    /root/pfe-combat-mirror/scripts/analysis/overlay_offsets.sh output/demo_03 "0 0.5 1 1.5 2"
```

## Références

- RT-COSMIK : https://github.com/Gepetto/rt-cosmik
- Calibration caméras (LAAS) : https://github.com/Gepetto/cams_calibration
- Publication ROS 2 : https://github.com/Gepetto/rtcosmik_ros
- Conteneur de développement : https://github.com/MaximeSabbah/cosmik-dev-container
