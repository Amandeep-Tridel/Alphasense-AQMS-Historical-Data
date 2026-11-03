# 05 — Conversion formulas: Alphasense method only

Every gas value uses **a zero and a sensitivity, by Alphasense's method only**: the sensitivity from the sensor's factory calibration sheet (datasheet typical for VOC); the H2S and NH3 zeros from a **site zero**, the station's own output in clean air (AAN 803-05 "Initial calibration"; Alphasense's advice of Nov 2026: the cleanest part of the day). No temperature tables, no cross-sensitivity corrections, no density correction, no filtering or smoothing. **A negative result counts as 0**, also in averages. All voltages in mV.

```
H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity     H2S-B4 on ISB
NH3 (ppm) = (WE - WE zero) / sensitivity                         NH3-B1 on ISB
VOC (ppm) = (V - V zero)   / sensitivity                         PIDX-A-040, ppm isobutylene
```

- The H2S line is Alphasense AAN 803-05 Algorithm 3 at 20 °C, where its factor k'T is 1 (AAN 803-05, Table 3). The NH3 line is Algorithm 4 with the AE left out (3-electrode sensor).
- A channel at ≥ 2550 mV or ≤ 5 mV is stuck (unplugged, no power, shorted): no number (`channel_at_rail`).
- Temperature correction (needs the temperature at the top of the sensor; at 20 °C nothing changes):
  - `sensitivity_pct`: sensitivity at that temperature, for all three sensors, from the datasheet charts (H2S-B4 Fig. 1, NH3-B1 Fig. 2, approximate) and, for the PIDX-A-040, the ideal gas law its datasheet states (about 6 % low at 40 °C). Divide by `sensitivity × sensitivity_pct / 100`.
  - `aan803_factor` + `aan803_corrected_we`: AAN 803-05 Algorithms 1–4 with the H2S-B4 Table 3 factors, for the H2S zero; they also need the ISB electronic offsets. k''T is in nA, so Algorithm 4 multiplies it by the board gain (mV/nA).
- The VOC line uses the PIDX-A-040 datasheet's zero and sensitivity. Its output follows the ideal gas law (datasheet Fig. 2), so it reads lower when hot; AAN 302-04's "ignore temperature" is about the older PID-A1/PID-AH. A voltage below V zero means a sensor fault.
- "WE zero" and "AE zero" are the total zero offsets (board offset and sensor zero together).

| File | What it is |
| --- | --- |
| `factory_formulas.py` | The three formulas, rail check and AAN 803-05 algorithms, Python 3.9+, no dependencies (same as the handover package's `alphasense_formulas.py`, plus `no_negative`) |
| `factory_formulas.js` | The same in JavaScript (Node or browser) |
| `calibration_records.json` | In use from 28 Oct 2026: H2S-B4 site zero (458 / 359 mV) with factory-sheet 1.727952 mV/ppb; NH3-B1+ **77840031** site zero (420 mV) with factory-sheet 58.624 mV/ppm; PIDX-A-040 datasheet typical. The factory-zero records are kept for history |
| `calibration_template_to_fill.json` | Blank VOC factory-sheet record; add it with a later `valid_from` to replace the datasheet values |
| `example_usage.py` | Converts one real station packet |
| `test_factory_formulas.py` | Worked-example checks |

```
python example_usage.py
python -m unittest test_factory_formulas -v
```

| Gas | Formula | Source |
| --- | --- | --- |
| NH3-B1+ | `(A0 mV - 420) / 58.624` ppm | Site zero 420 mV; sensitivity from factory sheet 77840031 (its zero: 328 mV) |
| H2S-B4 | `((A1 - 458) - (A2 - 359)) / 1.727952` ppb | Site zero 458 / 359 mV; sensitivity from the factory sheet (its zeros: 395 / 362 mV; sheet example OP1 0.600 V, OP2 0.300 V -> 0.1545 ppm) |
| PIDX-A-040 | `(A3 mV - 70) / 55` ppm | Datasheet typical: offset 40-100 mV (midpoint), 55 mV/ppm; below 40 mV = sensor fault |

The site zeros are the median output from 02:00 to 05:00 Dubai time on five nights (29 Oct – 3 Nov 2026, 899 readings). With the factory zeros, the same clean air read 1.57 ppm NH3 and 38 ppb H2S. The station reads highest at night and lowest in office hours (temperature, not gas), so with the night zero, daytime values show 0 until temperature correction is switched on.

The VOC datasheet typical values can leave a steady offset in clean air (about +/-0.55 ppm).

This replaces the earlier `h2s_b4.py`, `nh3_b1.py` and `pidx_a040.py` modules, which added temperature tables, cross-sensitivity and density corrections.
