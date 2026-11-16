# Protocole d'étalonnage du plateau de force (prototype 4 capteurs)

**Projet :** PFE Combat Mirror — Polytech Montpellier, MEA
**Auteur :** Aymeric Duchene
**Date :** 16 novembre 2026 (v1)
**Documents associés :** conditionnement des capteurs, `hardware/firmware/nucleo_acq`, `scripts/forceplate`

---

## 1. Objet

Ce protocole décrit comment étalonner le prototype de plateau de force à quatre FlexiForce A201-100 :

1. caractériser et étalonner chaque capteur seul, monté dans son module de coin ;
2. étalonner le plateau assemblé (force totale et position du centre de pression) ;
3. vérifier la réponse à un impact.

Il en ressort un fichier `calibration.json` utilisé par le script d'acquisition, et une fiche de relevés (§ 11).

Les critères d'acceptation reprennent les performances typiques de la fiche technique Tekscan :

| Grandeur | Critère |
|---|---|
| Écart à la droite d'étalonnage | < 3 % de la pleine échelle |
| Hystérésis | < 4,5 % de la pleine échelle |
| Répétabilité | < 2,5 % de la pleine échelle |
| Force totale sur le plateau | erreur < 5 % |
| Centre de pression | erreur < 10 mm |

---

## 2. Matériel

| Matériel | Usage |
|---|---|
| Nucleo F072RB avec le firmware `nucleo_acq`, carte de conditionnement | Acquisition |
| PC avec Python, `pyserial`, `numpy`, `matplotlib` et le script `forceplate.py` | Commandes et calculs |
| Masses connues : disques de musculation, haltères, masses de laboratoire (pesées sur une balance au préalable) | Charges d'étalonnage |
| Plateau de charge rigide (planchette ou disque) posé sur le support haut d'un module | Appliquer les masses sur un seul capteur |
| Pèse-personne ou balance de référence | Charges au-delà des masses disponibles |
| Tournevis de réglage, multimètre | Réglage de RV, mesure de R_F |
| Thermomètre | Relever la température (0,36 %/°C) |
| Mètre ruban, feutre | Tracer la grille de points sur le plateau |

1 kg correspond à 9,81 N. En mode standard, la pleine échelle visée (≈ 445 N) correspond à environ 45 kg. Si les masses disponibles sont plus faibles, la pleine échelle d'étalonnage est la plus grande charge disponible, et les pourcentages ci-dessous s'y rapportent.

**Mode haute force :** les charges jusqu'à 4 400 N (≈ 450 kg) ne s'obtiennent pas avec des masses. Il faut une presse ou une machine d'essai avec capteur de référence (à demander au laboratoire de mécanique). À défaut, ce mode est vérifié par l'essai de chute (§ 9) seulement.

---

## 3. Préparation

1. Flasher le firmware depuis STM32CubeIDE (projet `hardware/firmware/nucleo_acq`, **Run**). La LED verte doit changer d'état toutes les 0,5 s.
2. Placer le cavalier JP1 sur le mode à étalonner (en général position 2, mode standard).
3. Lancer `python forceplate.py -p COMx monitor` et vérifier :
   - V_REF lue conforme au mode (1,03 / 0,51 / 0,10 V) ;
   - VDDA ≈ 3,3 V ;
   - à vide, chaque voie ≈ V_REF ;
   - `gaps=0 bad=0` (aucune trame perdue).
4. Laisser le montage sous tension 10 minutes avant toute mesure, et noter la température.
5. Travailler dans un dossier de données dédié (par exemple `data/etalonnage_AAAAMMJJ/`), dans lequel les fichiers sont écrits.

---

## 4. Conditionnement des capteurs

Les valeurs de répétabilité et d'hystérésis de la fiche ne valent que pour un capteur conditionné. Pour chaque capteur neuf, ou après un démontage :

1. Monter le capteur dans son module, palet et bille en place.
2. Appliquer environ 110 % de la plus forte charge d'essai, la maintenir 3 secondes, puis décharger.
3. Répéter 4 à 5 fois.

---

## 5. Réglage de la pleine échelle (une fois par voie et par mode)

1. Mettre RV_x au maximum.
2. Appliquer la charge maximale d'essai sur le capteur.
3. Tourner RV_x jusqu'à lire **3,0 V** sur la voie dans `monitor`.
4. Décharger : la voie doit revenir près de V_REF.
5. Hors tension, capteur débranché, mesurer au multimètre la résistance de contre-réaction R_F (R_F_x + RV_x, entre la sortie et l'entrée inverseuse de l'ampli). La noter.
6. Remettre sous tension et relancer `monitor --rf <R_F en kΩ>` sous la charge maximale : le script affiche la **résistance du capteur**. La noter.

Cette résistance remplace l'hypothèse de 10 kΩ (`RSFS`) dans les simulations ngspice. Si R_F dépasse 101 kΩ en mode haute force, le potentiomètre doit être remplacé par une valeur plus forte.

---

## 6. Étalonnage de chaque capteur

Un capteur à la fois, module seul posé sur une surface plane et rigide, plateau de charge sur le support haut. La masse du plateau de charge fait partie de la charge.

1. **Tare**, sans charge :
   `python forceplate.py -p COMx tare`
   Le bruit affiché doit rester sous quelques mV ; sinon, le script demande de recommencer.

2. **Paliers croissants**, à 0, 10, 25, 50, 75 et 100 % de la pleine échelle. À chaque palier : poser la masse au centre, attendre 5 secondes, puis :
   `python forceplate.py -p COMx step --sensor 1 --load <N> --dir up`

