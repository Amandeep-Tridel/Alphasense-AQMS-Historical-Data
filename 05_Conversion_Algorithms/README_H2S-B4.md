# H2S-B4 — hydrogen sulfide

`h2s_b4.py` converts raw logger output into hydrogen sulfide concentration in
**ppb**.

Standalone file, stdlib only, Python 3.9+.

```bash
python h2s_b4.py        # self-test against the raw fixture
```

Of the three sensors on the station this is the capable one: a genuine ppb-class
instrument with 1 ppb noise, designed for air-quality networks. It is also the
one whose compensation is most involved, and the one Alphasense left a gap in.

---

## ⚠️ Read this first: the coefficient table does not exist

Alphasense Application Note **AAN 803-05** is the temperature-compensation
method for 4-electrode sensors. Its **Table 2** recommends **algorithm 1** for
H2S B-type sensors.

Its **Table 3**, which holds the actual coefficient values, covers:

> NO-A4, NO-B4, NO2-A43F, NO2-B43F, OX-A431, OX-B431, CO-A4, CO-B4, SO2-A4, SO2-B4

**There is no H2S row.** The note tells you which algorithm to use and then does
not give you the numbers for it.

So `N_T_PLACEHOLDER` in the module is *mine*, not Alphasense's. It was invented
so the code runs and can be round-trip tested. Every reading computed with it
carries `COEFF_UNVERIFIED`, and the default coefficient set is literally named
`"PLACEHOLDER - fixture ground truth, not Alphasense data"`.

**Before production, do one of:**

1. Ask Alphasense for the H2S-B4 `n_T` table. AAN 110 explicitly says to
   "consult Alphasense for specific temperature correction data", so this is the
   supported route.
2. Fit your own from a zero-air temperature soak (procedure below).

Then pass it with `verified=True` and the flag clears.

---

## How the sensor works

Four electrodes sit in an electrolyte. H2S diffusing in reacts at the **working
electrode (WE)**, releasing electrons — that current is proportional to
concentration, about **2 nA per ppb**.

Two problems follow.

**The current is tiny.** 2 nA/ppb is a billionth of an amp. An Alphasense **ISB**
(Individual Sensor Board) converts it to a voltage you can actually measure.

**The sensor drifts with temperature.** In clean air it still produces a current,
and that background moves by **−120 to −160 nA** between 20 °C and 50 °C. At
2 nA/ppb that is a phantom **60–80 ppb** appearing when the sun comes out.

The fix is the **auxiliary electrode (AE)** — an identical electrode in the same
electrolyte, buried where gas cannot reach it. It feels temperature but never
sees H2S, so it is a control:

```
WE = real gas signal + temperature drift
AE =                   temperature drift
                       ───────────────── subtract (scaled)
     real gas signal
```

The scaling factor is `n_T`, and it is exactly the ratio of the two electrodes'
total zeros at that temperature. Which is the number Table 3 does not print.

---

## The four algorithms

All four from AAN 803-05 Table 1, implemented verbatim:

```
1:  WE_c = (WE_u − WE_e) − n_T  × (AE_u − AE_e)
2:  WE_c = (WE_u − WE_e) − k_T  × (WE_0/AE_0) × (AE_u − AE_e)
3:  WE_c = (WE_u − WE_e) − (WE_0 − AE_0) − k'_T × (AE_u − AE_e)
4:  WE_c = (WE_u − WE_e) − WE_0 − k''_T
```

then `ppb = WE_c / sensitivity(T)`.

| # | Approach | Fails when |
|---|---|---|
| 1 | scale AE by one factor | AE term has the opposite sign to `n_T`, or dwarfs the WE term |
| 2 | scale by the ratio of the two zeros | `AE_0` is zero (division) or opposite in sign to `WE_0` |
| 3 | avoids dividing by `AE_0` | `AE_0` opposite in sign to, or far from, `WE_0` |
| 4 | ignores the AE entirely | `WE_0` or `k''_T` far from `WE_u` |

