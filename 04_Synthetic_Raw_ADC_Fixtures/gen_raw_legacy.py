#!/usr/bin/env python3
"""
Synthesise RAW Alphasense sensor output (H2S-B4 WE/AE mV, NH3-B1 WE mV, PIDX-A-040 V)
from real measured concentrations, for testing an AQMS ingest/conversion pipeline.

Concentration driver : REAL hourly H2S + SO2 + T + RH + P from the Osservatorio
                       Vesuviano geochemical network (Zenodo 10.5281/zenodo.15965670,
                       CC-BY-4.0), which uses actual Alphasense H2S-B4 sensors.
NH3 and VOC series   : SYNTHETIC. No public data exists for NH3-B1 or PIDX-A-040.
Raw forward model    : datasheet parameters, inverted.

Columns ending _counts are what a logger ADC would actually see.
Columns starting true_ are ground truth, for round-trip validation only.
"""
import csv, math, random
from datetime import datetime, timedelta, timezone

random.seed(20260918)

# ----------------------------------------------------------------- datasheet curves
# H2S-B4 sensitivity vs T, fraction of the 20 C value. Anchored on datasheet key
# specs (@-20 C: 77-90 %, @50 C: 100-110 %); Fig 1 shape in between.
H2S_SENS_TC = {-30: 0.75, -20: 0.835, -10: 0.88, 0: 0.92, 10: 0.96,
                20: 1.00, 30: 1.03, 40: 1.055, 50: 1.05}
# H2S-B4 WE zero current change from 20 C, nA. Anchored on datasheet key specs
# (@-20 C: +50..60 nA, @50 C: -120..-160 nA); Fig 2 shape in between.
H2S_ZERO_TC = {-30: 60.0, -20: 55.0, -10: 45.0, 0: 32.0, 10: 16.0,
                20: 0.0, 30: -28.0, 40: -72.0, 50: -140.0}
# Ratio (total WE zero)/(total AE zero) vs T, i.e. the n_T of AAN 803 Algorithm 1.
# FIXTURE GROUND TRUTH ONLY. AAN 803-05 Table 3 publishes no H2S row at all.
H2S_NT_TRUE = {-30: 1.45, -20: 1.42, -10: 1.36, 0: 1.30, 10: 1.24,
                20: 1.20, 30: 1.18, 40: 1.22, 50: 1.32}


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
    f = (t - lo) / (hi - lo)
    return tbl[lo] + f * (tbl[hi] - tbl[lo])


# ----------------------------------------------------------------- per-unit models
class H2SB4:
    """4-electrode on an Alphasense ISB. Raw = two voltages."""

    # ISB transimpedance, mV/nA.
    #   PPB_GAIN sizes 0-200 ppb across ~300 mV, matching datasheet Fig 3. It is
    #   what a ppb air-quality ISB gives you -- and it SATURATES above ~1.4 ppm.
    #   PPM_GAIN covers a 0-20 ppm fence-line range and still resolves 0.6 ppb
    #   per count on a bipolar 16-bit ADC. See README.
    PPB_GAIN = 0.73
    PPM_GAIN = 0.056

    def __init__(self, tag, gain=PPM_GAIN):
        self.tag = tag
        self.S20 = random.uniform(1450, 2600)      # nA/ppm   datasheet spread
        self.we_z0 = random.uniform(-250, 200)     # nA @20 C datasheet spread
        self.gain = gain                           # mV/nA    ISB transimpedance
        self.we_e = random.uniform(200, 300)       # mV       AAN 803-05 p.2
        self.ae_e = random.uniform(200, 300)       # mV
        self.lag = 60.0 / 2.303                    # t90 < 60 s -> tau
        self.noise_ppb = 0.5                       # 1 ppb at 2 sd -> 0.5 ppb 1 sd
        self._we = 0.0

    def step(self, ppm, t_c, dt_s):
        a = 1.0 - math.exp(-dt_s / self.lag)
        self._we += a * (ppm - self._we)
        S = self.S20 * interp(H2S_SENS_TC, t_c)
        we_zero = self.we_z0 + interp(H2S_ZERO_TC, t_c)
        ae_zero = we_zero / interp(H2S_NT_TRUE, t_c)
        we_na = self._we * S + we_zero + random.gauss(0, self.noise_ppb * S / 1000.0)
        ae_na = ae_zero + random.gauss(0, self.noise_ppb * S / 3000.0)
        return self.we_e + we_na * self.gain, self.ae_e + ae_na * self.gain


