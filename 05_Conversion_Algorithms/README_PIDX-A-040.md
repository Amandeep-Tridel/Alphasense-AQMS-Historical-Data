# PIDX-A-040 — volatile organic compounds

`pidx_a040.py` converts raw logger output into VOC concentration in **ppm, as
isobutylene equivalent**.

Standalone file, stdlib only, Python 3.9+.

```bash
python pidx_a040.py        # self-test against the raw fixture
```

---

## How it works

**PID** = Photo Ionisation Detector. A small ultraviolet lamp shines on the
sampled air. If a photon carries enough energy, it knocks an electron off a
molecule — the molecule becomes an ion. Those ions drift to charged plates, and
the arriving charge is a current, which the sensor's own electronics turn into a
voltage.

Unlike the two electrochemical sensors, **no interface board is needed**. The
sensor outputs 0.040–2.85 V directly.

```
ppm_iso  = (V_out_mV − V_zero_mV) / mv_per_ppm
ppm_iso ×= (T_K / T_cal_K) × (P_cal / P)      # ideal-gas density
ppm      = ppm_iso × response_factor           # 1.0 = isobutylene equivalent
```

---

## The 10.6 eV rule — what this sensor can and cannot see

Every molecule has an **ionisation potential**: the energy needed to knock an
electron off, in electron-volts. This sensor's lamp delivers **10.6 eV**. The
rule is absolute, with no partial credit:

> Ionisation potential **below** 10.6 eV → detected.
> **Above** 10.6 eV → completely invisible.

| Compound | IP (eV) | Seen? |
|---|---|---|
| Xylene | 8.56 | ✅ |
| Toluene | 8.82 | ✅ |
| Benzene | 9.24 | ✅ |
| Acetone | 9.71 | ✅ |
| Vinyl chloride | 9.99 | ✅ |
| Hexane | 10.13 | ✅ |
| **Ammonia (NH3)** | **10.16** | ✅ |
| **Hydrogen sulfide (H2S)** | **10.45** | ✅ |
| Ethanol | 10.47 | ✅ (weakly) |
| **Methane (CH4)** | **12.61** | ❌ |
| Water vapour | 12.6 | ❌ |
| Carbon dioxide | 13.77 | ❌ |
| Carbon monoxide | 14.01 | ❌ |
| Oxygen / nitrogen | 12.1 / 15.6 | ❌ |

### ⚠️ Methane is invisible

At 12.61 eV, methane cannot be ionised by this lamp **at all**. Methane is the
principal gas a landfill produces. Someone will eventually assume the "VOC"
channel covers it — put the exclusion in the parameter description, not just in
a code comment.

The upside of the same rule: water, CO2, N2 and O2 are all invisible too, so
ordinary air produces no signal.

### ⚠️ The PID also reads your H2S and NH3

Both sit **below** 10.6 eV, so the VOC channel includes a contribution from
them. For H2S the published response factor on a 10.6 eV lamp is about **3.2**,
meaning:

```
ppm_iso_from_H2S  ≈  ppm_H2S / 3.2
```

So 5 ppm of H2S on the fence line adds roughly **1.6 ppm** to the VOC reading,
with no VOCs present at all. On a landfill that is not a rounding error.

The station carries dedicated H2S and NH3 sensors, so this is correctable —
subtract the estimated contribution from the VOC channel. The module does not
do this automatically, because the response factors are lamp- and unit-specific
and should be confirmed with Alphasense before being applied. Worth raising with
them alongside the interface-board questions.

---

## Quick start

```python
import pidx_a040

cal = pidx_a040.Calibration(
    serial="PIDX-A-040-001",
    mv_per_ppm=56.8,      # from YOUR span calibration on isobutylene
    v_zero_mv=68.0,       # clean-air offset
    t_cal_c=25.0,         # conditions during that span calibration
    p_cal_hpa=1013.25,
    response_factor=1.0,  # leave at 1.0 for an unknown mixture
)

baseline = pidx_a040.BaselineTracker(window_samples=1440)   # 24 h at 1/min

r = pidx_a040.convert(counts, head_t_c, p_hpa, cal, baseline=baseline)

if r.usable:
    publish(r.ppm_isobutylene)      # always keep the isobutylene value
```