Table 2's suggestion for H2S: **B-type → algorithm 1**, alternative 2.
(A-type is the reverse: suggested 2, alternative 1.)

But the note openly invites you to try all four. **Choose empirically**: soak the
sensor in zero air across your temperature range and keep whichever algorithm
holds the flattest zero. That is a measurement, not a reading-comprehension
exercise.

### Coefficients are passed as a set, not a dict

Each algorithm needs its **own** table. `n_T` is a ratio near 1; `k''_T` is a
millivolt offset in the hundreds. Hand algorithm 4 the `n_T` table and you get a
confident wrong answer, not an error — I hit exactly this while writing the
module. So:

```python
coeffs = h2s_b4.CoefficientSet(
    source="Alphasense email 2026-09-20",   # provenance; fill in honestly
    verified=True,
    n_t={-30: ..., -20: ..., ...},          # algorithm 1
    k_t={...},                              # algorithm 2, if you have it
)

r = h2s_b4.compute(we, ae, t_c, cal, algorithm=1, coeffs=coeffs)
```

Ask for an algorithm whose table you never supplied and it refuses.

---

## Quick start

```python
import h2s_b4

cal = h2s_b4.Calibration(
    serial="H2S-B4-001",
    we_e=253.1, ae_e=248.7,     # mV, ISB board label
    we_0=-40.2, ae_0=-33.5,     # mV, sensor certificate
    sens_mv_per_ppb=0.112,      # mV/ppb, sensor certificate
)

r = h2s_b4.compute(we_counts, ae_counts, head_t_c, cal,
                   algorithm=1, coeffs=my_coeffs)

if r.usable:
    publish(r.ppb, r.ugm3())    # 1 ppb = 1.393 µg/m³ at 25 °C
else:
    log(h2s_b4.describe(r.flags))
```

Two raw channels — working **and** auxiliary electrode. Some certificates quote
*total* zero offsets instead of sensor zeros; pass `we_t`/`ae_t` and the module
derives the rest.

---

## Calibration constants

| Field | Units | Where it comes from |
|---|---|---|
| `we_e`, `ae_e` | mV | **ISB board label** — the board's own offset with no sensor fitted. Alphasense sets these 200–300 mV deliberately, so a negative sensor current still lands in positive voltage territory. |
| `we_0`, `ae_0` | mV | **sensor certificate** — what this unit outputs in clean air at 20 °C |
| `we_t`, `ae_t` | mV | alternative: total offsets (= electronic + sensor) |
| `sens_mv_per_ppb` | mV/ppb | sensor certificate |

**Averages will not do.** The datasheet quotes sensitivity as **1450 to
2600 nA/ppm** — nearly 2× between the weakest and strongest unit. Assume the
middle and an individual sensor can be 30 % out.

**H2S-B4+ (IST)** carries these in onboard EEPROM plus a ±1 °C temperature
sensor at the head. Given the P1.4 head/board temperature split, that is the
variant worth paying for.

---

## Datasheet numbers the module uses

| | |
|---|---|
| Sensitivity | 1450 to 2600 nA/ppm at 2 ppm |
| Zero current | −250 to +200 nA in zero air at 20 °C |
| Noise | **1 ppb** equivalent (±2 standard deviations, with ISB) |
| t90 | < 60 s |
| Range | 100 ppm (performance warranty limit) |
| Overgas limit | 200 ppm |
| Sensitivity @ −20 °C / 50 °C | 77–90 % / 100–110 % of the 20 °C value |
| Zero @ −20 °C / 50 °C | +50 to +60 nA / **−120 to −160 nA** vs 20 °C |
| Sensitivity drift | < 20 %/year |
| Operating life | > 24 months to 50 % signal (24-month warranted) |
| Temperature | −30 to 50 °C |
| Pressure / humidity | 80–120 kPa / 15–90 % rh continuous |

`SENSITIVITY_TC` in the module is built from the −20 °C and 50 °C anchors with
Fig 1's curve shape between them. Replace it if you measure your own.

