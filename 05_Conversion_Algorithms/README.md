# 05 — Conversion formulas: Alphasense factory calibration only

Every gas value uses **only the zero and sensitivity printed on the sensor's Alphasense factory calibration sheet**. No temperature tables, no cross-sensitivity corrections, no density correction, no filtering or smoothing. All voltages in mV.

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
| `calibration_records.json` | Factory sheets in use: NH3-B1+ **77840031** (zero 328 mV, 58.624 mV/ppm) |
| `calibration_template_to_fill.json` | Blank H2S and VOC records, to fill from their factory sheets |
| `example_usage.py` | Converts one real station packet |
| `test_factory_formulas.py` | Worked-example checks |

```
python example_usage.py
python -m unittest test_factory_formulas -v
```

Only the NH3 factory sheet (77840031) exists today: `NH3 (ppm) = (A0 mV - 328) / 58.624`. H2S and VOC give no value until their factory sheets are entered.

This replaces the earlier `h2s_b4.py`, `nh3_b1.py` and `pidx_a040.py` modules, which added temperature tables, cross-sensitivity and density corrections.
