# gas_algo — Alphasense sensor conversion

Turns raw logger output into gas concentrations for the three sensors on the
Tridel AQMS station: **H2S-B4**, **NH3-B1** and **PIDX-A-040**.

Three standalone files. No third-party dependencies, Python 3.9+. Nothing
imports anything else here, so you can copy a single file into the logger
firmware or the backend without dragging the rest along.

---

## Quick start

```bash
python h2s_b4.py          # each file self-tests against the raw fixture
python nh3_b1.py
python pidx_a040.py
python example_usage.py   # four worked ways to feed data in
```

Minimal use:

```python
import h2s_b4

cal = h2s_b4.Calibration(
    serial="H2S-B4-001",
    we_e=253.1, ae_e=248.7,        # mV, from the ISB board label
    we_0=-40.2, ae_0=-33.5,        # mV, from the sensor certificate
    sens_mv_per_ppb=0.112,         # mV/ppb, from the sensor certificate
)

r = h2s_b4.compute(we_counts, ae_counts, head_t_c, cal)

if r.usable:
    publish(r.ppb, r.ugm3())
else:
    log(h2s_b4.describe(r.flags))
```

---

## Files

| File | What it is |
|---|---|
| `h2s_b4.py` | Hydrogen sulfide. All four AAN 803-05 algorithms. Reports **ppb**. |
| `nh3_b1.py` | Ammonia. Algorithm-4 shape only (3-electrode part). Reports **ppm**. |
| `pidx_a040.py` | VOCs by photoionisation. Reports **ppm as isobutylene equivalent**. |
| `example_usage.py` | Four input methods: single reading, CSV, live ADC loop, MQTT payload. |

This file is the overview. Each sensor also has its own detailed document:

- **[README_H2S-B4.md](README_H2S-B4.md)** — the four AAN 803-05 algorithms and
  how to choose between them, the missing coefficient table and how to fit your
  own, the ISB gain ceiling, and pair agreement between the two units.
- **[README_NH3-B1.md](README_NH3-B1.md)** — the temperature characterisation you
  have to do yourself, the full cross-sensitivity table, and why this part is an
  odour-event detector rather than a concentration measurement at landfill levels.
- **[README_PIDX-A-040.md](README_PIDX-A-040.md)** — the 10.6 eV rule and what it
  can and cannot see (including that it reads your H2S), response factors, the
  drifting zero, ADC resolution, and the 14-month lamp replacement cycle.

Test data lives in `../sensor raw data/` — see that folder's README for where it
came from and what is real versus synthetic.

---

## What you must supply

Only three things. Everything else is optional refinement.

**1. Raw counts** — the integer straight off the ADC. Not volts, not millivolts.
If your ADC library returns volts, convert back: `counts = volts / fsr_v * 32767`.

**2. Conditions** — head temperature in °C for all three; barometric pressure in
hPa for the PID as well.

**3. A `Calibration`** — per-sensor constants from that unit's certificate.

Channel count differs per sensor:

| Sensor | Raw channels | Also needs |
|---|---|---|
| H2S-B4 | 2 — working **and** auxiliary electrode | temperature |
| NH3-B1 | 1 — working electrode only | temperature, **and the H2S reading** |
| PIDX-A-040 | 1 — voltage output | temperature **and pressure** |

---

## Calibration: the part that actually blocks you

**There is no default that works.** The H2S-B4 datasheet quotes sensitivity as
"1450 to 2600 nA/ppm" and the NH3-B1 as "20 to 80 nA/ppm" — a 4× spread between
units. Assume an average and you can be 60% out on an individual sensor.

Every constant comes off paperwork that shipped with the hardware:

| Constant | Where it lives |
|---|---|
| `we_e`, `ae_e` | the **ISB / interface board** label — the board's own offset with no sensor attached, deliberately set 200–300 mV so negative currents still read positive |
| `we_0`, `ae_0` | the **sensor** certificate — what that unit outputs in clean air at 20 °C |
| `sens_mv_per_ppb` / `sens_mv_per_ppm` | the sensor certificate |
| PID `mv_per_ppm`, `v_zero_mv` | your own span calibration on isobutylene |

Keep them in a config file, not in code. Swapping a sensor should be an edit,
not a redeploy — otherwise someone eventually forgets.

If you buy the **`+` / IST variants** (H2S-B4+, NH3-B1+), the sensor carries its
own calibration data in onboard EEPROM plus a ±1 °C temperature sensor at the
head, read over I²C. That removes both the "where did we file the certificate"
problem and the head-temperature problem below.