Zero drift is listed as `< ±100`, with the column reading "ppm equivalent
change/year in lab air". For a ppb-class part that unit looks inconsistent —
worth confirming with Alphasense rather than designing around it.

---

## Cross-sensitivity

Verified against the printed datasheet table:

| Interferent | At | Response | Matters on a landfill? |
|---|---|---|---|
| SO2 | 5 ppm | **< 20 %** | **yes** — volcanic/industrial co-emission, and the largest positive error |
| NO | 5 ppm | < 12 % | possible from flares and plant |
| Cl2 | 5 ppm | < −12 % | unlikely |
| NO2 | 5 ppm | < −10 % | traffic, plant |
| CO | 5 ppm | < 3 % | minor |
| H2 | 100 ppm | < 0.5 % | negligible |
| C2H4 | 100 ppm | < 0.1 % | negligible |
| **NH3** | 20 ppm | **< 0.1 %** | **no — negligible** |
| CO2 | 5 % | < 0.1 % | negligible |

Note the asymmetry with the ammonia sensor: **NH3 barely affects H2S (< 0.1 %),
but H2S wrecks NH3 (< −200 %)**. One direction needs correcting, the other does
not.

```python
r = h2s_b4.compute(we, ae, t_c, cal, interferents_ppb={"so2": so2_ppb})
```

These are bounds ("< 20 %"), not measurements. Over-correcting is as wrong as
not correcting.

---

## Quality flags

| Flag | Meaning | Fatal? |
|---|---|---|
| `ADC_RAILED` | converter pinned at a limit | **yes** |
| `TEMP_OUT_OF_SPEC` | outside −30…50 °C | **yes** |
| `OVERCOMPENSATED` | the AE term swamped the WE term — the correction ate the signal | **yes** |
| `COEFF_UNVERIFIED` | using a coefficient table Alphasense did not publish | no |
| `AE_SIGN_ANOMALY` | `WE_0` and `AE_0` have opposite signs (algorithms 2 and 3) | no |
| `ADC_NEAR_RAIL` | within 2 % of a limit | no |
| `TEMP_EXTRAPOLATED` | beyond the coefficient table; clamped rather than extrapolated | no |
| `NEGATIVE` | below −5 ppb, more than the 1 ppb noise explains | no |
| `ABOVE_LINEAR_RANGE` | past 100 ppm | no |

`OVERCOMPENSATED` and `AE_SIGN_ANOMALY` come straight from AAN 803-05's own
Notes column — the note documents exactly when each algorithm breaks, so those
conditions are machine-checked rather than left as prose.

Real data shows this matters: the INGV Campi Flegrei series, measured with this
same sensor, contains **0.17 % negative values** — the over-compensation
artefact the note warns about, visible in a production network.

---

## Hardware requirements

### Check the ISB gain before the order closes

Datasheet Fig 3 puts 0–200 ppb across ~300 mV, implying an ISB transimpedance
near **0.73 mV/nA**. At that gain a 2.048 V ADC span is exhausted at
**≈ 1.4 ppm H2S**.

Landfill fence lines exceed that routinely. When the fixture was first built at
ppb gain, **54 % of samples railed at full scale**.

For comparison: INGV run the same H2S-B4 sensors at **0–20 ppm** in their
volcanic monitoring network — they made the ppm-gain choice.

Dropping to ~0.056 mV/nA covers 0–20 ppm and still resolves **0.6 ppb per count**
on a bipolar 16-bit ADC. You lose nothing that matters. Confirm with Alphasense
which gain the `000-0ISB-00` boards are populated for, and what full-scale
concentration that corresponds to. **This is a purchasing question with a
deadline, not a firmware setting.**

### Bipolar ADC

The sensor zero can legitimately be negative (−250 to +200 nA). Read
differentially/bipolar or you lose the bottom of the range.

### Head temperature, not board temperature

