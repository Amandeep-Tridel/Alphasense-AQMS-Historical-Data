# Alphasense AQMS Historical Data & Conversion Package (`H2S-B4`, `NH3-B1`, `PIDX-A-040`)

This directory contains all historical concentration time series, raw ADC fixtures, conversion algorithms, calibration certificates/tables, and datasheets for your **3-gas Alphasense AQMS (`H2S-B4`, `NH3-B1`, `PIDX-A-040`)**.

---

## 1. Complete Directory Structure

```text
Alphasense_AQMS_Historical_Data/
├── README_HOW_TO_USE.md                          # Master guide: how to use all datasets & scripts
│
├── 01_H2S_Historical_Data/
│   ├── campi_flegrei_h2s_b4_real.csv             # REAL: 65,776 hourly H2S-B4 readings (6 stations, 2023–2025)
│   ├── campi_flegrei_stations_summary.csv        # Per-station coordinates, date ranges, and H2S percentiles
│   └── H2S_DATASET_NOTES.md                      # Schema, provenance (Zenodo 10.5281/zenodo.15965670), & caveats
│
├── 02_NH3_Historical_Data/
│   ├── wwtp_fenceline_nh3_real.csv               # REAL: 242 30-min outdoor WWTP fenceline NH3 + met readings
│   ├── wwtp_fenceline_nh3_metadata.csv           # Column definitions for the WWTP fenceline dataset
│   ├── dairy_source_nh3_clean_celsius.csv        # REAL: 661 hourly outdoor NH3 readings (ISO-8601 + °C converted)
│   ├── dairy_source_nh3_real.csv                 # Original raw dairy NH3 file (timestamps dd/mm/yyyy, temp in K)
│   ├── uk_ceh_whim_bog_ec_nh3_2024/              # REAL: UK CEH 1-min electrochemical NH3 sensors vs Picarro (2024)
│   └── NH3_DATASET_NOTES.md                      # Schema, provenance, bipolar ADC & H2S interference notes
│
├── 03_VOC_PID_Historical_Data/
│   ├── pidx_a040_hourly_reference_series.csv     # 720-hour (30-day) PIDX-A-040 isobutylene-eq & raw voltage series
│   ├── external_voc_pid_datasets_catalog.csv     # Verified DOIs/URLs for PID-AH2 (Zenodo) & EPA/Dryad SPOD 10.6 eV PIDs
│   └── VOC_DATASET_NOTES.md                      # Isobutylene eq basis, T/P density correction, CH4/H2S cross-response
│
├── 04_Synthetic_Raw_ADC_Fixtures/
│   ├── aqms_1sensor_2min_fixture.csv             # PRIMARY FIXTURE: 21,600 rows (30 days @ 2-min), 1 sensor/gas
│   ├── aqms_1sensor_2min_cal.csv                 # Per-sensor calibration constants for the 1-sensor/gas fixture
│   ├── generate_1sensor_2min_fixture.py          # Generator script driven by real H2S-B4 + real WWTP NH3
│   ├── aqms_2sensor_1min_fixture_legacy.csv      # LEGACY FIXTURE: 43,200 rows (30 days @ 1-min), A/B sensor pairs
│   ├── aqms_2sensor_1min_cal_legacy.csv          # Per-sensor calibration constants for the A/B pair fixture
│   ├── gen_raw_legacy.py                         # Legacy A/B pair generator script
│   └── verify_roundtrip.py                       # Round-trip arithmetic validation script
│
├── 05_Conversion_Algorithms/
│   ├── h2s_b4.py                                 # Standalone H2S-B4 conversion (AAN 803-05 Algorithms 1–4)
│   ├── nh3_b1.py                                 # Standalone NH3-B1 conversion (3-electrode + H2S cross-sensitivity)
│   ├── pidx_a040.py                              # Standalone PIDX-A-040 conversion (10.6 eV PID + T/P ideal gas law)
│   ├── example_usage.py                          # 4 worked patterns: single sample, CSV batch, live ADC, MQTT JSON
│   ├── README_H2S-B4.md                          # Detailed H2S-B4 algorithm & hardware notes
│   ├── README_NH3-B1.md                          # Detailed NH3-B1 algorithm & hardware notes
│   └── README_PIDX-A-040.md                      # Detailed PIDX-A-040 algorithm & hardware notes
│
└── 06_Datasheets_and_App_Notes/
    ├── alphasense_h2s-b4_datasheet_0224-final_en_1.pdf
    ├── alphasense_nh3-b1_datasheet-0526-final_en_1.pdf
    ├── alphasense_pidx-a-040_datasheet.pdf
    └── AAN-803-05.pdf
```

