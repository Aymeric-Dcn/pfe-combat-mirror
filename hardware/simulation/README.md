# Simulation of the FlexiForce conditioning circuit (ngspice)

One measurement channel (the 4 channels are identical), with the V_REF divider and the JP1 jumper.

| File | Content |
|---|---|
| `conditionnement.inc` | Circuit, parameters and simplified op-amp model (shared) |
| `sim_dc.cir` | Sweep of the sensor conductance: linearity, offset, saturation |
| `sim_ac.cir` | Frequency response of the chain (amplifier + filter) |
| `sim_tran.cir` | Response to a 15 ms impact |
| `sim_worstcase.cir` | Same impact on an ideal sensor, a sensor with hysteresis, and a sensor with hysteresis + sensitivity error (datasheet values) |

## Running

On Windows, ngspice is in `C:\pfe\tools\Spice64` (outside the repository):

- `run_all_sims.bat`: runs the 3 simulations in batch mode and writes `sim_*.log` (measurements) and `*_result.csv`.
- `run_sim_dc.bat`, `run_sim_ac.bat`, `run_sim_tran.bat`: interactive run with plots (type `quit` to close).

On Linux (e.g. the Polytech Debian machine):

```
sudo apt install ngspice
cd hardware/simulation
ngspice sim_dc.cir
```

## Parameters (top of `conditionnement.inc`)

- `SEL`: JP1 position (1 = sensitive, 2 = standard, 3 = high force).
- `RSFS`: sensor resistance at the full-scale force of the chosen mode. **Hypothesis of 10 kΩ**, to be replaced by the measured value. In high-force mode, RSFS is the resistance at ~4,400 N, much lower than in standard mode.
- `RF` is computed automatically for a 3.0 V full-scale output.

If `RSFS` is changed, adapt the sweep range in `sim_dc.cir` (up to about 1.2 / RSFS).

## Expected results (SEL = 2, RSFS = 10 kΩ)

| Measurement | Expected value |
|---|---|
| V_REF | 0.505 V |
| RF | 49.4 kΩ |
| `v_zero` (no load) | ≈ 0.505 V |
| `v_fs` (full scale, 1e-4 S) | ≈ 3.00 V |
| `g_sat` (output at 3.2 V) | ≈ 1.08e-4 S, i.e. about 108 % of full scale |
| `f_cut` | ≈ 480 Hz |
| `v_peak_adc` (80 % impact) | ≈ 2.50 V |

Worst case (`sim_worstcase.cir`, same settings):

| Measurement | Expected value |
|---|---|
| `err_h_max` (hysteresis 4.5 %) | ≈ 4.5 % of full scale, during unloading |
| `err_w_max` (hysteresis + 5.5 % sensitivity) | ≈ 7 % of full scale, during unloading |
| `v_peak_worst` | ≈ 2.61 V (vs 2.50 V ideal, +4.4 % of full scale) |

The datasheet values (Tekscan FlexiForce A201 Rev A, typical performance) are parameters at the top of the file: `HYS` (hysteresis, 0.045) and the factor 1.055 of `Bgw` (sensitivity error of 5.5 %). The hysteresis model is a simple shape (zero at rest and at the peak, maximum at mid-load), not a measured curve.

Large deviations from these values point to a problem in the netlist or the model.

**Note for the high-force mode:** with SEL = 3 and RSFS = 10 kΩ, RF would be 281 kΩ, beyond the 101 kΩ of the trimmer. In that mode RSFS must be the (lower) resistance at ~4,400 N; if the computed RF exceeds 101 kΩ, a larger trimmer is needed.

## Using the Microchip model

The provided op-amp is simplified (1 MHz GBW, rail-to-rail output, no offset or noise). To use the real model:

1. Download the MCP6004 SPICE model from the Microchip product page.
2. In `conditionnement.inc`, replace the `opamp_rr` subcircuit with `.include <model_file>`.
3. Replace `opamp_rr` with the subcircuit name of the model in the `XU1` line, **checking the pin order** given in the model file header (usually: in+, in−, V+, V−, out).

## Using it in KiCad

KiCad's simulator (Inspect → Simulator) is based on ngspice. Once the schematic is entered in KiCad, the same analyses can be run there: the sensor becomes a resistor whose value is swept (or a behavioural source), and the `.dc`, `.ac` and `.tran` directives are added as text on the schematic.
