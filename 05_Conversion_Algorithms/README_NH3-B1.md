# NH3-B1 — ammonia

`nh3_b1.py` converts raw logger output into ammonia concentration in **ppm**.

Standalone file, stdlib only, Python 3.9+.

```bash
python nh3_b1.py        # self-test against the raw fixture
```

---

## Read this before you build on it

This part is specified for **industrial leak detection**, not ambient air
quality. Two datasheet numbers set the ceiling on what it can do:

| | |
|---|---|
| Zero in clean air | **< ±10 ppm equivalent** |
| Cross-sensitivity to H2S | **< −200 %** at 20 ppm |

Real measured ammonia at a wastewater treatment plant — the closest public
analogue to a landfill — has a **median of 3.2 ppm** and a maximum of 9.9 ppm
(Zenodo `10.5281/zenodo.8032908`, miniDOAS reference instrument).

So at a comparable source the entire real signal sits *inside* the sensor's own
zero uncertainty, and the correction for H2S is larger than the raw reading.

The self-test says so plainly:

```
bias                     : +0.0003 ppm       <- arithmetic is exact
BELOW_ZERO_UNCERTAINTY   : 43200 (100.0 %)   <- and none of it is quantitative
INTERFERENT_DOMINATED    : 43200 (100.0 %)
```

Independent confirmation, if you need it for a design review:

- **UK Centre for Ecology & Hydrology** (which runs Britain's national ammonia
  network), Tang et al. 2018: the available ammonia sensors are "ppm range …
  suited to industrial measurements (e.g. leak detection in refrigeration
  systems), but not for air quality monitoring (low ppb levels). **These include
  the Alphasense NH3-A1 and NH3-B1**."
- **ACS Omega** 11(1):917–929, 2025: tested six *other* low-cost NH3 sensors
  outdoors and concluded "outdoor ammonia sensor measurements are not yet ready
  for routine use."

**This does not make the channel useless.** A rise still reliably indicates a
plume. It makes it an **odour-event detector**, not a concentration measurement
— and your compliance documentation needs to say which it is.

---

## How it differs from the H2S sensor

**NH3-B1 has three electrodes. H2S-B4 has four.**

The fourth electrode on the H2S part is the *auxiliary electrode*: a buried twin
that feels temperature but never touches the gas, used to cancel temperature
drift. This sensor does not have one.

So of the four algorithms in Alphasense AAN 803-05, three subtract an
auxiliary-electrode term and are simply unavailable here. Only the shape of
algorithm 4 applies:

```
WE_c   = (WE_u − WE_e) − WE_0 − k_T
ppm    = WE_c / sensitivity(T)
ppm   −= Σ (cross_sensitivity_i × concentration_i)
```

AAN 803-05 has no NH3 row anyway, so every constant here is yours to supply.

---

## Quick start

```python
import nh3_b1

cal = nh3_b1.Calibration(
    serial="NH3-B1-001",
    we_e=251.0,                 # mV, interface board label
    sens_mv_per_ppm=92.4,       # mV/ppm  (= nA/ppm from cert × board gain)
    zero_ppm_equivalent=-3.1,   # what this unit reads in clean air
    board_bias_mv=200.0,        # board MUST supply +200 mV
)

r = nh3_b1.convert(
    we_counts,                  # one channel — no auxiliary electrode
    head_t_c,
    cal,
    interferents_ppm={"h2s": h2s_ppm},   # pass this, always
)

if not r.usable:
    log(nh3_b1.describe(r.flags))
elif r.quantitative:
    publish_concentration(r.ppm)
else:
    publish_odour_event(r.ppm)   # below the ±10 ppm zero — not a concentration
```

`r.quantitative` is the property that matters on this sensor. Check it, not just
`r.usable`.

---

## Calibration constants

| Field | Units | Where it comes from |
|---|---|---|
| `we_e` | mV | interface board label — the board's own offset with no sensor |
| `sens_mv_per_ppm` | mV/ppm | sensor certificate (nA/ppm × board gain) |
| `zero_ppm_equivalent` | ppm | sensor certificate — clean-air reading at 20 °C |
| `board_bias_mv` | mV | what your board actually supplies; must be ≈ +200 |
| `adc_fsr_v`, `adc_bits`, `adc_bipolar` | — | your logger's ADC wiring |

**You cannot use average values.** The datasheet quotes sensitivity as
**20 to 80 nA/ppm** — a 4× spread between units. Assume the middle and a weak
sensor reads 2.5× too low.

The zero is expressed in **ppm-equivalent**, not millivolts, because that is how
the datasheet specifies it.

**NH3-B1+ (IST)** carries these constants in onboard EEPROM plus a ±1 °C
temperature sensor at the head, read over I²C. Given the head/board temperature
split in the P1.4 enclosure, that is the variant worth paying for.

---

## The temperature problem

The datasheet's temperature rows read, in full:

```
Sensitivity @ −20 °C .......... nd
Sensitivity @ +40 °C .......... nd
Zero @ −20 °C ................. nd
Zero @ +50 °C ................. nd
```

`nd` = **not determined**. Alphasense has not published how this part responds
to temperature. There is no graph, no table, nothing.

So `TC_UNCHARACTERISED` fires on every reading unless you supply your own
curves:

```python
r = nh3_b1.convert(counts, t_c, cal,
                   sensitivity_tc=my_fitted_sens_curve,   # {°C: fraction}
                   zero_tc_ppm=my_fitted_zero_curve)      # {°C: ppm offset}
```