---

## 2. Which Dataset to Use for Each Task

| Your Goal | File to Use | Why |
| :--- | :--- | :--- |
| **Test your 1-sensor-per-gas AQMS logger or backend pipeline (2-min cadence)** | `04_Synthetic_Raw_ADC_Fixtures/aqms_1sensor_2min_fixture.csv` + `aqms_1sensor_2min_cal.csv` | Matches your confirmed station design (**1× `H2S-B4`, 1× `NH3-B1`, 1× `PIDX-A-040`, 1× wind, 2-min send interval**). Driven by real `H2S-B4` (`campi_flegrei_h2s_b4_real.csv`) and real outdoor fenceline `NH3` (`wwtp_fenceline_nh3_real.csv`). |
| **Analyze real multi-year `H2S-B4` field behavior, diurnal cycles, and temperature/RH drift** | `01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv` | **65,776 real hourly measurements** from 6 field stations equipped with Alphasense `H2S-B4` (0–20 ppm gain), co-located with $\text{SO}_2$, air temperature, RH, and pressure. |
| **Model realistic outdoor fenceline $\text{NH}_3$ plumes and wind roses** | `02_NH3_Historical_Data/wwtp_fenceline_nh3_real.csv` | **242 30-min measurements** of downwind $\text{NH}_3$ (`median 3.19 ppm`, `max 9.93 ppm`), upwind background $\text{NH}_3$, wind speed/direction, $T$, $\text{RH}$, and pressure at an outdoor wastewater plant. |
| **Compare low-cost electrochemical $\text{NH}_3$ sensors against a Picarro reference** | `02_NH3_Historical_Data/uk_ceh_whim_bog_ec_nh3_2024/data/` | **1-minute outdoor dataset** (Jul–Aug 2024) of 5 electrochemical $\text{NH}_3$ sensors co-located with a Picarro G2103 analyzer during controlled plume releases. |
| **Test high-concentration $\text{NH}_3$ alarm thresholds (10–60 ppm)** | `02_NH3_Historical_Data/dairy_source_nh3_clean_celsius.csv` | **661 hourly measurements** (`median 9.95 ppm`, `p95 32.15 ppm`, `max 58.77 ppm`) with timestamps normalized to ISO-8601 UTC and temperature converted to °C. |
| **Test `PIDX-A-040` VOC conversion, ideal-gas $T/P$ density correction, and baseline drift** | `03_VOC_PID_Historical_Data/pidx_a040_hourly_reference_series.csv` | **720 hourly records** pairing raw `PIDX-A-040` voltage (`0.040–2.85 V`) with isobutylene-equivalent ppm, co-emitted $\text{H}_2\text{S}$/$\text{NH}_3$, $T$, $\text{RH}$, and $P$. |

---

## 3. Quick Start: Converting Raw ADC Counts to Gas Concentrations

The three Python modules in `05_Conversion_Algorithms/` (`h2s_b4.py`, `nh3_b1.py`, `pidx_a040.py`) have **zero third-party dependencies** (standard library Python 3.9+ only) so you can copy them directly into your logger or backend.

### Step 1: Run the Built-In Self-Tests
Open PowerShell in `05_Conversion_Algorithms/` and run:

