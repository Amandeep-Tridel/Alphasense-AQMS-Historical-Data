# VOC / PID Historical Data Notes (`03_VOC_PID_Historical_Data`)

## 1. About Alphasense `PIDX-A-040` Historical Data
The **Alphasense `PIDX-A-040`** (`0–40 ppm` isobutylene equivalent, `10.6 eV` krypton lamp, ATEX/IECEx intrinsically safe) was released in late 2025 (datasheet ref `PIDX-A-040/OCT25`). Because the part is new, no multi-month field archive specifically labeled `PIDX-A-040` has been deposited in public repositories yet. However, its physics and 10.6 eV lamp response are identical to Alphasense's `PID-AH2` / `PID-AH` / `PID-A1` and US EPA `SPOD` 10.6 eV fenceline PIDs.

## 2. Files in This Folder

### A. `pidx_a040_hourly_reference_series.csv`
- **Rows & Cadence:** **720 hourly rows** (30 days) extracted from our forward-modeled landfill fenceline simulation.
- **Columns:**
  - `ts`: ISO-8601 UTC timestamp
  - `voc_ppm_isobutylene_eq`: True VOC concentration (`0.02` to `~20 ppm` isobutylene equivalent)
  - `pidx_raw_volts`: Simulated raw `PIDX-A-040` voltage output (`0.040` to `2.850 V`, including `55 mV/ppm` sensitivity, `62 mV` offset, lamp baseline walk, and ideal-gas $T/P$ density factor)
  - `co_emitted_h2s_ppm`, `co_emitted_nh3_ppm`, `air_t_c`, `rh_pct`, `p_hpa`

### B. `external_voc_pid_datasets_catalog.csv`
Verified DOIs and direct URLs for 5 open-access 10.6 eV PID VOC time-series datasets discovered across Zenodo, Data.gov, Dryad, and Mountain Scholar:
1. **`10.5281/zenodo.18299926` (2026) — Alphasense `PID-AH2` Plume Dataset (`RED:VAPOR`):** High-resolution time-series responses of Alphasense `PID-AH2` photoionization detectors to VOC vapor plumes (*Nature Scientific Data*, `10.1038/s41597-026-06927-8`).
2. **`10.23719/1527833` (2022) — US EPA SPOD Fenceline VOC Dataset (Louisville, KY):** Continuous 10.6 eV PID fenceline sensor time series + TO-15 canister grab samples.
3. **`10.5061/dryad.pc866t1x6` (2024) — SENSIT SPOD 10.6 eV PID Dataset (Northern Colorado):** Continuous outdoor PID VOC + 2D ultrasonic wind time series (CC0).
4. **`10.25675/10217/235365` (2022) — Fort Collins & Greeley Neighborhood PID VOC Dataset:** Continuous VOC and meteorological time series with triggered canister samples.
5. **`10.5061/dryad.q573n5tvp` (2025) — HEI Denver-Julesburg Basin Near-Pad VOC Dataset:** Near-pad VOC and hazardous air pollutant monitoring time series (CC0).
