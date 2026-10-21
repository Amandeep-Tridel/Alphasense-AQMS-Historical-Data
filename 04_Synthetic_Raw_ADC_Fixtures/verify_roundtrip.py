#!/usr/bin/env python3
"""
Round-trip check: read aqms_raw_fixture.csv (raw ADC counts only), run the
documented conversion chain, compare against the true_* ground-truth columns.

This validates the ARITHMETIC of the pipeline. It says nothing about whether
your calibration constants are right in the field -- only that counts -> mV ->
offset removal -> temperature compensation -> concentration is implemented
correctly. That is exactly what a unit test should cover.
"""
import csv, math, statistics as st

FULL = (1 << 15) - 1
NT = {-30: 1.45, -20: 1.42, -10: 1.36, 0: 1.30, 10: 1.24,
       20: 1.20, 30: 1.18, 40: 1.22, 50: 1.32}
SENS_TC = {-30: 0.75, -20: 0.835, -10: 0.88, 0: 0.92, 10: 0.96,
            20: 1.00, 30: 1.03, 40: 1.055, 50: 1.05}


def interp(tbl, t):
    ks = sorted(tbl)
    if t <= ks[0]:
        return tbl[ks[0]]
    if t >= ks[-1]:
        return tbl[ks[-1]]
    hi = next(k for k in ks if k >= t)
    lo = ks[ks.index(hi) - 1]
    return tbl[lo] + (t - lo) / (hi - lo) * (tbl[hi] - tbl[lo])


def counts_to_mv(c, fsr_v):
    return float(c) / FULL * fsr_v * 1000.0


cal = {}
for r in csv.DictReader(open("aqms_raw_fixture_cal.csv", encoding="utf-8")):
    cal.setdefault(r["sensor"], {})[r["param"]] = float(r["value"])

class Lag:
    """Apply the sensor's own first-order lag to the truth column, so the
    comparison isolates arithmetic error from unavoidable response delay."""

    def __init__(self, t90_s, dt_s=60.0):
        self.a = 1.0 - math.exp(-dt_s / (t90_s / 2.303))
        self.v = None

    def __call__(self, x):
        self.v = x if self.v is None else self.v + self.a * (x - self.v)
        return self.v


lag_h2s, lag_nh3, lag_voc = Lag(60.0), Lag(150.0), Lag(6.5)
err_h2s, err_voc, err_nh3 = [], [], []
lerr_h2s, lerr_voc, lerr_nh3 = [], [], []
for r in csv.DictReader(open("aqms_raw_fixture.csv", encoding="utf-8")):
    t_c = float(r["head_t_c"])
    p = float(r["p_hpa"])

    # ---- H2S-B4, AAN 803-05 Algorithm 1 -----------------------------------
    c = cal["H2S-B4-A"]
    we_u = counts_to_mv(r["h2s_A_we_counts"], 2.048)
    ae_u = counts_to_mv(r["h2s_A_ae_counts"], 2.048)
    we_c = (we_u - c["WE_e"]) - interp(NT, t_c) * (ae_u - c["AE_e"])
    sens_mv_per_ppb = c["S20"] * interp(SENS_TC, t_c) * c["isb_gain"] / 1000.0
    got = we_c / sens_mv_per_ppb
    err_h2s.append(got - float(r["true_h2s_ppb"]))
    lerr_h2s.append(got - lag_h2s(float(r["true_h2s_ppb"])))

    # ---- PIDX-A-040 -------------------------------------------------------
    c = cal["PIDX-A-040-A"]
    v_mv = float(r["voc_A_counts"]) / FULL * 4.096 * 1000.0
    ppm = (v_mv - c["v_zero"]) / c["mv_per_ppm"]
    ppm *= ((t_c + 273.15) / (c["t_cal"] + 273.15)) * (c["p_cal"] / p)
    err_voc.append(ppm - float(r["true_voc_ppm_iso"]))
    lerr_voc.append(ppm - lag_voc(float(r["true_voc_ppm_iso"])))

    # ---- NH3-B1, with H2S + SO2 cross-interference removed ----------------
    c = cal["NH3-B1-A"]
    we_u = counts_to_mv(r["nh3_A_we_counts"], 2.048)
    S = c["S20"] * (1.0 + 0.004 * (t_c - 20.0))
    apparent = (we_u - c["WE_e"]) / c["gain"] / S - c["zero_ppm"]
    nh3 = apparent - c["xs_h2s"] * float(r["true_h2s_ppb"]) / 1000.0 \
                   - c["xs_so2"] * float(r["true_so2_ppm"])
    err_nh3.append(nh3 - float(r["true_nh3_ppm"]))
    lerr_nh3.append(nh3 - lag_nh3(float(r["true_nh3_ppm"])))


def report(name, errs, unit, tol):
    bias = st.mean(errs)
    rms = math.sqrt(sum(e * e for e in errs) / len(errs))
    p95 = sorted(abs(e) for e in errs)[int(0.95 * len(errs))]
    ok = "PASS" if p95 < tol else "FAIL"
    print("  %-8s bias=%+9.4f  rms=%8.4f  p95|err|=%8.4f %-7s %s (tol %g)"
          % (name, bias, rms, p95, unit, ok, tol))


print("round-trip: raw counts -> concentration (n=%d)\n" % len(err_h2s))
print("vs INSTANTANEOUS truth  (includes unavoidable sensor response lag):")
report("H2S", err_h2s, "ppb", 40.0)
report("VOC", err_voc, "ppm", 0.15)
report("NH3", err_nh3, "ppm", 0.60)
print("\nvs LAG-MATCHED truth  (isolates the conversion arithmetic):")
report("H2S", lerr_h2s, "ppb", 8.0)
report("VOC", lerr_voc, "ppm", 0.05)
report("NH3", lerr_nh3, "ppm", 0.25)
print("\nAssert on the second block in a unit test: what remains there is only")
print("sensor noise and ADC quantisation.")