class NH3B1:
    """3-electrode, biased +200 mV. No auxiliary electrode. Raw = one voltage."""

    def __init__(self, tag):
        self.tag = tag
        self.S20 = random.uniform(20, 80)          # nA/ppm  4:1 datasheet spread
        self.z_ppm = random.uniform(-10, 10)       # zero, ppm equivalent
        self.gain = 2.2                            # mV/nA
        self.we_e = random.uniform(200, 300)       # mV
        self.lag = 150.0 / 2.303                   # t90 < 150 s
        self.xs_h2s = -2.0                         # datasheet: < -200 % at 20 ppm
        self.xs_so2 = -3.0                         # datasheet: < -300 % at 20 ppm
        self._v = 0.0

    def step(self, nh3_ppm, h2s_ppm, so2_ppm, t_c, dt_s):
        a = 1.0 - math.exp(-dt_s / self.lag)
        apparent = nh3_ppm + self.xs_h2s * h2s_ppm + self.xs_so2 * so2_ppm
        self._v += a * (apparent - self._v)
        # Datasheet gives "nd" for NH3-B1 temperature coefficients. The 0.4 %/K
        # below is a PLACEHOLDER so the fixture is not temperature-flat.
        S = self.S20 * (1.0 + 0.004 * (t_c - 20.0))
        na = (self._v + self.z_ppm) * S + random.gauss(0, 0.02 * self.S20)
        return self.we_e + na * self.gain


class PIDX:
    """PIDX-A-040. Raw = one voltage, 0.040 to 2.85 V."""

    def __init__(self, tag):
        self.tag = tag
        self.v0 = random.uniform(40, 100)              # mV offset, datasheet
        self.mvppm = 55.0 * random.uniform(0.9, 1.1)   # 55 mV/ppm +-10 %
        self.lag = 6.5 / 2.303                         # t90 6.5 s
        self.tcal = 25.0
        self.pcal = 1013.25
        self.drift = 0.0
        self._v = 0.0

    def step(self, ppm_iso, t_c, p_hpa, dt_s):
        a = 1.0 - math.exp(-dt_s / self.lag)
        self._v += a * (ppm_iso - self._v)
        self.drift += random.gauss(0, 0.004)           # lamp/window baseline walk
        dens = ((self.tcal + 273.15) / (t_c + 273.15)) * (p_hpa / self.pcal)
        mv = self.v0 + self.drift + self._v * self.mvppm * dens + random.gauss(0, 0.35)
        return min(2850.0, max(40.0, mv)) / 1000.0     # volts, clipped to spec range


def adc(volts, fsr, bits=16, bipolar=True):
    """ADS1115-style. Bipolar (differential): -FSR..+FSR maps to -2^15-1..+2^15-1.

    The electrochemical channels MUST be read bipolar. An NH3-B1 with a negative
    zero sitting in H2S will drive its output below the board's electronic offset
    and a unipolar input simply floors at 0, losing the signal entirely.
    """
    full = (1 << (bits - 1)) - 1
    lo = -full if bipolar else 0
    return max(lo, min(full, int(round(volts / fsr * full))))


