# 07 — Dubai test station history (Alphasense method)

The complete history of the Dubai test station `aqms-monitor`, as stored in Firebase (raw voltages only), recalculated with the Alphasense formulas and calibration records in [`05_Conversion_Algorithms`](../05_Conversion_Algorithms).

| File | Rows | What it is |
| --- | --- | --- |
| `Station_history_readings.csv` | 7,136 | Every reading, 2026-10-28 14:16 UTC to 2026-11-03 16:02 UTC (about one a minute) |
| `Station_history_10min_averages.csv` | 735 | 10-minute averages of the same readings; a window needs at least 8 of 10 valid readings |

**Formulas used (mV):**
- NH3-B1+ **77840031**, site zero 420 mV, factory-sheet sensitivity: `NH3 (ppm) = (A0 − 420) / 58.624`
- H2S-B4, site zero 458 / 359 mV, factory-sheet sensitivity 1.727952 mV/ppb: `H2S (ppb) = ((A1 − 458) − (A2 − 359)) / 1.727952`
- PIDX-A-040, **datasheet typical** (offset 40–100 mV, midpoint used; 55 mV/ppm): `VOC (ppm) = (A3 − 70) / 55`

The site zeros are the median output from 02:00 to 05:00 Dubai time on five nights (899 readings), as Alphasense advised (Nov 2026) and AAN 803-05 "Initial calibration" describes. With the factory-sheet zeros (NH3 328 mV; H2S 395 / 362 mV), the same clean air read 1.57 ppm NH3 and 38 ppb H2S.

No filtering, smoothing or temperature tables. **A negative result counts as 0**, and the 10-minute averages are made from those values; the raw voltage columns are unchanged. **A channel stuck at the ADC rail** (≥ 2550 mV or ≤ 5 mV) gets no number and the reason `sensor fault (channel stuck at rail)`.

**Columns:** `time_utc`, `firebase_key`, `station_id`, raw voltages `a0_nh3_mv`, `a1_h2s_we_mv`, `a2_h2s_ae_mv`, `a3_voc_mv`, then `h2s_ppb`, `nh3_ppm`, `voc_ppm` (each with an `*_invalid_reason`), `h2s_calibration_record`, `nh3_calibration_record`, `battery_v`, `schema_version` and the original `raw_string` packet.

**Summary:**
- H2S: median 0 ppb (95th percentile 10.3, max 155); 4,871 readings at 0; 198 sensor faults (3 Nov 2026, 06:47–12:41 UTC, when A1 and A2 sat at 2560 mV).
- NH3: median 0 ppm (95th percentile 0.47, max 12.8); 5,143 readings at 0; 3 sensor faults (A0 at about 2 mV).
- VOC: median 0.63 ppm (5–95 % 0.45–0.92, max 24.7).

The station reads highest at night and lowest in office hours, a temperature effect, not gas. With the night-time zero, daytime values therefore show 0. Temperature correction (AAN 803-05, needs the sensor temperature) would remove that swing. VOC uses datasheet typical values, so it is **indicative** (about ±0.55 ppm).

When a new calibration arrives (PID factory sheet, a new site zero, sensor temperature), the raw voltage columns let the whole period be recalculated.
