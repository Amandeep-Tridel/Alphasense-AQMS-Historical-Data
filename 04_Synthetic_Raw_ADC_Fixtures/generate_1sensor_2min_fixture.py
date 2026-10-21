#!/usr/bin/env python3
"""
Generate the 1-sensor-per-gas, 2-minute cadence (21,600 rows = 30 days)
synthetic raw ADC fixture (`aqms_1sensor_2min_fixture.csv` & `aqms_1sensor_2min_cal.csv`)
for the Tridel AQMS station (`H2S-B4`, `NH3-B1`, `PIDX-A-040`).

Drivers:
- H2S, SO2, T, RH, P: Real hourly Alphasense H2S-B4 series from Osservatorio Vesuviano
  (`../01_H2S_Historical_Data/campi_flegrei_h2s_b4_real.csv`, Zenodo 10.5281/zenodo.15965670)
- NH3, Wind Speed/Dir: Real 30-min outdoor WWTP fenceline NH3 series
  (`../02_NH3_Historical_Data/wwtp_fenceline_nh3_real.csv`, Zenodo 10.5281/zenodo.8032908)
- VOC: Co-emitted non-methane landfill VOC plume (0-40 ppm isobutylene equivalent)
"""
import csv, math, os, random
from datetime import datetime, timedelta, timezone

random.seed(20261022)

H2S_SENS_TC = {-30: 0.75, -20: 0.835, -10: 0.88, 0: 0.92, 10: 0.96,
               20: 1.00, 30: 1.03, 40: 1.055, 50: 1.05}
H2S_ZERO_TC = {-30: 60.0, -20: 55.0, -10: 45.0, 0: 32.0, 10: 16.0,
               20: 0.0, 30: -28.0, 40: -72.0, 50: -140.0}
H2S_NT_TRUE = {-30: 1.45, -20: 1.42, -10: 1.36, 0: 1.30, 10: 1.24,
               20: 1.20, 30: 1.18, 40: 1.22, 50: 1.32}
# U-shaped NH3-B1 sensitivity vs T from Datasheet Fig 2
NH3_SENS_TC = {-30: 1.24, -20: 1.16, -10: 1.07, 0: 1.01, 10: 0.99,
               20: 1.00, 30: 1.045, 40: 1.13, 50: 1.25}


def interp(tbl, t):
    ks = sorted(tbl)
    if t <= ks[0]:
        return tbl[ks[0]]
    if t >= ks[-1]:
        return tbl[ks[-1]]
    hi = next(k for k in ks if k >= t)
    lo = ks[ks.index(hi) - 1]
    if hi == lo:
        return tbl[lo]
    return tbl[lo] + ((t - lo) / (hi - lo)) * (tbl[hi] - tbl[lo])