# ----------------------------------------------------------------- driver series
rows = []
with open("campi_h2s_real.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if "" in (r["air_t_c"], r["p_hpa"], r["air_rh_pct"]):
            continue
        rows.append(r)
best = max({r["station"] for r in rows},
           key=lambda s: sum(1 for r in rows if r["station"] == s))
rows = [r for r in rows if r["station"] == best]
rows.sort(key=lambda r: r["ts"])
print("driver station: %s  (%d complete hourly rows)" % (best, len(rows)))

HOURS, DT = 24 * 30, 60          # 30 days at 1-minute cadence
rows = rows[:HOURS + 1]
t0 = datetime(2026, 6, 1, tzinfo=timezone.utc)

sensors = {"A": (H2SB4("A"), NH3B1("A"), PIDX("A")),
           "B": (H2SB4("B"), NH3B1("B"), PIDX("B"))}   # 2 of each, per P1.4

cols = ["ts", "true_h2s_ppb", "true_nh3_ppm", "true_voc_ppm_iso", "true_so2_ppm",
        "head_t_c", "rh_pct", "p_hpa"]
for ch in ("A", "B"):
    cols += [f"h2s_{ch}_we_counts", f"h2s_{ch}_ae_counts",
             f"nh3_{ch}_we_counts", f"voc_{ch}_counts"]

out = open("aqms_raw_fixture.csv", "w", newline="", encoding="utf-8")
w = csv.DictWriter(out, fieldnames=cols)
w.writeheader()

n = 0
for h in range(HOURS):
    a, b = rows[h], rows[min(h + 1, len(rows) - 1)]
    for m in range(0, 3600, DT):
        f = m / 3600.0

        def lerp(k, a=a, b=b, f=f):
            return float(a[k]) + f * (float(b[k]) - float(a[k]))

        h2s = max(0.0, lerp("h2s_ppm") * (1.0 + random.gauss(0, 0.06)))
        so2 = float(a["so2_ppm"]) if a["so2_ppm"] else 0.0
        so2 = max(0.0, so2)
        t_c = lerp("air_t_c") + random.gauss(0, 0.05)
        rh = lerp("air_rh_pct")
        p = lerp("p_hpa")
        # SYNTHETIC co-emitted NH3 and VOC, correlated with the real H2S plume
        nh3 = max(0.0, h2s * 0.45 * (1 + random.gauss(0, 0.25)) + 0.15)
        voc = max(0.0, h2s * 1.8 * (1 + random.gauss(0, 0.30)) + 0.30)
        rec = {"ts": (t0 + timedelta(hours=h, seconds=m)).isoformat().replace("+00:00", "Z"),
               "true_h2s_ppb": round(h2s * 1000, 2),
               "true_nh3_ppm": round(nh3, 4),
               "true_voc_ppm_iso": round(voc, 4),
               "true_so2_ppm": round(so2, 4),
               "head_t_c": round(t_c, 3),
               "rh_pct": round(rh, 2),
               "p_hpa": round(p, 2)}
        for ch, (s_h2s, s_nh3, s_pid) in sensors.items():
            we, ae = s_h2s.step(h2s, t_c, DT)
            rec[f"h2s_{ch}_we_counts"] = adc(we / 1000.0, 2.048)
            rec[f"h2s_{ch}_ae_counts"] = adc(ae / 1000.0, 2.048)
            rec[f"nh3_{ch}_we_counts"] = adc(s_nh3.step(nh3, h2s, so2, t_c, DT) / 1000.0, 2.048)
            # PID output is 0.040-2.85 V, always positive -> unipolar is correct here
            rec[f"voc_{ch}_counts"] = adc(s_pid.step(voc, t_c, p, DT), 4.096, bipolar=False)
        w.writerow(rec)
        n += 1
out.close()

with open("aqms_raw_fixture_cal.csv", "w", newline="", encoding="utf-8") as f:
    w2 = csv.writer(f)
    w2.writerow(["sensor", "param", "value", "units", "source"])
    for ch, (sh, sn, sp) in sensors.items():
        for k, v, u in (("S20", sh.S20, "nA/ppm"), ("we_zero_20", sh.we_z0, "nA"),
                        ("isb_gain", sh.gain, "mV/nA"), ("WE_e", sh.we_e, "mV"),
                        ("AE_e", sh.ae_e, "mV")):
            w2.writerow([f"H2S-B4-{ch}", k, round(v, 4), u, "per-unit, would be on cal cert"])
        for k, v, u in (("S20", sn.S20, "nA/ppm"), ("zero_ppm", sn.z_ppm, "ppm"),
                        ("gain", sn.gain, "mV/nA"), ("WE_e", sn.we_e, "mV"),
                        ("xs_h2s", sn.xs_h2s, "ppm/ppm"), ("xs_so2", sn.xs_so2, "ppm/ppm")):
            w2.writerow([f"NH3-B1-{ch}", k, round(v, 4), u, "per-unit"])
        for k, v, u in (("v_zero", sp.v0, "mV"), ("mv_per_ppm", sp.mvppm, "mV/ppm"),
                        ("t_cal", sp.tcal, "C"), ("p_cal", sp.pcal, "hPa")):
            w2.writerow([f"PIDX-A-040-{ch}", k, round(v, 4), u, "per-unit"])
    for t, v in sorted(H2S_NT_TRUE.items()):
        w2.writerow(["H2S-B4-*", "n_T@%dC" % t, v, "-", "FIXTURE TRUTH - not Alphasense data"])

print("wrote aqms_raw_fixture.csv  rows=%d  cols=%d" % (n, len(cols)))