### Seeing it go wrong

`example_usage.py` method 2 deliberately runs the fixture with mismatched
constants. Every row comes out negative with the `NEGATIVE` flag set. That is
the point: wrong calibration, wrong answer, and the only reason it is visible is
that the flags caught it.

---

## Nothing returns a bare number

Every call returns a `Reading` carrying QC flags, because **most ways this chain
fails are silent**. A railed ADC still produces a plausible-looking
concentration. An out-of-spec temperature still produces a number. Someone
reading a spreadsheet next year cannot tell.

```python
r.usable          # False -> do not put this in a compliance series
r.flags           # what is wrong (combine/test with | and &)
describe(r.flags) # human-readable, e.g. "ADC_RAILED|NEGATIVE"
r.ugm3()          # mass units at REFERENCE conditions, not ambient
```

Common flags across all three:

| Flag | Meaning |
|---|---|
| `ADC_RAILED` | converter pinned at a limit — value is fiction. **Fatal.** |
| `ADC_NEAR_RAIL` | within 2% of a limit, no headroom left |
| `TEMP_OUT_OF_SPEC` | outside the sensor's rated range. **Fatal.** |
| `TEMP_EXTRAPOLATED` | beyond the coefficient table; clamped rather than guessed |
| `NEGATIVE` | below zero by more than noise explains |

Sensor-specific ones are documented in each file's `QC` class.

---

## Per-sensor warnings

### H2S-B4 — the coefficient table does not exist

AAN 803-05 Table 2 recommends **algorithm 1** for H2S B-type sensors. Table 3,
which holds the actual coefficients, covers NO, NO2, OX, CO and SO2 — **there is
no H2S row**. The note tells you which method to use and then withholds the
numbers.

`N_T_PLACEHOLDER` in the file is mine, not Alphasense's. Every reading computed
with it carries `COEFF_UNVERIFIED`, and the default `CoefficientSet` is named
*"PLACEHOLDER - fixture ground truth, not Alphasense data"*. Get the real table
from Alphasense, or fit one from a zero-air temperature soak, then set
`verified=True`.

Coefficients are passed as a `CoefficientSet`, not a loose dict, because each
algorithm needs its **own** table — `n_T` is a ratio near 1, `k''_T` is a mV
offset in the hundreds. Handing algorithm 4 the `n_T` table produces a confident
wrong answer rather than an error, so the class refuses instead.

### NH3-B1 — probably cannot do this job quantitatively

Two datasheet facts: zero is spec'd at **±10 ppm equivalent**, and
cross-sensitivity to H2S is **< −200%** (SO2 < −300%, NO2 < −200%, NO < −300%).

Real measured NH3 at a wastewater treatment plant — the closest public analogue
to a landfill — has a **median of 3.2 ppm**. The entire signal sits inside the
sensor's own zero uncertainty, and the H2S correction is larger than the raw
reading.

The self-test reflects this honestly:

```
BELOW_ZERO_UNCERTAINTY   : 43200 (100.0 %)
INTERFERENT_DOMINATED    : 43200 (100.0 %)
```

Arithmetic is exact; `r.quantitative` is False throughout. Check that property,
not just `r.usable`. When it is False the channel is an **odour-event detector**,
not a concentration measurement — and your compliance documentation should say
so.

Also: the datasheet gives `nd` (not determined) for **every** NH3-B1 temperature
row, so `TC_UNCHARACTERISED` fires unless you pass your own chamber-fitted
curves. And the part needs a **+200 mV biased** interface board; an unbiased one
will not drive it.

### PIDX-A-040 — methane is invisible

The 10.6 eV lamp cannot ionise methane (12.6 eV). On a landfill someone will
eventually assume the VOC channel covers it. Put it in the parameter
description, not just a code comment.

Other essentials:

- **Temperature and pressure are required**, not optional. The ideal-gas density
  correction is ±13% across the operating range.
- **The zero drifts** as the lamp dims and the window fouls. `BaselineTracker`
  follows it by rolling percentile, but its assumption — *the air is sometimes
  clean* — breaks at a fence line that never clears. In the self-test the
  tracker scores **worse** than a static zero for exactly that reason
  (bias −0.92 vs −0.002 ppm). A charcoal-scrubbed zero-air reference on a
  solenoid is the version that survives an audit.
- **Report as isobutylene equivalent.** Leave `response_factor` at 1.0 for an
  unspeciated mixture. `RESPONSE_FACTORS` is only valid for single known compounds.