def adc(volts, fsr, bits=16, bipolar=True):
    full = (1 << (bits - 1)) - 1
    lo = -full if bipolar else 0
    return max(lo, min(full, int(round(volts / fsr * full))))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    campi_file = os.path.join(here, "..", "01_H2S_Historical_Data", "campi_flegrei_h2s_b4_real.csv")
    wwtp_file = os.path.join(here, "..", "02_NH3_Historical_Data", "wwtp_fenceline_nh3_real.csv")

    campi_rows = []
    with open(campi_file, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if "" not in (r["air_t_c"], r["p_hpa"], r["air_rh_pct"]):
                campi_rows.append(r)
    best_st = max({r["station"] for r in campi_rows}, key=lambda s: sum(1 for r in campi_rows if r["station"] == s))
    campi_rows = sorted([r for r in campi_rows if r["station"] == best_st], key=lambda r: r["ts"])

    wwtp_nh3 = []
    with open(wwtp_file, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("NH3", "") not in ("", "NA"):
                wwtp_nh3.append((float(r["NH3"]), float(r.get("ws", 2.0) or 2.0), float(r.get("wd", 180.0) or 180.0)))

    s_h2s = {"S20": 2025.0, "we_z0": -35.0, "gain": 0.056, "we_e": 250.0, "ae_e": 248.0, "lag": 60.0 / 2.303, "state": 0.0}
    s_nh3 = {"S20": 52.0, "z_ppm": -1.5, "gain": 0.390, "we_e": 450.0, "lag": 150.0 / 2.303, "xs_h2s": -2.0, "xs_so2": -3.0, "state": 0.0}
    s_pid = {"v0": 62.0, "mvppm": 55.0, "lag": 6.5 / 2.303, "tcal": 25.0, "pcal": 1013.25, "drift": 0.0, "state": 0.0}

    HOURS, DT = 24 * 30, 120
    t0 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    fix_cols = [
        "ts", "true_h2s_ppm", "true_h2s_ppb", "true_nh3_ppm", "true_voc_ppm_iso", "true_so2_ppm",
        "head_t_c", "rh_pct", "p_hpa", "wind_speed_ms", "wind_dir_deg",
        "h2s_we_counts", "h2s_ae_counts", "nh3_we_counts", "voc_counts"
    ]

    out_fix = os.path.join(here, "aqms_1sensor_2min_fixture.csv")
    with open(out_fix, "w", newline="", encoding="utf-8") as fout:
        w = csv.DictWriter(fout, fieldnames=fix_cols)
        w.writeheader()
        for h in range(HOURS):
            a, b = campi_rows[h], campi_rows[min(h + 1, len(campi_rows) - 1)]
            nh3_a, ws_a, wd_a = wwtp_nh3[(h * 2) % len(wwtp_nh3)]
            nh3_b, ws_b, wd_b = wwtp_nh3[(h * 2 + 1) % len(wwtp_nh3)]
            for m in range(0, 3600, DT):
                f = m / 3600.0
                h2s = max(0.0, (float(a["h2s_ppm"]) + f * (float(b["h2s_ppm"]) - float(a["h2s_ppm"]))) * (1.0 + random.gauss(0, 0.04)))
                so2 = max(0.0, float(a["so2_ppm"] or 0.0))
                t_c = (float(a["air_t_c"]) + f * (float(b["air_t_c"]) - float(a["air_t_c"]))) + random.gauss(0, 0.04)
                rh = float(a["air_rh_pct"]) + f * (float(b["air_rh_pct"]) - float(a["air_rh_pct"]))
                p = float(a["p_hpa"]) + f * (float(b["p_hpa"]) - float(a["p_hpa"]))
                nh3 = max(0.0, (nh3_a + f * (nh3_b - nh3_a)) * (1.0 + random.gauss(0, 0.05)))
                ws = max(0.1, ws_a + f * (ws_b - ws_a))
                wd = (wd_a + f * ((wd_b - wd_a + 180) % 360 - 180)) % 360
                voc = min(39.5, max(0.02, 0.35 * h2s + 0.25 * nh3 + 0.15 * (1.0 + random.gauss(0, 0.20))))

                ah = 1.0 - math.exp(-DT / s_h2s["lag"])
                s_h2s["state"] += ah * (h2s - s_h2s["state"])
                S_h = s_h2s["S20"] * interp(H2S_SENS_TC, t_c)
                we_z = s_h2s["we_z0"] + interp(H2S_ZERO_TC, t_c)
                ae_z = we_z / interp(H2S_NT_TRUE, t_c)
                we_mv = s_h2s["we_e"] + (s_h2s["state"] * S_h + we_z + random.gauss(0, 0.5 * S_h / 1000.0)) * s_h2s["gain"]
                ae_mv = s_h2s["ae_e"] + (ae_z + random.gauss(0, 0.5 * S_h / 3000.0)) * s_h2s["gain"]

                an = 1.0 - math.exp(-DT / s_nh3["lag"])
                app_nh3 = nh3 + s_nh3["xs_h2s"] * h2s + s_nh3["xs_so2"] * so2
                s_nh3["state"] += an * (app_nh3 - s_nh3["state"])
                S_n = s_nh3["S20"] * interp(NH3_SENS_TC, t_c)
                nh3_mv = s_nh3["we_e"] + ((s_nh3["state"] + s_nh3["z_ppm"]) * S_n + random.gauss(0, 0.02 * s_nh3["S20"])) * s_nh3["gain"]

                ap = 1.0 - math.exp(-DT / s_pid["lag"])
                s_pid["state"] += ap * (voc - s_pid["state"])
                s_pid["drift"] += random.gauss(0, 0.003)
                dens = ((s_pid["tcal"] + 273.15) / (t_c + 273.15)) * (p / s_pid["pcal"])
                pid_v = min(2850.0, max(40.0, s_pid["v0"] + s_pid["drift"] + s_pid["state"] * s_pid["mvppm"] * dens + random.gauss(0, 0.35))) / 1000.0

                ts_str = (t0 + timedelta(hours=h, seconds=m)).isoformat().replace("+00:00", "Z")
                w.writerow({
                    "ts": ts_str,
                    "true_h2s_ppm": round(h2s, 4),
                    "true_h2s_ppb": round(h2s * 1000.0, 2),
                    "true_nh3_ppm": round(nh3, 4),
                    "true_voc_ppm_iso": round(voc, 4),
                    "true_so2_ppm": round(so2, 4),
                    "head_t_c": round(t_c, 3),
                    "rh_pct": round(rh, 2),
                    "p_hpa": round(p, 2),
                    "wind_speed_ms": round(ws, 2),
                    "wind_dir_deg": round(wd, 1),
                    "h2s_we_counts": adc(we_mv / 1000.0, 2.048, bipolar=True),
                    "h2s_ae_counts": adc(ae_mv / 1000.0, 2.048, bipolar=True),
                    "nh3_we_counts": adc(nh3_mv / 1000.0, 2.048, bipolar=True),
                    "voc_counts": adc(pid_v, 4.096, bipolar=False),
                })

    print("Wrote", out_fix)


if __name__ == "__main__":
    main()
