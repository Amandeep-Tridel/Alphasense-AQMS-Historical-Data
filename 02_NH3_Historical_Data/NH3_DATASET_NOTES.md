# NH3 Historical Data Notes (`02_NH3_Historical_Data`)

## 1. Why There Is No Public Alphasense `NH3-B1` Raw Archive
Searches across Zenodo, Figshare, Dryad, Harvard Dataverse, Mendeley Data, EU JRC, and GitHub confirm that **no public field dataset has ever been published from an Alphasense `NH3-B1` or `NH3-A1` head**. Both the UK Centre for Ecology & Hydrology (Tang et al., 2018) and ACS Omega (Espina-Martín et al., 2025, `10.1021/acsomega.5c07873`) note that `NH3-B1` (`±10 ppm` clean-air zero uncertainty, `20–80 nA/ppm`) is an industrial leak-detection sensor rather than an ambient ppb air-quality sensor.

Instead, this folder provides **three real outdoor $\text{NH}_3$ datasets** to drive your simulation, baseline testing, and interference compensation:

## 2. Files in This Folder

### A. `wwtp_fenceline_nh3_real.csv` & `wwtp_fenceline_nh3_metadata.csv`
- **Source:** Outdoor wastewater treatment plant fenceline in Switzerland (miniDOAS optical reference + ultrasonic anemometer + met station).
- **DOI & License:** `10.5281/zenodo.8032908` (<https://zenodo.org/records/8032908>), CC-BY-4.0.
- **Cadence & Rows:** **242 rows** at **30-minute** intervals (Sep–Oct 2019).
- **Key Concentrations:** Downwind `NH3` has `min = 0.20 ppm`, `median = 3.19 ppm`, `p95 = 5.85 ppm`, `max = 9.93 ppm`. Upwind `NH3_bgd` has `median = 0.60 ppm`.
- **Use Case:** Best real-world outdoor odour-source fenceline analogue for a landfill. Used to drive the $\text{NH}_3$ channel in `04_Synthetic_Raw_ADC_Fixtures/aqms_1sensor_2min_fixture.csv`.

### B. `dairy_source_nh3_clean_celsius.csv` (and raw `dairy_source_nh3_real.csv`)
- **Source:** Outdoor dairy housing emissions study, Tänikon, Switzerland.
- **DOI & License:** `10.5281/zenodo.8047581` (<https://zenodo.org/records/8047581>), CC-BY-4.0.
- **Cadence & Rows:** **661 hourly rows** (Sep–Dec 2018).
- **Key Concentrations:** `min = 3.55 ppm`, `median = 9.95 ppm`, `p95 = 32.15 ppm`, `max = 58.77 ppm`.
- **Note:** `dairy_source_nh3_clean_celsius.csv` converts the original `dd/mm/yyyy` dates to ISO-8601 UTC (`iso_ts`) and converts air temperature (`ta`) from **Kelvin to °C** (`air_t_c`). Use this dataset to test higher-concentration Warning/Action/Critical alarm rules (`10–60 ppm`).

### C. `uk_ceh_whim_bog_ec_nh3_2024/`
- **Source:** UK Centre for Ecology & Hydrology (Espina-Martín et al., 2025 companion field dataset at Whim Bog, Scotland).
- **DOI & License:** `10.5285/941b50a7-877e-48a9-921b-13003dfc1cd5` (Open Government Licence).
- **Contents:** **1-minute** outdoor time series (`2024-07-24` to `2024-08-28`) of **5 miniaturized electrochemical $\text{NH}_3$ sensors** and 1 metal-oxide sensor co-located with a **Picarro G2103 $\text{NH}_3$ reference analyzer**, temperature, relative humidity, wind speed/direction, and controlled $\text{NH}_3$ release timestamps.