Temperature **and pressure** are required positional arguments. They are not
optional refinements — see below.

---

## Calibration constants

| Field | Units | Where it comes from |
|---|---|---|
| `mv_per_ppm` | mV/ppm | **your** span calibration on isobutylene |
| `v_zero_mv` | mV | starting clean-air offset (datasheet range 40–100) |
| `t_cal_c`, `p_cal_hpa` | °C, hPa | conditions **during** that span calibration |
| `response_factor` | — | 1.0 unless you know the single compound |
| `adc_fsr_v`, `adc_bits`, `adc_bipolar` | — | logger ADC wiring; unipolar is fine here |

The nominal 55 mV/ppm carries a **±10 %** spread, so an individual unit is
somewhere between roughly 49.5 and 60.5. Span-calibrate each one.

`t_cal_c` and `p_cal_hpa` must record the actual conditions when you performed
the span, because the density correction is measured relative to them.

---

## Temperature and pressure are mandatory

This surprises people, so carefully:

**ppm is a ratio** — VOC molecules per million air molecules. But the sensor
does not measure a ratio. It counts ions in the fixed volume of its chamber, and
the number of molecules in a fixed volume depends on temperature and pressure.
Hot air is thinner.

So the **same ppm produces less signal when hot**. The datasheet confirms it
directly (Fig 2): *"the temperature response follows the ideal gas law."*

```python
density = (T_K / T_cal_K) × (P_cal / P)
```

Across −20…60 °C that is a **±13 %** swing around a 25 °C calibration — far
larger than most people expect from a PID, and larger than the ±10 % sensitivity
spread you carefully calibrated out.

Fit a BME280 at the head and get temperature, pressure and humidity together.
Passing a fixed 1013.25 for pressure is better than nothing but adds a few
percent.

**Humidity needs no correction.** The datasheet gives humidity sensitivity as
"near zero (to 95 % RH)", which is unusually good for a PID.

---

## Response factors

The sensor counts ions. It cannot tell benzene from acetone, and different
compounds ionise more or less readily, so they give different signal for the
same concentration.

Convention: calibrate on isobutylene, report everything as **isobutylene
equivalent**. To convert to a single known compound:

```
ppm_compound = ppm_isobutylene × response_factor
```

| Compound | Factor | Reading it |
|---|---|---|
| Isobutylene | 1.00 | the reference, by definition |
| Xylene | 0.45 | ionises easily → over-reports → scale down |
| Benzene / toluene | 0.55 | |
| Acetone | 1.10 | |
| Vinyl chloride | 2.00 | |
| Hexane | 4.30 | ionises poorly → under-reports → scale up |
| Ethanol | 10.0 | very poor response |

**For a landfill, leave it at 1.0.** The mixture is hundreds of compounds and
changes hourly; there is no correct single factor. Label the channel *"VOC as
isobutylene equivalent"* and say so in the metadata. Applying somebody's factor
to a mixture you have not chemically analysed is guesswork dressed as precision.

Setting a factor other than 1.0 raises `RESPONSE_FACTOR_APPLIED`, because the
number is then no longer comparable with a standard isobutylene-equivalent
reading. `r.ppm_isobutylene` always keeps the unconverted value — log it, so you
can re-derive if you later learn the composition.

---

## The drifting zero

In clean air the sensor still outputs 40–100 mV, and that offset **moves**:

- the UV lamp dims over its 10,000-hour life
- dust and film build on the lamp window, blocking light
- temperature shifts the electronics slightly

A factory zero will not still be right a year later.

### Option A — `BaselineTracker` (included)

Keeps a rolling window and takes a low percentile as the zero, on the assumption
that the air was clean at *some* point in the window.

```python
baseline = pidx_a040.BaselineTracker(
    window_samples=1440,   # 24 h at one sample per minute
    percentile=0.05,       # 5th percentile, not the minimum (noise-robust)
    initial_mv=68.0,
)
```

**Its assumption is also its failure mode.** At a site that never clears — a
landfill fence line in a long still spell — the 5th percentile is not clean air,
it is merely the quietest polluted air. The tracker then subtracts real signal
and under-reports, silently.

This is visible in the self-test, and deliberately not tuned away:

