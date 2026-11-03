# 07 — Dubai test station history (factory calibration)

The complete history of the Dubai test station `aqms-monitor`, as stored in Firebase (raw voltages only), recalculated with the **Alphasense factory calibration formulas** in [`05_Conversion_Algorithms`](../05_Conversion_Algorithms).

| File | Rows | What it is |
| --- | --- | --- |
| `Station_history_factory_calibration.csv` | 6,610 | Every reading, 2026-10-28 14:16 UTC to 2026-11-03 04:32 UTC (about one a minute) |
| `Station_history_10min_averages_factory_calibration.csv` | 666 | 10-minute averages of the same readings; a window needs at least 8 of 10 valid readings |

**Formulas used (mV):**
- NH3-B1+ factory sheet **77840031**: `NH3 (ppm) = (A0 − 328) / 58.624`
- H2S-B4 and PIDX-A-040: no factory sheet entered yet, so `h2s_ppb` and `voc_ppm` are empty with the reason `calibration missing`

No filtering, smoothing, temperature tables or clamping. Negative values near zero are kept as calculated.

**Columns:** `time_utc`, `firebase_key`, `station_id`, raw voltages `a0_nh3_mv`, `a1_h2s_we_mv`, `a2_h2s_ae_mv`, `a3_voc_mv`, then `h2s_ppb`, `nh3_ppm`, `voc_ppm` (each with an `*_invalid_reason`), `nh3_calibration_record`, `battery_v`, `schema_version` and the original `raw_string` packet.

Summary: NH3 median 1.34 ppm, 5–95 % range 0.16–2.06 ppm, maximum 14.3 ppm. The NH3-B1 datasheet gives a clean-air zero uncertainty of up to ±10 ppm, so treat small NH3 values as indicative.

When the H2S and VOC factory sheets are entered, the raw voltage columns let both gases be recalculated for the whole period.
