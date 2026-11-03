# 07 — Dubai test station history (Alphasense method)

The complete history of the Dubai test station `aqms-monitor`, as stored in Firebase (raw voltages only), recalculated with the Alphasense formulas and calibration records in [`05_Conversion_Algorithms`](../05_Conversion_Algorithms).

| File | Rows | What it is |
| --- | --- | --- |
| `Station_history_readings.csv` | 7,350 | Every reading, 2026-10-28 14:16 UTC to 2026-11-03 19:37 UTC (about one a minute) |
| `Station_history_10min_averages.csv` | 756 | 10-minute averages of the same readings; a window needs at least 8 of 10 valid readings |
| `Open_Meteo_hourly_temperature_Tridel_office.csv` | 168 | The hourly air temperature used for each reading |

**Formulas used (mV):**
- NH3-B1+ **77840031**, site zero 420 mV: `NH3 (ppm) = (A0 − 420) / (58.624 × S_NH3(T) / 100)`
- H2S-B4, site zero 458 / 359 mV: `H2S (ppb) = ((A1 − 458) − (A2 − 359)) / (1.727952 × S_H2S(T) / 100)`
- PIDX-A-040, **datasheet typical**: `VOC (ppm) = (A3 − 70) / (55 × S_PID(T) / 100)`

**Temperature (T):** the station sends no sensor temperature, so T is the **Open-Meteo hourly air temperature at the Tridel Dubai office** (QD01, DAFZA Industrial Park, Al Qusais Industrial Area 5; 25.28934 N, 55.40345 E; Open-Meteo grid point 25.318 N, 55.394 E, 3.4 km away) for the reading's UTC hour: 22.9 to 36.5 °C, median 28.7 °C. It changes only the **sensitivity**, S(T) as % of the 20 °C value: H2S-B4 and NH3-B1 from their datasheet charts (approximate), PIDX-A-040 from the ideal gas law its datasheet states, 100 × 293.15 / (273.15 + T). The H2S zero correction (AAN 803-05 Table 3) is not applied: it needs the ISB electronic offsets. Outdoor air temperature can differ by several degrees from the sensor's own, so this is a stand-in until the station measures it.

The site zeros are the median output from 02:00 to 05:00 Dubai time on five nights (899 readings), as Alphasense advised (Nov 2026) and AAN 803-05 "Initial calibration" describes. With the factory-sheet zeros (NH3 328 mV; H2S 395 / 362 mV), the same clean air read 1.57 ppm NH3 and 38 ppb H2S.

No filtering or smoothing. **A negative result counts as 0**, and the 10-minute averages are made from those values; the raw voltage columns are unchanged. **A channel stuck at the ADC rail** (≥ 2550 mV or ≤ 5 mV) gets no number and the reason `sensor fault (channel stuck at rail)`.

**Columns:** `time_utc`, `firebase_key`, `station_id`, raw voltages `a0_nh3_mv`, `a1_h2s_we_mv`, `a2_h2s_ae_mv`, `a3_voc_mv`, then `h2s_ppb`, `nh3_ppm`, `voc_ppm` (each with an `*_invalid_reason`), `h2s_calibration_record`, `nh3_calibration_record`, `open_meteo_temp_c`, `h2s_sensitivity_pct`, `nh3_sensitivity_pct`, `voc_sensitivity_pct` (blank when the reading is invalid), `battery_v`, `schema_version` and the original `raw_string` packet.

**Summary:**
- H2S: median 0 ppb (95th percentile 10.0, max 150); 4,988 readings at 0; 198 sensor faults (3 Nov 2026, 06:47–12:41 UTC, when A1 and A2 sat at 2560 mV).
- NH3: median 0 ppm (95th percentile 0.50, max 12.1); 5,159 readings at 0; 3 sensor faults (A0 at about 2 mV).
- VOC: median 0.64 ppm (5–95 % 0.45–0.94, max 25.8).
- Against the same history without temperature: H2S and NH3 about 2 % lower (sensitivity 101–105 % and 101–108 %), VOC about 3 % higher (PID sensitivity 95–99 %).

The station reads highest at night and lowest in office hours, a temperature effect on the zero, not gas. With the night-time zero, daytime values therefore show 0. Only the H2S zero correction with the sensor's own temperature would remove that swing. VOC uses datasheet typical values, so it is **indicative** (about ±0.55 ppm).

When a new calibration arrives (PID factory sheet, a new site zero, sensor temperature), the raw voltage columns let the whole period be recalculated.
