# Statistical Summary & Datasheet Reference (`H2S-B4`, `NH3-B1`, `PIDX-A-040`)

## 1. Percentiles Across All Historical & Synthetic Datasets in This Package

| Dataset File | Variable | Count | Min | P5 | P25 | Median | P75 | P95 | P99 | Max |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv` | `h2s_ppm` | 65,776 | -0.2659 | 0.0902 | 0.4250 | **1.2914** | 3.4424 | **9.1111** | 15.8405 | **21.2301** |
| `01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv` | `so2_ppm` | 51,401 | 0.0000 | 0.0313 | 0.1356 | **0.4146** | 0.7704 | **1.4209** | 1.9523 | **2.9947** |
| `01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv` | `air_t_c` | 57,958 | 2.7790 | 10.1717 | 14.2668 | **18.3298** | 23.4859 | **29.4740** | 32.6212 | **40.1004** |
| `01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv` | `air_rh_pct` | 58,816 | 1.6568 | 49.7314 | 65.8203 | **75.5551** | 84.5128 | **93.4239** | 99.2352 | **100.0000** |
| `01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv` | `p_hpa` | 56,265 | 975.74 | 991.56 | 998.21 | **1002.36** | 1007.12 | **1015.65** | 1020.58 | **1028.73** |
| `02_NH3_Historical_Data/wwtp_fenceline_nh3_real.csv` | `NH3` (ppm) | 242 | 0.2002 | 0.7293 | 2.2589 | **3.1938** | 4.0402 | **5.8462** | 7.6346 | **9.9344** |
| `02_NH3_Historical_Data/wwtp_fenceline_nh3_real.csv` | `NH3_bgd` (ppm) | 242 | -0.6988 | -0.4225 | 0.1225 | **0.6044** | 1.1499 | **2.2286** | 3.3906 | **3.5355** |
| `02_NH3_Historical_Data/dairy_source_nh3_clean_celsius.csv` | `nh3_ppm` | 661 | 3.5537 | 4.5189 | 6.4636 | **9.9494** | 16.0791 | **32.1544** | 44.7001 | **58.7726** |
| `02_NH3_Historical_Data/dairy_source_nh3_clean_celsius.csv` | `air_t_c` | 661 | 5.3515 | 7.7244 | 9.8416 | **13.3766** | 16.6114 | **21.0405** | 24.1344 | **26.7648** |

---

## 2. Alphasense Datasheet Specifications Summary

| Specification | `H2S-B4` (`H2S-B4/FEB24`) | `NH3-B1` (`NH3-B1/JUN26`) | `PIDX-A-040` (`PIDX-A-040/OCT25`) |
| :--- | :--- | :--- | :--- |
| **Electrodes / Principle** | 4-Electrode EC (WE, CE, RE, AE) | 3-Electrode EC (WE, CE, RE — no AE) | 10.6 eV Photoionisation Detector |
| **Measurement Range** | `0 to 100 ppm` (200 ppm overgas) | `0 to 100 ppm` (200 ppm overgas) | `0 to 40 ppm` isobutylene eq |
| **Sensitivity** | `1450 to 2600 nA/ppm` @ 2 ppm | `20 to 80 nA/ppm` @ 50 ppm | `55 mV/ppm ±10%` @ 10 ppm |
| **Response Time ($t_{90}$)** | `< 60 s` | `< 150 s` ($t_{50} = 30\text{ s}$) | `6.5 s` (5 s warm-up) |
| **Zero Current / Offset** | `-250 to +200 nA` @ 20 °C | `< ±10 ppm` eq (`+200 mV` bias) | `40 to 100 mV` (`0.040–2.85 V` span) |
| **Operating Temp / RH** | `-30 to +50 °C` / `15 to 90% RH` | `-30 to +50 °C` / `15 to 90% RH` | `-20 to +60 °C` IS / `0 to 95% RH` |
| **Annual Drift (Lab Air)** | `< ±100 ppb/yr` zero, `< 20%/yr` span | `< 2 ppm/yr` zero, `< 3%/yr` span | Governed by 10,000 h lamp window |
| **Key Interferents** | $\text{SO}_2 < 20\%$, $\text{NO} < 12\%$, $\text{NO}_2 < -10\%$ | $\text{H}_2\text{S} < -200\%$, $\text{SO}_2 < -300\%$, $\text{NO}_2 < -200\%$ | Reads gases with $\text{IP} < 10.6\text{ eV}$ ($\text{H}_2\text{S}$, $\text{NH}_3$; blind to $\text{CH}_4$) |
