# D'où vient le conteneur, et comment le transporter

## Comment l'image a été construite

Le dépôt [cosmik-dev-container](https://github.com/MaximeSabbah/cosmik-dev-container) ne contient **pas** d'image toute faite : il ne contient que la recette, le `.devcontainer/Dockerfile`. Un `docker build -t mmpose_image .` :

1. **télécharge une seule image de base** depuis Docker Hub : `nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04`, qui apporte Ubuntu 22.04, CUDA 12.1 et cuDNN 8 ;
2. **construit tout le reste en local**, couche par couche :
   - ROS 2 Humble (dépôts apt ROS) ;
   - torch 2.4.1 et torchvision 0.19.1 (cu121), ultralytics, opencv, meshcat, quadprog, onnx, avec `numpy==1.26.4` épinglé ;
   - compilation depuis les sources, versions figées : BLASFEO, FATROP, CasADi 3.7.2, eigenpy 3.12, coal 3.0.2, Pinocchio 3.9.0 (avec CasADi), example-robot-data (modèle humain), acados ;
   - clonage de `MaximeSabbah/RT-COSMIK` (branche `main`, commit `bd80b0d`) dans `/root/workspace/ros_ws/RT-COSMIK`.

C'est pour ça que l'image locale `mmpose_image` fait environ 42 Go et que sa construction est longue (compilations gourmandes en RAM, d'où la recommandation d'un swap de 32 Go dans le README de Maxime). Aucun serveur ne fournit la « grosse image » : elle n'existe que sur la machine qui l'a construite.

Notre conteneur de travail (`90034be366af`) = cette image + nos ajouts faits à la main (ffmpeg, RT-COSMIK `main` de Gepetto, poids, moteur TensorRT, calibration, scripts). Sauvegarde locale : `cosmik-backup:2026-09-26`, puis `cosmik-backup:2026-09-27-demo`.

## Trois façons de transporter l'environnement

| Méthode | Principe | Taille / durée | Quand l'utiliser |
|---|---|---|---|
| **Reconstruire** (recommandé) | `docker build` du Dockerfile de Maxime sur la nouvelle machine, puis ce dépôt pour nos ajouts | Quelques Go téléchargés, construction longue | Machine Debian de Polytech, et toute nouvelle machine |
| **Archive** | `docker save -o cosmik.tar cosmik-backup:...` puis `docker load -i cosmik.tar` | Environ 20 Go de contenu (plus si non compressé) | Sauvegarde froide sur disque externe |
| **Registre** | `docker push` vers Docker Hub, GHCR ou GitLab LAAS, puis `docker pull` | Environ 20 Go à envoyer | Seulement si plusieurs personnes doivent partager exactement la même image |

Attention : le moteur TensorRT (`*.engine`) est lié au GPU et à la version de TensorRT. Il doit être **régénéré** sur une autre machine (`BATCHES="1" bash scripts/bash/fetch_models.sh`), quelle que soit la méthode.

## Recréer notre environnement

On ne maintient pas notre propre Dockerfile complet : on part de l'image de Maxime et on ajoute nos quelques éléments (ffmpeg, RT-COSMIK `main` de Gepetto, nos deux patchs, la calibration). Deux options équivalentes :

- **Dans un conteneur existant** :
  ```bash
  git clone https://github.com/Aymeric-Dcn/pfe-combat-mirror.git /root/pfe-combat-mirror
  bash /root/pfe-combat-mirror/scripts/tools/setup_rtcosmik_main.sh
  ```
- **Comme image dérivée** : `docker/Dockerfile` part de `mmpose_image` et exécute le même script. Les poids sont téléchargés au premier lancement, parce que le moteur TensorRT doit être construit sur le GPU :
  ```bash
  docker build -f docker/Dockerfile -t pfe_cosmik .
  ```

Le script peut être relancé sans risque : il ne refait que ce qui manque.

## Lancement sur Linux natif (Debian de Polytech)

Commande du README de Maxime. `--net=host` rend Meshcat accessible directement, et `-v /dev:/dev --privileged` expose toutes les caméras, sans usbipd :

```bash
xhost +local:
docker run -it --net=host --gpus all --privileged \
  --device-cgroup-rule "c 81:* rmw" --device-cgroup-rule "c 189:* rmw" \
  -e DISPLAY=$DISPLAY -v /dev:/dev -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $HOME/pfe-combat-mirror:/root/pfe \
  mmpose_image
```

Le `-v $HOME/pfe-combat-mirror:/root/pfe` (ajout de notre part) monte ce dépôt dans le conteneur : ce qui y est écrit reste sur la machine hôte.