- Check `cal.ppb_per_count` — on a 16-bit ADC at 4.096 V it is **2.44 ppb**,
  above the datasheet's 1 ppb detection limit. Your converter is the bottleneck,
  not the sensor. Oversample, narrow the range, or fit 24-bit.

---

## Hardware requirements the code assumes

**Bipolar ADC on both electrochemical channels.** Not optional. With a negative
zero and a few ppm of H2S present, the NH3-B1 output sits *below* the board's
electronic offset. A unipolar input floors at 0 and the signal is silently gone
— this happened while building the test data, killing one channel for 100% of a
30-day run.

**Head temperature, not board temperature.** AAN 803-05 requires the temperature
at the top of the sensor to within ±1 °C. The P1.4 design puts the heads in open
louvred air while the logger is conduction-bonded to the rear wall, so those two
differ by several kelvin, worst on the sunny side. Using board temperature
injects a sun-angle-correlated error into every compensation.

**Check the ISB gain before the order closes.** At the ~0.73 mV/nA implied by
datasheet Fig 3 — a ppb air-quality gain — a 2.048 V span is exhausted at
**≈1.4 ppm H2S**. Landfill fence lines exceed that routinely. INGV run the same
sensor at **0–20 ppm**. Confirm with Alphasense which gain the `000-0ISB-00`
boards are populated for.

**Read WE and AE in adjacent conversions on the same ADC.** Drift affecting both
cancels in the subtraction; drift between two separate chips does not.

---

## Integrating with the data stack

Conversion belongs on the **logger**, before MQTT — `backend/PAYLOAD_SPEC.md`
takes engineering units. But:

> **Publish the raw counts alongside the converted values.**

Add codes like `H2S_A_WE_CNT`, `H2S_A_AE_CNT`, `NH3_A_WE_CNT`, `VOC_A_CNT`,
`HEAD_T`, `PRESS`. The spec already ignores unknown parameter codes, so this
costs nothing.

The reason is recalibration. When a sensor is re-spanned in month 9, or the
`n_T` table turns out wrong, or Alphasense reissues a certificate — with raw
stored you re-derive the entire history in one backfill. Without it you have a
year of numbers you can never correct and never defend.

**Omit unusable values rather than sending zero.** The payload spec says so
explicitly: a gap is honest, a zero looks like data. See `example_usage.py`
method 4.

**Cadence.** Sample at 1–10 Hz, average to 1 minute, publish 1 minute, aggregate
to 15 min / 1 h for compliance. Do not report faster than t90 — NH3-B1 at 150 s
means a 1-minute value is already a smoothed sample.

---

## Testing

Each file self-tests against `../sensor raw data/aqms_raw_fixture.csv`, which was
built by running this physics **backwards** from known concentrations. If the
conversion is right, it must return the originals — a round-trip test.

```
h2s_b4.py      bias -0.0002 ppb    p95 |err| 33.68 ppb
nh3_b1.py      bias +0.0003 ppm    p95 |err|  0.29 ppm
pidx_a040.py   bias -0.0021 ppm    p95 |err|  0.015 ppm
```

**Watch the bias.** Random noise averages out over 43,200 rows, so bias near zero
means the arithmetic is right. Individual errors being larger is expected — that
is sensor noise plus response lag against an instantaneous truth column.

These tests validate **arithmetic, not calibration**. They cannot tell you
whether your field constants are correct.

Point them at other data with `--fixture` and `--cal`.

---

## References

- **AAN 803-05**, *Correcting for background currents in four electrode toxic gas
  sensors*, Alphasense, March 2019 — copy in `../sensor raw data/AAN-803-05.pdf`
- **AAN 110**, *Environmental changes: temperature, pressure, humidity* — covers
  NO2/CO/H2S/SO2 only, and states its curves "should not be used for programming
  temperature compensation — consult Alphasense for specific temperature
  correction data"
- Datasheets: H2S-B4 v1.1, NH3-B1 v1.1, PIDX-A-040 v1.1 (doc ref `PIDX-A-040/OCT25`)
- Tang et al., *Development of a high sensitivity Ammonia sensor*, UK CEH, 2018 —
  <https://nora.nerc.ac.uk/id/eprint/530856/>
- Espina-Martin et al., *Are Ammonia Sensors Ready for Outdoor Use?*,
  ACS Omega 11(1):917–929, 2025, doi:10.1021/acsomega.5c07873
