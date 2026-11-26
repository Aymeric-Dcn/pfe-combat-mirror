# Notice de montage du banc d'essai 4 capteurs

Banc de 300 × 300 mm : une plaque de base, une plaque de frappe et un module de coin par angle. Modèles : `module_coin.scad` (module) et `test_rig.scad` (banc et gabarits de perçage).

## 1. Chaîne d'effort d'un module

De bas en haut : plaque de base, embase, capteur FlexiForce, palet, bille d'acier, support haut (cône), plaque de frappe.

Les deux tiges filetées M5 et leurs ressorts assurent une précharge. Les ressorts sont beaucoup plus souples que le capteur : ils servent seulement à mettre la pile en contact et à équilibrer les 4 coins. Ils ne reprennent quasiment pas l'effort de frappe.

## 2. Pièces

### Pièces imprimées, par module

| Pièce | Rôle |
|---|---|
| Embase (`base`) | vissée sur la plaque de base, écrous M5 encastrés dessous |
| Bague (`ring`) | loge le capteur et guide le palet |
| Palet (`puck`) | transmet l'effort de la bille au capteur, empreinte sphérique dessus |
| Support haut (`upper_support`) | vissé sous la plaque de frappe, cône de centrage pour la bille |

Le palet doit être la version **bille 10 mm** (`module_coin_puck_bille10.stl`).

### Quincaillerie

| Élément | Par module | Total (4 modules) |
|---|---|---|
| Tige filetée M5, longueur 56 mm | 2 | 8 |
| Écrou M5 | 4 | 16 |
| Ressort RS PRO 751-584 (Ø ext. 9 mm, longueur libre 28,5 mm) | 2 | 8 |
| Vis M3 × 8 (fixation de la bague) | 2 | 8 |
| Vis à bois Ø 4, tête fraisée, longueur environ 16 mm (embase) | 4 | 16 |
| Vis à bois Ø 4, tête de diamètre au plus 8,5 mm, longueur environ 20 mm (support haut) | 4 | 16 |
| Bille d'acier Ø 10 mm | 1 | 4 |

La longueur de 56 mm des tiges se mesure depuis le dessous de l'embase.

## 3. Préparation des plaques

1. Ouvrez `test_rig.scad` dans OpenSCAD, puis choisissez `template_bottom` et `template_top`.
2. Faites F6, puis exportez en SVG ou en DXF.
3. Imprimez les gabarits **à 100 %**, sans « ajuster à la page ».
4. Scotchez chaque gabarit sur sa plaque et pointez les trous.
5. Percez avant perçage à Ø 2,5 à 3 mm pour les vis à bois.

Les gabarits sont symétriques : inutile de les retourner.

## 4. Montage d'un module

### Partie basse

1. **Écrous.** Enfoncez un écrou M5 dans chacune des 2 empreintes hexagonales, sous l'embase.
2. **Tiges.** Vissez chaque tige par le dessus jusqu'à ce qu'elle affleure le dessous de l'embase, sans dépasser, sinon l'embase ne repose pas à plat. Une goutte de frein filet ou de colle évite que la tige tourne ensuite.
3. **Fixation de l'embase.** Vissez l'embase sur la plaque de base avec les 4 vis à bois fraisées. **Orientation :** le canal de sortie de la queue du capteur pointe vers le centre de la plaque, là où se trouvent la Nucleo et le shield.
4. **Capteur.** Posez la partie ronde du FlexiForce au centre de l'embase, face sensible vers le haut, avec la queue dans l'axe du canal.
5. **Bague.** Posez la bague par-dessus : la pastille du capteur se loge dans la poche, la queue dans le canal. Fixez-la avec 2 vis M3 × 8, qui se taraudent dans les avant-trous de l'embase.
   - Serrez sans forcer. Le capteur n'est pas pincé par la bague, il est seulement tenu en place.
   - Vérifiez que la queue sort librement et n'est pas cisaillée au bord du canal.
6. **Palet.** Glissez le palet dans l'alésage de la bague, empreinte sphérique vers le haut. Il doit coulisser librement et reposer à plat sur le capteur.
7. **Bille.** Posez la bille dans l'empreinte du palet.

### Partie haute

8. **Supports hauts.** Vissez les 4 supports hauts sous la plaque de frappe, aux positions du gabarit `template_top`. Les vis passent par les lamages, depuis le dessous du support. Orientez les oreilles comme les embases, pour que les trous des oreilles tombent sur les tiges.

## 5. Assemblage des deux plaques et précharge

1. Retournez la plaque de frappe, supports vers le bas.
2. Descendez-la en enfilant les oreilles sur les 8 tiges. Chaque cône vient coiffer sa bille.
3. Sur chaque tige, enfilez un ressort au-dessus de l'oreille, puis un écrou M5.
4. Serrez les écrous **en croix, un demi-tour à la fois**, jusqu'à ce que chaque ressort soit légèrement comprimé.
5. Branchez la carte et lancez `forceplate.py monitor`. Ajustez les écrous jusqu'à obtenir **une tension de repos proche sur les 4 voies**, puis faites la tare.

Valeurs de contrôle : entre les deux plaques, l'écart est d'environ 49 mm. Entre le support haut et la bague, il reste environ 4 mm de jeu, qui ne doit jamais se refermer.

## 6. Points de vigilance

- **Jamais d'appui sans bille.** Sans bille, le support haut porte directement sur le palet ou la bague, et l'effort ne passe plus par le capteur.
- **Ne pliez pas la queue du capteur** à angle vif en sortie de bague. Faites-la courir à plat vers le connecteur.
- **Ne serrez pas trop la précharge.** Au-delà d'un léger contact, le capteur est déjà chargé au repos, et une partie de sa plage de mesure est perdue.
- Avant de serrer définitivement, **vérifiez que chaque palet coulisse librement**.
