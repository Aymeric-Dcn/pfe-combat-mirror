# Force plate: PC acquisition and calibration

Reads the frames of the Nucleo firmware (`hardware/firmware/nucleo_acq`), shows the forces live, records CSV files and computes the calibration.

## Install

```
pip install pyserial numpy matplotlib
```

The Nucleo appears as *STMicroelectronics STLink Virtual COM Port (COMx)* in the Windows device manager (`/dev/ttyACM0` on Linux).

## Commands

Run them from a data folder: the calibration (`calibration.json`), the steps (`steps.csv`) and the plate points (`points.csv`) are written in the current folder.

```
python forceplate.py -p COM5 monitor              # values 4 times per second
python forceplate.py -p COM5 monitor --rf 49.4    # + sensor resistance, R_F in kOhm
python forceplate.py -p COM5 live                 # live plot and centre of pressure
python forceplate.py -p COM5 record -d 30 -o jab.csv
python forceplate.py -p COM5 tare                 # plate unloaded
python forceplate.py -p COM5 step --sensor 1 --load 98.1 --dir up
python forceplate.py fit                          # gains from steps.csv
python forceplate.py -p COM5 point --x 50 --y -50 --mass 10
python forceplate.py fitplate                     # gain corrections from points.csv
python forceplate.py drop chute.csv --mass 3 --height 50 --x 0 --y 0 --plot chute.png
```

Replace `-p COM5` with `--sim` to try any command without the board (simulated data: one 600 N punch per second after 2.5 s at rest).

## Calibration file

```text
{
  "positions_mm": [[105, 105], [-105, 105], [105, -105], [-105, -105]],
  "offset_v": [...],          tare
  "gain_n_per_v": [...],      fit
  "plate_correction": [...]   fitplate
}
```

`positions_mm` gives the sensor positions from the plate centre (test rig: 300 mm plates, modules 45 mm from the edges). Change it for another plate. Force: `F_k = gain_k * correction_k * (V_k - offset_k)`; the centre of pressure is the force-weighted mean of the positions, computed above 20 N.

The script warns when V_REF (the JP1 mode) differs from the one used for the tare or the fit: each mode needs its own calibration.

## CSV columns

`t_s` (from the sample counter, 0.5 ms per sample), `sample`, `v1`..`v4`, `vref`, `vdda` (V), then, once calibrated, `f1`..`f4`, `f_total` (N) and `x_mm`, `y_mm` (centre of pressure).
