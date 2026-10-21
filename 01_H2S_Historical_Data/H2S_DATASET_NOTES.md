# H2S Historical Data Notes (`01_H2S_Historical_Data`)

## 1. `campi_flegrei_h2s_b4_real.csv`
- **Sensor Model:** Real **Alphasense `H2S-B4`** (configured for 0–20 ppm range).
- **Source / Provenance:** Osservatorio Vesuviano (INGV) multiparametric geochemical network, Solfatara–Pisciarelli (Campi Flegrei, Italy).
- **DOI & License:** `10.5281/zenodo.15965670` (<https://zenodo.org/records/15965670>), CC-BY-4.0.
- **Rows & Cadence:** **65,776 hourly rows** across 6 stations (`MG-1`, `MG-2`, `MG-3`, `V07`, `V11`, `V202`) from `2023-04-19` to `2025-07-14`.

### Columns
| Column | Units | Description |
| :--- | :--- | :--- |
| `station` | string | Station identifier (`MG-1`, `MG-2`, `MG-3`, `V07`, `V11`, `V202`) |
| `ts` | UTC timestamp | Hourly measurement timestamp (`YYYY-MM-DD HH:MM:SS`) |
| `h2s_ppm` | ppm | Converted $\text{H}_2\text{S}$ concentration from Alphasense `H2S-B4` |
| `so2_ppm` | ppm | Co-located $\text{SO}_2$ concentration |
| `air_t_c` | °C | Ambient air temperature (`2.78 °C` to `40.10 °C`) |
| `air_rh_pct` | % RH | Relative humidity (`1.66 %` to `100.0 %`) |
| `p_hpa` | hPa | Barometric pressure (`975.7 hPa` to `1028.7 hPa`) |

### Key Statistical Findings
- **Overall $\text{H}_2\text{S}$ Distribution:** `min = -0.2659 ppm`, `p5 = 0.0902 ppm`, `p25 = 0.4250 ppm`, `median = 1.2914 ppm`, `p75 = 3.4424 ppm`, `p95 = 9.1111 ppm`, `p99 = 15.8405 ppm`, `max = 21.2301 ppm`.
- **48.04%** of all hourly readings exceed `1.4 ppm` (the saturation ceiling of a ppb-gain ISB board on a 2.048 V ADC).
- **0.173%** of values are slightly negative (`down to -0.27 ppm`), representing real field AAN 803 temperature over-compensation artefacts—useful for testing your QC negative-clamping/flagging logic.

## 2. `campi_flegrei_stations_summary.csv`
Contains the WGS84 coordinates, distance from the fumarole source, total rows, date span, and $\text{H}_2\text{S}$ / temperature / humidity percentiles for each of the 6 stations.
