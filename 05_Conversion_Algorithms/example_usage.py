#!/usr/bin/env python3
# =============================================================================
#  HOW TO FEED DATA INTO h2s_b4.py, nh3_b1.py AND pidx_a040.py
# =============================================================================
#
#  Run this file to see all four input methods working:
#
#      python example_usage.py
#
#  WHAT THE MODULES NEED FROM YOU -- only three things:
#
#    1. RAW COUNTS      the whole number your ADC chip produces. Not volts,
#                       not millivolts -- the integer straight off the chip.
#                       (If your ADC library hands you volts, multiply back:
#                        counts = volts / fsr_v * 32767)
#
#    2. CONDITIONS      head temperature in Celsius, always.
#                       Plus barometric pressure in hPa, for the PID only.
#
#    3. A Calibration   the per-sensor constants from the certificate that
#                       shipped with that exact sensor. THIS IS THE ONE PEOPLE
#                       GET STUCK ON -- there is no default that works, because
#                       sensitivity varies up to 4x between units.
#
#  Everything else is optional refinement.
# =============================================================================

import csv
import os

import h2s_b4
import nh3_b1
import pidx_a040


# =============================================================================
#  STEP 0: BUILD YOUR CALIBRATION OBJECTS, ONCE, AT STARTUP
# =============================================================================
# Do this ONCE when your program starts, not per reading. These numbers come
# off the calibration certificate. Keep them in a config file (JSON/CSV/YAML)
# so swapping a sensor means editing a file, not redeploying software.

H2S_A = h2s_b4.Calibration(
    serial="H2S-B4-A",
    we_e=253.1,             # mV, from the ISB circuit board label
    ae_e=248.7,             # mV, from the ISB circuit board label
    we_0=-40.2,             # mV, from the sensor certificate (zero in clean air)
    ae_0=-33.5,             # mV, from the sensor certificate
    sens_mv_per_ppb=0.112,  # mV per ppb, from the sensor certificate
)

NH3_A = nh3_b1.Calibration(
    serial="NH3-B1-A",
    we_e=251.0,             # mV, board offset
    sens_mv_per_ppm=92.4,   # mV per ppm  (= nA/ppm from the cert x board gain)
    zero_ppm_equivalent=-3.1,   # what this unit reads in clean air, in ppm
    board_bias_mv=200.0,    # your interface board MUST supply +200 mV
)

VOC_A = pidx_a040.Calibration(
    serial="PIDX-A-040-A",
    mv_per_ppm=56.8,        # from YOUR span calibration on isobutylene
    v_zero_mv=68.0,         # clean-air offset, mV
    t_cal_c=25.0,           # temperature when you span-calibrated
    p_cal_hpa=1013.25,      # pressure when you span-calibrated
)


def show(title):
    print("\n" + "=" * 72)
    print(" " + title)
    print("=" * 72)


# =============================================================================
#  METHOD 1: ONE READING, TYPED IN BY HAND
# =============================================================================
# The simplest possible case. Use this to check your calibration constants are
# sane before you wire anything up.

def method_1_single_reading():
    show("METHOD 1: a single reading, values typed in")

    # --- H2S: needs TWO counts (working + auxiliary electrode) ---------------
    r = h2s_b4.compute(
        we_counts=12000,        # working electrode, from ADC
        ae_counts=4000,         # auxiliary electrode, from ADC
        head_t_c=25.0,          # temperature at the sensor head
        cal=H2S_A,
    )
    print("H2S   %10.2f ppb   %s" % (r.ppb, h2s_b4.describe(r.flags)))
    print("      usable=%s   as ug/m3: %.2f" % (r.usable, r.ugm3()))

    # --- NH3: needs ONE count (no auxiliary electrode on this part) ----------
    # Pass the H2S reading as an interferent, or ammonia comes out far too low.
    r2 = nh3_b1.convert(
        we_counts=9000,
        head_t_c=25.0,
        cal=NH3_A,
        interferents_ppm={"h2s": r.ppb / 1000.0},   # ppb -> ppm
    )
    print("NH3   %10.3f ppm   %s" % (r2.ppm, nh3_b1.describe(r2.flags)))
    print("      quantitative=%s  (False means: plume detector, not a number)"
          % r2.quantitative)

    # --- VOC: needs ONE count, PLUS pressure ---------------------------------
    r3 = pidx_a040.convert(
        counts=900,
        head_t_c=25.0,
        p_hpa=1009.4,           # required -- see the density correction
        cal=VOC_A,
    )
    print("VOC   %10.4f ppm   %s" % (r3.ppm, pidx_a040.describe(r3.flags)))


