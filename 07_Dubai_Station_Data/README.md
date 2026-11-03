# 07 — Dubai test station history (Alphasense calibration values)

The complete history of the Dubai test station `aqms-monitor`, as stored in Firebase (raw voltages only), recalculated with **Alphasense calibration values only** in [`05_Conversion_Algorithms`](../05_Conversion_Algorithms).

| File | Rows | What it is |
| --- | --- | --- |
| `Station_history_factory_calibration.csv` | 6,626 | Every reading, 2026-10-28 14:16 UTC to 2026-11-03 04:48 UTC (about one a minute) |
| `Station_history_10min_averages_factory_calibration.csv` | 667 | 10-minute averages of the same readings; a window needs at least 8 of 10 valid readings |

**Formulas used (mV):**
- NH3-B1+ factory sheet **77840031**: `NH3 (ppm) = (A0 − 328) / 58.624`
- H2S-B4 **factory sheet** (WE zero 395 mV, AE zero 362 mV, 1.727952 mV/ppb): `H2S (ppb) = ((A1 - 395) - (A2 - 362)) / 1.727952`
- PIDX-A-040, **datasheet typical** (PIDX datasheet: offset 40-100 mV, midpoint used; 55 mV/ppm): `VOC (ppm) = (A3 - 70) / 55`

No filtering, smoothing or temperature tables. **A negative result counts as 0**, and the 10-minute averages are made from those values; the raw voltage columns are unchanged.

**Columns:** `time_utc`, `firebase_key`, `station_id`, raw voltages `a0_nh3_mv`, `a1_h2s_we_mv`, `a2_h2s_ae_mv`, `a3_voc_mv`, then `h2s_ppb`, `nh3_ppm`, `voc_ppm` (each with an `*_invalid_reason`), `nh3_calibration_record`, `battery_v`, `schema_version` and the original `raw_string` packet.

Summary: H2S median 32.3 ppb (5–95 % 5.2–48.4, max 59.6); NH3 median 1.34 ppm (5–95 % 0.16–2.06, max 14.3); VOC median 0.64 ppm (5–95 % 0.45–0.95, max 24.7). Readings that came out below 0 are stored as 0: H2S 259, NH3 205, VOC 0.

VOC uses datasheet typical values, so it is **indicative**: the PID's own zero can differ by about ±0.55 ppm, which shows as a steady clean-air reading. The NH3-B1 datasheet gives a clean-air zero uncertainty of up to ±10 ppm, so treat small NH3 values as indicative too.

When the PID factory sheet arrives, the raw voltage columns let VOC be recalculated for the whole period.
