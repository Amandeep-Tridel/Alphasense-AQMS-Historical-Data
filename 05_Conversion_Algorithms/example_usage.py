"""Convert one real station packet with the factory calibration formulas.

    python example_usage.py

The Dubai test station sends:  date,time,A0,A1,A2,A3,NA   (volts)
A0 = NH3 WE, A1 = H2S WE, A2 = H2S AE, A3 = VOC (PID).
Only factory-sheet values from calibration_records.json are used. A gas without a
factory sheet gets no value.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import factory_formulas as ff  # noqa: E402
PACKET = "2026-11-02,12:47:23,0.34969,0.43008,0.36375,0.10063,NA"


def main():
    with open(os.path.join(HERE, "calibration_records.json"), encoding="utf-8") as f:
        sheets = {r["channel"]: r for r in json.load(f)["records"]}

    parts = PACKET.split(",")
    nh3_mv, h2s_we_mv, h2s_ae_mv, voc_mv = (float(v) * 1000.0 for v in parts[2:6])
    print(f"Packet {parts[0]} {parts[1]} UTC")
    print(f"  A0 {nh3_mv:.2f} mV   A1 {h2s_we_mv:.2f} mV   A2 {h2s_ae_mv:.2f} mV   A3 {voc_mv:.2f} mV\n")

    s = sheets.get("NH3")
    if s:
        ppm = ff.nh3_ppm(nh3_mv, s["we_zero_mv"], s["sensitivity"])
        print(f"NH3 = ({nh3_mv:.2f} - {s['we_zero_mv']:g}) / {s['sensitivity']:g} = {ppm:.4f} ppm  (factory sheet {s['sensor_serial']})")
    s = sheets.get("H2S")
    if s:
        ppb = ff.h2s_ppb(h2s_we_mv, s["we_zero_mv"], h2s_ae_mv, s["ae_zero_mv"], s["sensitivity"])
        print(f"H2S = {ppb:.1f} ppb  (factory sheet {s['sensor_serial']})")
    else:
        print("H2S = no value (no factory calibration sheet entered)")
    s = sheets.get("VOC")
    if s:
        print(f"VOC = {ff.voc_ppm(voc_mv, s['we_zero_mv'], s['sensitivity']):.4f} ppm  (factory sheet {s['sensor_serial']})")
    else:
        print("VOC = no value (no factory calibration sheet entered)")


if __name__ == "__main__":
    main()
