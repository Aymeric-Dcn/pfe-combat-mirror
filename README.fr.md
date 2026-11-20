# PFE Combat Mirror — capture de mouvement du boxeur

*[English version](README.md)*

Projet de fin d'études, Polytech Montpellier (MEA), en collaboration avec le département de Biomedical Engineering de CSULB, l'entreprise australienne [Combat Mirror](https://combatmirror.com/) et le LAAS-CNRS (équipe Gepetto).

**Objectif :** instrumenter un miroir de boxe avec des capteurs de pression (intensité et position des impacts), synchroniser ces données avec la cinématique articulaire du boxeur mesurée par caméras RGB avec [RT-COSMIK](https://github.com/Gepetto/rt-cosmik), puis évaluer l'entraînement par IA (Transformer).

| Livrable | État (20/11/2026) |
|---|---|
| 1. Installation de RT-COSMIK | **Terminé.** Chaîne complète avec 1 webcam (détection, squelette, modèle biomécanique, angles articulaires en CSV) ; temps réel à 30 images/s sur la machine Debian de Polytech |
| 2. Instrumentation du miroir | **En cours.** Prototype de plateau de force à 4 FlexiForce : module de coin (3D), conditionnement (schéma, simulations, validé sur breadboard), firmware Nucleo et script PC fonctionnels ; capteurs en commande |
| 3. Synchronisation + CSV | **En cours.** Côté caméra prêt ; les trames du plateau portent un compteur d'échantillons à 2 kHz ; déclenchement matériel des caméras prévu (TIM1 de la Nucleo) |
| 4. Traitement des données (IA) | À démarrer |

Le rapport en cours est dans [`docs/rapport/`](docs/rapport/) (LaTeX, PDF compilé inclus).

## Contenu

```
config/cam_params/intrinsics/   calibration de la webcam (format lu par RT-COSMIK main)
rtcosmik/patches/               modifications apportées à RT-COSMIK (à appliquer avec git apply)
scripts/tests/                  tests unitaires : webcam, YOLO, squelette NLF, en-tête des moteurs
scripts/calibration/            calibration intrinsèque (damier sur écran) + recalcul
scripts/analysis/               analyse qualité d'une prise + vidéo avec squelette superposé
scripts/tools/                  installation de RT-COSMIK main + export du conteneur
scripts/forceplate/             plateau de force : acquisition, affichage et étalonnage (PC)
docker/                         image dérivée de celle de cosmik-dev-container
results/                        résultats des prises (CSV, graphes ; vidéos hors git)
hardware/3d/                    pièces du plateau de force (OpenSCAD) : module de coin, banc 4 capteurs
hardware/simulation/            simulation du conditionnement des capteurs (ngspice)
hardware/electronics/           schéma du conditionnement des capteurs (KiCad)
hardware/firmware/              firmware d'acquisition Nucleo F072RB (4 capteurs, 2 kHz)
docs/                           guide d'installation (EN/FR), rapport d'avancement et protocole d'étalonnage (FR)
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

## Plateau de force (prototype)

Quatre capteurs FlexiForce A201, un sous chaque coin d'une plaque, donnent la force de l'impact (somme) et sa position (centre de pression).

```
FlexiForce -> conditionnement à ampli-op (MCP6004, 3,3 V) -> filtre RC 480 Hz -> ADC Nucleo F072RB (2 kHz) -> USB -> forceplate.py
```

| Partie | Emplacement |
|---|---|
| Module de coin et banc d'essai 300 mm (OpenSCAD, paramétrique) | [`hardware/3d/`](hardware/3d/) |
| Schéma du conditionnement (KiCad) et fiches de test sur banc | [`hardware/electronics/`](hardware/electronics/) |
| Simulations du circuit (ngspice) | [`hardware/simulation/`](hardware/simulation/) |
| Firmware d'acquisition (STM32CubeIDE, au niveau des registres) | [`hardware/firmware/nucleo_acq/`](hardware/firmware/nucleo_acq/) |
| Acquisition, affichage et étalonnage côté PC | [`scripts/forceplate/`](scripts/forceplate/) |
| Protocole d'étalonnage | [`docs/protocole_etalonnage.md`](docs/protocole_etalonnage.md) |

Démarrage rapide : importer `hardware/firmware/nucleo_acq` dans STM32CubeIDE et flasher la carte (Run), puis :

```bash
pip install pyserial numpy matplotlib
cd scripts/forceplate
python forceplate.py -p COM4 monitor     # ou /dev/ttyACM0 ; --sim pour essayer sans la carte
python forceplate.py -p COM4 live
```

## Références

- RT-COSMIK : https://github.com/Gepetto/rt-cosmik
- Calibration caméras (LAAS) : https://github.com/Gepetto/cams_calibration
- Publication ROS 2 : https://github.com/Gepetto/rtcosmik_ros
- Conteneur de développement : https://github.com/MaximeSabbah/cosmik-dev-container
