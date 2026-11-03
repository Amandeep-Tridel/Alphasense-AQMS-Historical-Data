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
├── 05_Conversion_Algorithms/                     # Alphasense FACTORY CALIBRATION ONLY
│   ├── factory_formulas.py                       # H2S, NH3, VOC formulas (zero + factory sensitivity), rail check, AAN 803-05
│   ├── factory_formulas.js                       # The same formulas in JavaScript
│   ├── calibration_records.json                  # Factory sheets in use (NH3-B1+ 77840031)
│   ├── calibration_template_to_fill.json         # Blank VOC record to fill from the PID factory sheet
│   ├── example_usage.py                          # Converts one real station packet
│   ├── test_factory_formulas.py                  # Worked-example checks
│   └── README.md                                 # Formulas and how to use them
│
├── 06_Datasheets_and_App_Notes/
│   ├── alphasense_h2s-b4_datasheet_0224-final_en_1.pdf
│   ├── alphasense_nh3-b1_datasheet-0526-final_en_1.pdf
│   ├── alphasense_pidx-a-040_datasheet.pdf
│   └── AAN-803-05.pdf
│
└── 07_Dubai_Station_Data/                        # REAL: Dubai test station, site zero + factory sensitivity
    ├── Station_history_readings.csv              # 7,136 readings (28 Oct - 3 Nov 2026), raw mV + H2S/NH3/VOC
    ├── Station_history_10min_averages.csv        # 735 ten-minute averages
    └── README.md                                 # Formulas, columns and summary
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
| **Test `PIDX-A-040` VOC conversion and baseline drift** | `03_VOC_PID_Historical_Data/pidx_a040_hourly_reference_series.csv` | **720 hourly records** pairing raw `PIDX-A-040` voltage (`0.040–2.85 V`) with isobutylene-equivalent ppm, co-emitted $\text{H}_2\text{S}$/$\text{NH}_3$, $T$, $\text{RH}$, and $P$. |

---

## 3. Quick Start: Converting Raw Readings to Gas Concentrations

**Alphasense method only.** Each gas uses a zero and a sensitivity: the sensitivity from its Alphasense factory calibration sheet, the zero from a site zero (the station's clean-air output, AAN 803-05 "Initial calibration"). No temperature tables, no cross-sensitivity corrections, no density correction, no filtering or smoothing (all voltages in mV):

```
H2S (ppb) = ((WE - WE zero) - (AE - AE zero)) / sensitivity     # AAN 803-05 Alg. 3 at 20 degC (k'T = 1); site zero ((A1 - 458) - (A2 - 359)) / 1.727952
NH3 (ppm) = (WE - WE zero) / sensitivity                         # AAN 803-05 Alg. 4, no AE; site zero (A0 - 420) / 58.624
VOC (ppm) = (V - V zero) / sensitivity                           # AAN 302-04: no temperature correction
```

`05_Conversion_Algorithms/factory_formulas.py` (Python 3.9+, no dependencies) and `factory_formulas.js` hold these formulas. Calibration values go in `calibration_records.json`: H2S-B4 uses a site zero (458 / 359 mV) with its factory-sheet sensitivity 1.727952 mV/ppb, and NH3-B1+ 77840031 a site zero (420 mV) with its factory-sheet 58.624 mV/ppm (the factory-sheet zeros 395 / 362 and 328 mV are kept as older records); a channel stuck at the ADC rail gives no number; PIDX-A-040 uses Alphasense datasheet typical values (zero 70 mV, 55 mV/ppm), which are indicative until its factory sheet is added.

```powershell
cd 05_Conversion_Algorithms
python example_usage.py
python -m unittest test_factory_formulas -v
```

```python
import factory_formulas as ff
nh3 = ff.nh3_ppm(349.69, 328, 58.624)            # 0.37 ppm  (A0 = 349.69 mV, factory sheet 77840031)
h2s = ff.h2s_ppb(we_mv, we_zero_mv, ae_mv, ae_zero_mv, sensitivity_mv_per_ppb)   # values from the H2S factory sheet
voc = ff.voc_ppm(v_mv, v_zero_mv, sensitivity_mv_per_ppm)                         # values from the PID factory sheet
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
3. **Send no value (null) for a reading that has no factory calibration or is invalid, rather than `0.0`** — sending `0.0` corrupts rolling 10-minute averages and 30-day baselines (`B + 2S / 3S / 4S`).

---

## 5. Five Critical Hardware & Calibration Rules Surfaced by This Data

1. **`H2S-B4` ISB Gain Selection (`000-0ISB-00`):** A standard ppb-gain ISB (`~0.73 mV/nA`) saturates a `2.048 V` ADC at **`~1.4 ppm`**, which rails **48.04%** of the real `campi_flegrei_h2s_b4_real.csv` dataset. Ensure your `000-0ISB-00` boards are populated for ppm/fenceline gain (`~0.056 mV/nA` for 0–20 ppm or `~0.011 mV/nA` for 0–100 ppm).
2. **`NH3-B1` Bipolar ADC & `450 mV` Pedestal (`810-0016-01`):** Because `NH3-B1` has a `±10 ppm` clean-air zero offset and `< -200%` cross-sensitivity to $\text{H}_2\text{S}$, its output voltage drops below a standard `200–300 mV` offset whenever $\text{H}_2\text{S}$ is present (as seen in `aqms_2sensor_1min_fixture_legacy.csv` where `nh3_A_we_counts` floors at `-32767`). Always read electrochemical channels **bipolar/differentially** and use the `450 mV` pedestal (`aqms_1sensor_2min_fixture.csv`).
3. **`H2S-B4` and temperature:** AAN 803-05 (JAN23) Table 3 does have H2S-B4 factors, and they matter in Dubai: Algorithm 3's k'T is +1 at 20 °C but −1.2 at 30 °C and above (Table 2 suggests Algorithm 1 for B-type H2S). They are coded in `05_Conversion_Algorithms/factory_formulas.py` but not used yet: they need the temperature at the top of the sensor and the ISB electronic offsets. Until then the conversion is `((WE - WE zero) - (AE - AE zero)) / sensitivity` (Algorithm 3 at 20 °C) with the site zero.
4. **`NH3-B1` U-Shaped Temperature Curve:** Datasheet Figure 2 shows `NH3-B1` sensitivity follows a U-shaped curve across `-30 °C` to `+50 °C` (rising to `115–135%` at `50 °C`). `generate_1sensor_2min_fixture.py` incorporates this U-shaped curve.
5. **`PIDX-A-040` Methane Blindness:** A `10.6 eV` PID cannot ionize methane ($\text{CH}_4$, `12.61 eV`), but **does** respond to $\text{H}_2\text{S}$ (`10.45 eV`, $\text{RF} \approx 3.2$) and $\text{NH}_3$ (`10.16 eV`). With factory calibration only, no temperature or pressure correction is applied (Alphasense AAN 302-04).