### How to generate them

You need a temperature-controlled chamber, zero air, and a span bottle.

1. Soak the sensor at each of −5, 5, 15, 25, 35, 45 °C — long enough to settle,
   which for this part means well over the 150 s t90; allow 30 min per step.
2. At each step record the output in **zero air** → gives `zero_tc_ppm`.
3. At each step record the output at a **known span concentration** → gives
   `sensitivity_tc` as a fraction of the 25 °C value.
4. Fit or tabulate, pass both into `convert()`, and the flag clears.

Budget for this. It is not optional for a compliance dataset, and nobody else
has done it for you.

The placeholder in the file is a flat 0.4 %/K line. It exists only so the code
is not silently temperature-blind. It is not a characterisation.

---

## Cross-sensitivity

The sensor reacts to other gases, strongly, and mostly **negatively** — they
push the reading *down*.

| Interferent | Datasheet | Default factor | Effect |
|---|---|---|---|
| H2S | < −200 % @ 20 ppm | −2.0 | 1 ppm H2S → reads 2 ppm **low** |
| NO2 | < −200 % @ 20 ppm | −2.0 | |
| SO2 | < −300 % @ 20 ppm | −3.0 | |
| NO | < −300 % @ 50 ppm | −3.0 | |
| Cl2 | < −400 % @ 10 ppm | −4.0 | |
| CO | < 20 % @ 400 ppm | +0.20 | |
| H2 | < 15 % @ 400 ppm | +0.15 | |

**H2S is guaranteed present on a landfill.** Always pass it:

```python
interferents_ppm={"h2s": h2s_reading.ppb / 1000.0}
```

Skip that and ammonia reads roughly twice the H2S concentration too low. Since
the station carries two H2S-B4 sensors, this correction is available for free.

**But you have no channel for NO, NO2 or SO2.** Those corrections are simply
unavailable. Flag the NH3 series as uncorrectable-for-NOx in the metadata rather
than implying it is clean.

⚠️ **These are bounds, not measurements.** The datasheet says "< −200 %",
meaning *no worse than*. Your sensor might be −1.4. Over-correcting inflates
your ammonia numbers, which is just as wrong as not correcting. Measure the real
factor with a bottle if it matters, and pass your own `cross_sensitivity` dict.

---

## Quality flags

| Flag | Meaning | Fatal? |
|---|---|---|
| `BELOW_ZERO_UNCERTAINTY` | reading is inside the ±10 ppm zero spec — not a concentration | no |
| `INTERFERENT_DOMINATED` | the cross-sensitivity correction exceeded the raw signal | no |
| `TC_UNCHARACTERISED` | using placeholder temperature curves | no |
| `UNBIASED_BOARD` | board is not supplying +200 mV | **yes** |
| `ADC_RAILED` | converter pinned at a limit | **yes** |
| `TEMP_OUT_OF_SPEC` | outside −30…50 °C | **yes** |
| `TEMP_EXTRAPOLATED` | beyond the supplied table; clamped | no |
| `RH_OUT_OF_SPEC` | outside 15…90 % rh | no |
| `NEGATIVE` | below −10 ppm | no |
| `ABOVE_LINEAR_RANGE` | past the 100 ppm warranty limit | no |

---

## Hardware requirements

**The interface board must supply +200 mV bias.** The datasheet: *"Bias voltage
+200 mV (Working Electrode potential is above ground)"*. An ordinary unbiased
board will not drive this sensor. Make it explicit on the `810-0016-01` RFQ.

**The ADC must be bipolar.** Not negotiable. With a negative zero and a few ppm
of H2S present, the output sits *below* the board's 200–300 mV electronic
offset. A unipolar input floors at 0 and stays there — silently. This happened
while building the test fixture: one channel read zero for 100 % of a 30-day run
before the bipolar fix.

**Head temperature, not board temperature.** Every correction above uses it.

---

## Cadence

t90 is **< 150 s** — the slowest of the three sensors by a wide margin. Reporting
faster than that publishes a smoothed sample dressed as a measurement.

Sample at 1 Hz, average to 1 minute, aggregate to 15 min / 1 h for compliance.

---

## Testing

```bash
python nh3_b1.py
python nh3_b1.py --fixture path/to/other.csv --cal path/to/other_cal.csv
```

Watch the **bias** — it should be near zero, proving the arithmetic. Then watch
the flag percentages, which are the real story for this part. The arithmetic
passing does not mean the sensor is fit for purpose.

This validates arithmetic, not calibration. It cannot tell you whether your
field constants are right.

---

## References

- NH3-B1 Technical Specifications v1.1 (datasheet)
- AAN 803-05 — copy in `../sensor raw data/AAN-803-05.pdf`. No NH3 row; only
  the algorithm-4 shape transfers to a 3-electrode part.
- AAN 110 — covers NO2/CO/H2S/SO2 only, and says to "consult Alphasense for
  specific temperature correction data". That is the supported route to the
  missing `nd` rows.
- Tang et al., *Development of a high sensitivity Ammonia sensor*, UK CEH, 2018,
  <https://nora.nerc.ac.uk/id/eprint/530856/>
- Espina-Martin et al., *Are Ammonia Sensors Ready for Outdoor Use?*,
  ACS Omega 11(1):917–929, 2025, doi:10.1021/acsomega.5c07873
- Real NH3 concentration data: `../sensor raw data/nh3_wwtp_real.csv`