```powershell
cd "C:\Users\BARODA\Desktop\Alphasense_AQMS_Historical_Data\05_Conversion_Algorithms"
python h2s_b4.py --fixture "../04_Synthetic_Raw_ADC_Fixtures/aqms_2sensor_1min_fixture_legacy.csv" --cal "../04_Synthetic_Raw_ADC_Fixtures/aqms_2sensor_1min_cal_legacy.csv"
python nh3_b1.py --fixture "../04_Synthetic_Raw_ADC_Fixtures/aqms_2sensor_1min_fixture_legacy.csv" --cal "../04_Synthetic_Raw_ADC_Fixtures/aqms_2sensor_1min_cal_legacy.csv"
python pidx_a040.py --fixture "../04_Synthetic_Raw_ADC_Fixtures/aqms_2sensor_1min_fixture_legacy.csv" --cal "../04_Synthetic_Raw_ADC_Fixtures/aqms_2sensor_1min_cal_legacy.csv"
```

### Step 2: Convert a Single Reading from Your 1-Sensor-per-Gas Station

```python
import sys
sys.path.append(r"C:\Users\BARODA\Desktop\Alphasense_AQMS_Historical_Data\05_Conversion_Algorithms")

import h2s_b4
import nh3_b1
import pidx_a040

# 1. Load per-sensor calibration constants (matching aqms_1sensor_2min_cal.csv)
cal_h2s = h2s_b4.Calibration(
    serial="H2S-B4-01",
    we_e_mv=250.0,                 # Electronic offset on 000-0ISB-00 board label
    ae_e_mv=248.0,
    we_0_mv=-35.0 * 0.056,         # Clean-air zero offset (we_zero_20 * isb_gain)
    ae_0_mv=(-35.0 / 1.20) * 0.056,
    sens_mv_per_ppb=2025.0 * 0.056 / 1000.0,  # S20 (nA/ppm) * gain (mV/nA) / 1000
    adc_fsr_v=2.048,
    adc_bits=16,
    adc_bipolar=True,
)

cal_nh3 = nh3_b1.Calibration(
    serial="NH3-B1-01",
    we_e_mv=450.0,                 # 450 mV pedestal on 810-0016-01 board
    we_0_mv=-1.5 * 52.0 * 0.390,   # Clean-air zero offset (zero_ppm * S20 * gain)
    sens_mv_per_ppm=52.0 * 0.390,  # S20 (52 nA/ppm) * gain (0.390 mV/nA)
    xs_h2s_ppm_per_ppm=-2.0,       # Cross-sensitivity to H2S (< -200%)
    adc_fsr_v=2.048,
    adc_bits=16,
    adc_bipolar=True,
)

cal_voc = pidx_a040.Calibration(
    serial="PIDX-A-040-01",
    v_zero_mv=62.0,                # Clean-air zero offset (40–100 mV)
    mv_per_ppm=55.0,               # Isobutylene sensitivity (~55 mV/ppm)
    t_cal_c=25.0,
    p_cal_hpa=1013.25,
    adc_fsr_v=4.096,
    adc_bits=16,
    adc_bipolar=False,
)

# 2. Convert one 2-minute sample (order matters: compute H2S first so NH3 can subtract H2S interference!)
head_t_c = 32.4
p_hpa = 1004.5

res_h2s = h2s_b4.compute(we_counts=6545, ae_counts=4904, temp_c=head_t_c, cal=cal_h2s)
h2s_ppm = res_h2s.ppb / 1000.0

res_nh3 = nh3_b1.compute(we_counts=8120, temp_c=head_t_c, cal=cal_nh3, h2s_ppm=h2s_ppm)
res_voc = pidx_a040.compute(counts=1326, temp_c=head_t_c, pressure_hpa=p_hpa, cal=cal_voc)

print(f"H2S: {h2s_ppm:.3f} ppm (usable={res_h2s.usable}, flags={h2s_b4.describe(res_h2s.flags)})")
print(f"NH3: {res_nh3.ppm:.3f} ppm (usable={res_nh3.usable}, quantitative={res_nh3.quantitative})")
print(f"VOC: {res_voc.ppm:.3f} ppm isobutylene eq (usable={res_voc.usable})")
```

---

