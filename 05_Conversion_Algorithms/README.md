# 05 — Conversion formulas: Alphasense calibration values only

Every gas value uses **only an Alphasense zero and sensitivity**: the sensor's own factory calibration sheet where available, otherwise Alphasense's published datasheet typical values (indicative). No temperature tables, no cross-sensitivity corrections, no density correction, no filtering or smoothing. **A negative result counts as 0**, also in averages. All voltages in mV.

```
H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity     H2S-B4 on ISB
NH3 (ppm) = (WE - WE zero) / sensitivity                         NH3-B1 on ISB
VOC (ppm) = (V - V zero)   / sensitivity                         PIDX-A-040, ppm isobutylene
```

- The H2S line is Alphasense AAN 803-05 Algorithm 3 at the factory calibration temperature, where Alphasense's factor k'T is 1 (AAN 803-05, Table 3).
- The VOC line follows Alphasense AAN 302-04: the PID needs no temperature correction. A voltage below V zero means a sensor fault.
- "WE zero" and "AE zero" are the total zero offsets on the factory sheet.

| File | What it is |
| --- | --- |
| `factory_formulas.py` | The three formulas, Python 3.9+, no dependencies |
| `factory_formulas.js` | The same in JavaScript (Node or browser) |
| `calibration_records.json` | Values in use: NH3-B1+ factory sheet **77840031** (zero 328 mV, 58.624 mV/ppm); H2S-B4 and PIDX-A-040 datasheet typical |
| `calibration_template_to_fill.json` | Blank H2S and VOC factory-sheet records; add them with a later `valid_from` to replace the datasheet values |
| `example_usage.py` | Converts one real station packet |
| `test_factory_formulas.py` | Worked-example checks |

```
python example_usage.py
python -m unittest test_factory_formulas -v
```

| Gas | Formula | Source |
| --- | --- | --- |
| NH3-B1+ | `(A0 mV - 328) / 58.624` ppm | Factory sheet 77840031 |
| H2S-B4 | `((A1 - 350) - (A2 - 350)) / 1.4` ppb | Datasheet typical: Alphasense ISB manual, Table 2 (zero 350/350 mV; 1750 nA/ppm x 0.8 mV/nA) |
| PIDX-A-040 | `(A3 mV - 70) / 55` ppm | Datasheet typical: offset 40-100 mV (midpoint), 55 mV/ppm; below 40 mV = sensor fault |

Datasheet typical values can leave a steady offset in clean air (H2S about -143 to +114 ppb, VOC about +/-0.55 ppm).

This replaces the earlier `h2s_b4.py`, `nh3_b1.py` and `pidx_a040.py` modules, which added temperature tables, cross-sensitivity and density corrections.