```
static factory zero    bias= -0.0021  rms= 0.0078 ppm
tracked baseline       bias= -0.9229  rms= 1.0522 ppm     <- worse
```

### Option B — scrubbed zero air (recommended for compliance)

A solenoid periodically draws air through a charcoal filter, which strips VOCs.
Whatever the sensor reads then is a **measured** zero, not an assumption. More
hardware, more maintenance, and the only version that survives an audit.

Either way, log `r.v_zero_used_mv`. Watching it climb over months is how you see
the lamp ageing before it fails.

---

## ADC resolution — check this before you build

`cal.ppb_per_count` reports the quantisation floor:

```
55 mV/ppm  =  55 µV/ppb
16-bit ADC on 4.096 V  =  125 µV per step
125 / 55  ≈  2.3 ppb per step
```

The self-test prints **2.44 ppb per count** against a datasheet minimum
detection level of **1 ppb**. Your converter is the bottleneck, not the sensor.

Fixes: oversample and average (16 samples roughly halves the noise), narrow the
full-scale range, or fit a 24-bit converter. Note the FSR must still span
2.85 V, so 4.096 V is the natural ADS1115 setting.

---

## Quality flags

| Flag | Meaning | Fatal? |
|---|---|---|
| `ADC_RAILED` | converter pinned at a limit | **yes** |
| `OUT_OF_OUTPUT_RANGE` | outside 0.040–2.85 V — sensor or wiring fault | **yes** |
| `TEMP_OUT_OF_SPEC` | outside −40…65 °C | **yes** |
| `WARMUP` | inside the 5-minute stabilisation window | **yes** |
| `BASELINE_UNTRACKED` | using a static factory zero | no |
| `BASELINE_OUT_OF_SPEC` | tracked zero left 40–100 mV — lamp or window failing | no |
| `RESPONSE_FACTOR_APPLIED` | not an isobutylene-equivalent number any more | no |
| `ABOVE_LINEAR_RANGE` | past 40 ppm; response no longer linear | no |
| `NEGATIVE` | zero estimate too high | no |
| `RH_OUT_OF_SPEC` | above 95 % rh | no |

Timing per the datasheet: **5 s** warm-up, **5 minutes** to full stabilisation.
Pass `seconds_since_power_on` and readings inside that window are flagged.

---

## Maintenance — plan for it

Unlike the electrochemical sensors, this one has **user-replaceable consumables**
and a hard service interval.

| Item | Life |
|---|---|
| 10.6 eV lamp | **10,000 hours ≈ 14 months continuous** |
| Electrode stack | user replaceable |
| Electronics / housing | 24-month warranty |
| Lamp | 12-month warranty |

| Part number | Description |
|---|---|
| `001-0042-00` | 10.6 eV lamp |
| `001-0051-00` | Detector ionisation cell assembly |
| `001-0050-00` | Cap with filter |
| `001-0036-00` | Gas hood |
| `001-0048-00` | Maintenance kit — 2× polishing disc, cap with filter, padded swab |
| `001-0049-00` | Sensor rebuild kit — 2× lamp, ionisation cell assembly, cap with filter |

On a permanently powered station the lamp reaches end of life in **about 14
months**. That is an O&M line item, not a warranty event — budget a rebuild kit
per sensor per year and a site visit to fit it. The onboard filter removes
liquids and particulates, which matters on a dusty landfill.

`BASELINE_OUT_OF_SPEC` is your early warning: when the tracked zero drifts
outside 40–100 mV, the lamp or window needs attention.

---

## Testing

```bash
python pidx_a040.py
python pidx_a040.py --fixture path/to/other.csv --cal path/to/other_cal.csv
```

Runs both zeroing strategies side by side so you can compare them on your own
data. Watch the **bias** — near zero proves the arithmetic.

Validates arithmetic, not calibration.

---

## References

- PIDX-A-040 Technical specifications v1.1, doc ref `PIDX-A-040/OCT25`
- Ionisation potentials and response factors: manufacturer PID response-factor
  tables for 10.6 eV lamps. Confirm the H2S and NH3 factors with Alphasense
  before correcting for them in production.
- The PID needs no Alphasense application note — AAN 803-05 covers
  electrochemical sensors only and does not apply here.