## 4. Feeding Historical CSV Data into Your AQMS Web App (`TEMS`)

To replay `04_Synthetic_Raw_ADC_Fixtures/aqms_1sensor_2min_fixture.csv` (or `01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv`) into your AQMS backend (`POST /api/v1/ingest` or MQTT `tridel/aqms/{tenant}/{station}/data`):

1. **Format each row as a batch point** on your 2-minute schedule (`expected_interval_seconds = 120`):
   ```json
   {
     "version": "1.0",
     "station_id": "AQMS-01",
     "batch_id": "550e8400-e29b-41d4-a716-446655440000",
     "points": [
       {
         "ts": "2026-06-01T00:00:00Z",
         "seq": 1,
         "values": {
           "H2S": 1.0185,
           "NH3": 3.1938,
           "TVOC": 2.0502,
           "WIND_SPEED": 2.13,
           "WIND_DIRECTION": 185.0,
           "H2S_WE_CNT": 6545,
           "H2S_AE_CNT": 4904,
           "NH3_WE_CNT": 6812,
           "VOC_CNT": 1326,
           "HEAD_T": 17.05,
           "PRESSURE": 1002.0
         }
       }
     ]
   }
   ```
2. **Always store raw ADC counts alongside converted ppm** (`H2S_WE_CNT`, `H2S_AE_CNT`, `NH3_WE_CNT`, `VOC_CNT`, `HEAD_T`, `PRESSURE`) so that historical series can be recalculated whenever a sensor is re-calibrated.
3. **Omit unusable readings (`r.usable == False`) rather than sending `0.0`** — sending `0.0` corrupts rolling 10-minute averages and 30-day baselines (`B + 2S / 3S / 4S`).

---

## 5. Five Critical Hardware & Calibration Rules Surfaced by This Data

1. **`H2S-B4` ISB Gain Selection (`000-0ISB-00`):** A standard ppb-gain ISB (`~0.73 mV/nA`) saturates a `2.048 V` ADC at **`~1.4 ppm`**, which rails **48.04%** of the real `campi_flegrei_h2s_b4_real.csv` dataset. Ensure your `000-0ISB-00` boards are populated for ppm/fenceline gain (`~0.056 mV/nA` for 0–20 ppm or `~0.011 mV/nA` for 0–100 ppm).
2. **`NH3-B1` Bipolar ADC & `450 mV` Pedestal (`810-0016-01`):** Because `NH3-B1` has a `±10 ppm` clean-air zero offset and `< -200%` cross-sensitivity to $\text{H}_2\text{S}$, its output voltage drops below a standard `200–300 mV` offset whenever $\text{H}_2\text{S}$ is present (as seen in `aqms_2sensor_1min_fixture_legacy.csv` where `nh3_A_we_counts` floors at `-32767`). Always read electrochemical channels **bipolar/differentially** and use the `450 mV` pedestal (`aqms_1sensor_2min_fixture.csv`).
3. **`H2S-B4` Missing $n_T$ Table in `AAN 803-05`:** Table 2 of `AAN-803-05.pdf` recommends Algorithm 1 for `H2S-B4`, but Table 3 omits the $\text{H}_2\text{S}$ coefficients. Request the official `H2S-B4` temperature table from Alphasense or characterize zero drift in a temperature chamber up to `50 °C`.
4. **`NH3-B1` U-Shaped Temperature Curve:** Datasheet Figure 2 shows `NH3-B1` sensitivity follows a U-shaped curve across `-30 °C` to `+50 °C` (rising to `115–135%` at `50 °C`). `generate_1sensor_2min_fixture.py` incorporates this U-shaped curve.
5. **`PIDX-A-040` Ideal-Gas Density Correction & Methane Blindness:** A `10.6 eV` PID cannot ionize methane ($\text{CH}_4$, `12.61 eV`), but **does** respond to $\text{H}_2\text{S}$ (`10.45 eV`, $\text{RF} \approx 3.2$) and $\text{NH}_3$ (`10.16 eV`). Always apply the ideal-gas temperature and pressure density correction (`±13%` across the operating range).