3. **Paliers décroissants**, de 75 % à 0 %, de la même façon avec `--dir down`.

4. **Répéter** la montée et la descente 3 fois au total, pour mesurer la répétabilité.

5. Passer au capteur suivant (`--sensor 2`, etc.), en refaisant le conditionnement (§ 4) s'il a été démonté.

6. **Calcul :**
   `python forceplate.py fit`
   Pour chaque capteur, le script donne le gain (N/V), l'écart maximal à la droite, l'hystérésis et la répétabilité, en pourcentage de la pleine échelle. Les gains sont écrits dans `calibration.json`.

**En cas de dépassement des critères :** vérifier le centrage du palet sur la zone sensible, la présence de la bille dans le cône, l'absence de frottement du support haut sur les tiges, puis refaire le conditionnement et les paliers.

---

## 7. Dérive sous charge constante

Sur un capteur, avec une charge d'environ 25 % de la pleine échelle :

1. Poser la charge et enregistrer 10 minutes :
   `python forceplate.py -p COMx record -d 600 -o derive_capteur1.csv`
2. Relever la variation entre 10 s et 600 s après la pose.

La fiche annonce moins de 5 % par décade de temps : de 10 s à 600 s (1,8 décade), la dérive doit rester sous ≈ 9 %. Ce relevé fixe la fréquence de la tare en séance. La précharge des modules subit la même dérive.

---

## 8. Étalonnage du plateau assemblé

### 8.1 Montage et précharge

1. Visser les quatre modules sur la planche du bas (gabarit `template_bottom`) et les supports hauts sur la planche du haut (gabarit `template_top`).
2. Poser la planche du haut, chaque bille dans son cône.
3. Serrer les écrous de précharge progressivement, en croix, en surveillant `monitor` : arrêter quand chaque voie indique une petite précharge, à peu près égale sur les quatre coins (de l'ordre de 10 à 20 N). Une précharge forte augmente la dérive et consomme de la gamme.
4. Vérifier que la planche du haut ne bascule pas quand on appuie sur un coin.

### 8.2 Tare et grille de points

1. Plateau vide : `python forceplate.py -p COMx tare`
2. Tracer sur la planche du haut une grille de 9 points : le centre, et les points à ±60 mm en x et en y (axes et positions des capteurs : voir `positions_mm` dans `calibration.json` ; capteur 1 en x > 0, y > 0).
3. Pour chaque point, poser une masse connue (10 kg, puis 20 kg), centrée sur le point, et lancer :
   `python forceplate.py -p COMx point --x <mm> --y <mm> --mass <kg>`
   Le script affiche la force totale et le centre de pression mesurés.
4. **Calcul :**
   `python forceplate.py fitplate`
   Le script corrige les quatre gains par moindres carrés pour que la somme des forces égale le poids et que le centre de pression tombe sur le point. Il affiche les erreurs avant et après correction.

**Critères :** erreur sur la force totale < 5 %, erreur de position < 10 mm.

---

## 9. Vérification dynamique : essai de chute

1. Lâcher une masse connue m (par exemple un médecine-ball de 3 kg) d'une hauteur connue h, au centre du plateau, en enregistrant :
   `python forceplate.py -p COMx record -d 10 -o chute_h50.csv`
2. Dans le fichier, calculer l'impulsion du premier choc, I = ∫ F dt, et la comparer à la quantité de mouvement à l'impact, m·√(2gh) :
   - I doit être compris entre m·√(2gh) (aucun rebond) et 2·m·√(2gh) (rebond parfait) ;
   - le centre de pression au pic doit tomber au point d'impact.
3. Répéter à plusieurs hauteurs (25, 50, 100 cm) et vérifier qu'aucune voie ne sature (sortie < 3,25 V). En cas de saturation, passer en mode haute force.

---

## 10. En séance

- **Tare** à chaque démarrage, plateau vide, et avant chaque série.
- Vérifier au démarrage que le mode affiché par le script correspond au mode étalonné. Le script prévient en cas d'écart : chaque mode a son propre étalonnage.
- **Contrôle hebdomadaire** avec une masse connue au centre (`point`). Un écart supérieur à 5 % impose de refaire le § 6.
- Les capteurs s'usent plus vite sous de fortes charges que dans l'essai d'endurance du constructeur (3 millions d'appuis à 22 N) : prévoir de remplacer un capteur dont l'étalonnage dérive, puis refaire les § 4 à 8.
- Étalonner et mesurer à la même température, à 5 °C près.

---

## 11. Fiche de relevés

**Date :** ……… **Température :** ……… °C **Mode (JP1) :** ……… **V_REF lue :** ……… V **Opérateur :** ………

### Réglage des voies

| Voie | Charge max (N) | R_F mesurée (kΩ) | R capteur à charge max (kΩ) | V sortie à charge max (V) |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |

### Résultats de `fit`

| Voie | Gain (N/V) | Écart à la droite (% PE) | Hystérésis (% PE) | Répétabilité (% PE) | Conforme |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |

### Plateau (`fitplate`)

| | Erreur force max (%) | Erreur position max (mm) |
|---|---|---|
| Avant correction | | |
| Après correction | | |

Corrections de gain : ……… / ……… / ……… / ………

### Dérive et chute

| Essai | Résultat |
|---|---|
| Dérive 10 s → 600 s, capteur … | ……… % |
| Chute m = … kg, h = … cm : impulsion / m·√(2gh) | ……… |
| Chute : écart du centre de pression | ……… mm |