# =============================================================================
#  METHOD 2: FROM A CSV FILE  (batch / backfill / re-processing)
# =============================================================================
# This is how you reprocess stored raw data -- e.g. after a recalibration, when
# you want to re-derive the whole history with corrected constants.

def method_2_from_csv(path):
    show("METHOD 2: reading from a CSV file")

    if not os.path.exists(path):
        print("  (fixture not found, skipping: %s)" % path)
        return

    # NOTE -- READ THIS, IT IS THE WHOLE POINT OF CALIBRATION:
    # The H2S numbers below come out NEGATIVE, and the NEGATIVE flag fires on
    # every row. That is not a bug in the module. It is because the H2S_A
    # constants at the top of this file are made-up examples, while this CSV
    # was generated from a DIFFERENT set of constants.
    #
    # Wrong calibration -> wrong answer. There is no way around it and no
    # default that saves you. The only reason you can SEE the problem here is
    # that the flags caught it; with a bare float you would have logged
    # negative gas concentrations for a month without noticing.
    #
    # Run `python h2s_b4.py` to see the same data converted with the CORRECT
    # constants: bias drops to -0.0002 ppb.
    print("  %-20s %11s %-18s %10s %10s"
          % ("timestamp", "H2S ppb", "H2S flags", "NH3 ppm", "VOC ppm"))
    with open(path, encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            if i >= 5:                      # just show the first 5 rows
                break

            # Pull the numbers out of the row. csv gives you strings, so the
            # float() calls matter.
            t_c = float(row["head_t_c"])
            p = float(row["p_hpa"])

            h2s = h2s_b4.compute(
                float(row["h2s_A_we_counts"]),
                float(row["h2s_A_ae_counts"]),
                t_c, H2S_A)

            nh3 = nh3_b1.convert(
                float(row["nh3_A_we_counts"]), t_c, NH3_A,
                interferents_ppm={"h2s": h2s.ppb / 1000.0},
                rh_pct=float(row["rh_pct"]))

            voc = pidx_a040.convert(
                float(row["voc_A_counts"]), t_c, p, VOC_A,
                rh_pct=float(row["rh_pct"]))

            # Show the flags, not just the numbers -- that is what they are for.
            print("  %-20s %11.2f %-18s %10.3f %10.4f"
                  % (row["ts"][:19], h2s.ppb,
                     "NEGATIVE" if h2s.flags & h2s_b4.QC.NEGATIVE else "-",
                     nh3.ppm, voc.ppm))


# =============================================================================
#  METHOD 3: LIVE, FROM THE ADC CHIP ON THE LOGGER
# =============================================================================
# The shape of the real acquisition loop. The adc.read() call is whatever your
# hardware library provides -- Adafruit_ADS1x15, smbus2, spidev, etc. Everything
# after that line is identical regardless of which chip you use.

def method_3_live_loop_sketch():
    show("METHOD 3: live acquisition loop (shape only -- not run here)")
    print("""
    import time

    adc  = ADS1115(address=0x48)      # your ADC library
    bme  = BME280(address=0x76)       # temperature + pressure AT THE HEAD

    voc_baseline = pidx_a040.BaselineTracker(window_samples=1440)

    while True:
        # --- read the environment ONCE per cycle -------------------------
        t_c   = bme.temperature        # MUST be at the sensor head, not the
        p_hpa = bme.pressure           # logger board. See the module headers.

        # --- read the raw channels ---------------------------------------
        # Read WE and AE in ADJACENT conversions on the SAME chip. Drift that
        # affects both cancels out in the subtraction; drift between two
        # separate chips does not.
        we = adc.read(channel=0)
        ae = adc.read(channel=1)

        # --- convert ------------------------------------------------------
        h2s = h2s_b4.compute(we, ae, t_c, H2S_A)

        nh3 = nh3_b1.convert(
            adc.read(channel=2), t_c, NH3_A,
            interferents_ppm={"h2s": h2s.ppb / 1000.0})

        voc = pidx_a040.convert(
            adc.read(channel=3), t_c, p_hpa, VOC_A,
            baseline=voc_baseline)

        # --- act on the result --------------------------------------------
        for r in (h2s, nh3, voc):
            if r.usable:
                buffer_for_publish(r)
            else:
                log_warning(describe(r.flags))

        time.sleep(1)      # sample fast, average to 1 minute before publishing
""")


# =============================================================================
#  METHOD 4: INTO YOUR MQTT PAYLOAD
# =============================================================================
# Matching backend/PAYLOAD_SPEC.md. Two points worth making:
#
#  * Send the RAW counts alongside the converted values. Then a future
#    recalibration can re-derive the whole history. Without them, a year of
#    data can never be corrected. The spec already ignores unknown parameter
#    codes, so adding them costs nothing.
#
#  * Omit a value rather than sending zero when a reading is unusable. The spec
#    says so explicitly: a gap is honest, a zero is a lie that looks like data.

def method_4_build_payload(row):
    show("METHOD 4: building an MQTT payload")

    t_c = float(row["head_t_c"])
    p = float(row["p_hpa"])

    h2s = h2s_b4.compute(float(row["h2s_A_we_counts"]),
                         float(row["h2s_A_ae_counts"]), t_c, H2S_A)
    nh3 = nh3_b1.convert(float(row["nh3_A_we_counts"]), t_c, NH3_A,
                         interferents_ppm={"h2s": h2s.ppb / 1000.0})
    voc = pidx_a040.convert(float(row["voc_A_counts"]), t_c, p, VOC_A)

    values = {
        # --- raw channels: always send, so history can be re-derived --------
        "H2S_A_WE_CNT": float(row["h2s_A_we_counts"]),
        "H2S_A_AE_CNT": float(row["h2s_A_ae_counts"]),
        "NH3_A_WE_CNT": float(row["nh3_A_we_counts"]),
        "VOC_A_CNT": float(row["voc_A_counts"]),
        "HEAD_T": t_c,
        "PRESS": p,
    }
    flags = {}

    # --- converted channels: only when the reading is trustworthy -----------
    if h2s.usable:
        values["H2S_A"] = round(h2s.ppb, 2)
    if h2s.flags:
        flags["H2S_A"] = h2s_b4.describe(h2s.flags)

    if nh3.usable:
        values["NH3_A"] = round(nh3.ppm, 4)
    if nh3.flags:
        flags["NH3_A"] = nh3_b1.describe(nh3.flags)

    if voc.usable:
        values["VOC_A"] = round(voc.ppm, 4)
    if voc.flags:
        flags["VOC_A"] = pidx_a040.describe(voc.flags)

    payload = {
        "version": "1.0",
        "station_id": "DXB-001",
        "ts": row["ts"],
        "values": values,
        "flags": flags,
    }

    import json
    print(json.dumps(payload, indent=2)[:1200])
    return payload


# =============================================================================

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    fixture = os.path.join(os.path.dirname(here), "sensor raw data",
                           "aqms_raw_fixture.csv")

    method_1_single_reading()
    method_2_from_csv(fixture)
    method_3_live_loop_sketch()

    if os.path.exists(fixture):
        with open(fixture, encoding="utf-8") as fh:
            first = next(csv.DictReader(fh))
        method_4_build_payload(first)

    print("\n" + "=" * 72)
    print(" Constants above are EXAMPLES. Replace them with the numbers from")
    print(" your own calibration certificates before any of this means anything.")
    print("=" * 72)