AAN 803-05 requires the temperature **at the top of the sensor to within ±1 °C**.
The P1.4 design puts heads in open louvred air while the logger is
conduction-bonded to the rear wall — several kelvin apart, worst on the sunny
side. Board temperature injects a sun-angle-correlated error into every
correction above.

### Read WE and AE in adjacent conversions on the same ADC

Drift affecting both cancels in the subtraction. Drift between two separate
chips does not.

---

## Two sensors: pair agreement

The station carries two H2S-B4. A single sensor cannot tell you it has failed —
electrolyte dries, electrodes poison, sensitivity fades, and the number still
looks plausible. Two sensors in the same air should agree; divergence is the
earliest warning you get without a span bottle.

```python
agree, diff_ppb = h2s_b4.pair_agreement(reading_a, reading_b)
if not agree:
    raise_maintenance_ticket(diff_ppb)
```

Tolerance is the larger of an absolute floor (10 ppb, so it stays sane near
zero) and a relative band (20 %, so it stays sane at high readings).

⚠️ **Do not confuse this with a spatial gradient.** In the real INGV data, two
sensors **47 m apart** differ fourfold in median (1.60 vs 0.41 ppm) — that is
genuine atmosphere, not drift. Pair agreement only means something for sensors
in the *same* air, i.e. co-located on one mast.

---

## Cadence

t90 < 60 s, noise 1 ppb at 2σ with the ISB low-noise circuit.

Sample at 1–10 Hz, average to 1 minute, aggregate to 15 min / 1 h for
compliance. A 1-minute average genuinely resolves ~1 ppb; detection limit is
about 2–3 ppb.

---

## Fitting your own coefficients

If Alphasense will not supply the H2S table:

1. Put the sensor and its ISB in a temperature chamber on **zero air**.
2. Soak at −5, 5, 15, 25, 35, 45 °C — 30 min per step (well beyond the 60 s t90).
3. At each step log `WE_u` and `AE_u` in millivolts.
4. Compute per step: `n_T = (WE_u − WE_e) / (AE_u − AE_e)`. That ratio *is*
   `n_T` — it is what makes algorithm 1 return zero in zero air.
5. Tabulate against temperature and pass as `CoefficientSet(n_t=...)`.
6. Repeat on a span concentration if you also want to refine `SENSITIVITY_TC`.

Do it for each sensor, or at minimum each batch, and record which in `source`.

---

## Testing

```bash
python h2s_b4.py
python h2s_b4.py --fixture path/to/other.csv --cal path/to/other_cal.csv
```

```
bias              : -0.0002 ppb      <- the number that matters
rms               : 15.7465 ppb
p95 |error|       : 33.6814 ppb
A/B disagreements : 2 (0.00 %)
```

Bias near zero proves the arithmetic; random noise averages out over 43,200
rows. Larger individual errors are expected — that is sensor noise plus response
lag measured against an instantaneous truth column. With lag-matched truth the
residual drops to **0.59 ppb RMS**, which lands on the datasheet's 1 ppb @ 2σ
noise figure.

Validates arithmetic, not calibration. It cannot tell you whether your field
constants are right.

---

## References

- H2S-B4 Technical Specifications v1.1 (datasheet)
- **AAN 803-05**, *Correcting for background currents in four electrode toxic gas
  sensors*, March 2019 — copy at `../sensor raw data/AAN-803-05.pdf`
- **AAN 110**, *Environmental changes* — covers NO2/CO/H2S/SO2, and states its
  curves "should not be used for programming temperature compensation — consult
  Alphasense for specific temperature correction data"
- Real H2S-B4 field data: `../sensor raw data/campi_h2s_real.csv`
  (65,776 hourly readings, Zenodo `10.5281/zenodo.15965670`, CC-BY-4.0)
- Mead et al., *Atmos. Environ.* 70 (2013) 186–203
- Popoola et al., *Atmos. Environ.* 147 (2016) 330–343
- Cross et al., *Atmos. Meas. Tech.* 10 (2017) 3575–3588
