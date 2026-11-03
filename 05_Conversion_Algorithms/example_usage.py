"""Convert one real station packet with the Alphasense formulas.

    python example_usage.py

The Dubai test station sends:  date,time,A0,A1,A2,A3,NA   (volts)
A0 = NH3 WE, A1 = H2S WE, A2 = H2S AE, A3 = VOC (PID).
Only Alphasense values from calibration_records.json are used: for each gas, the record
with the latest valid_from that is not after the packet's time (site zero for H2S and NH3,
datasheet typical for VOC). A channel stuck at the ADC rail gives no number.
"""

import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import factory_formulas as ff  # noqa: E402
PACKET = "2026-11-02,12:47:23,0.34969,0.43008,0.36375,0.10063,NA"


def main():
    parts = PACKET.split(",")
    at = f"{parts[0]}T{parts[1]}Z"
    with open(os.path.join(HERE, "calibration_records.json"), encoding="utf-8") as f:
        records = [r for r in json.load(f)["records"] if r["valid_from"] <= at]   # ISO UTC strings sort by time
    sheets = {}
    for r in sorted(records, key=lambda r: r["valid_from"]):
        sheets[r["channel"]] = r                                                   # the latest one wins

    nh3_mv, h2s_we_mv, h2s_ae_mv, voc_mv = (float(v) * 1000.0 for v in parts[2:6])
    print(f"Packet {parts[0]} {parts[1]} UTC")
    print(f"  A0 {nh3_mv:.2f} mV   A1 {h2s_we_mv:.2f} mV   A2 {h2s_ae_mv:.2f} mV   A3 {voc_mv:.2f} mV\n")

    s = sheets.get("NH3")
    if s and ff.channel_at_rail(nh3_mv):
        print("NH3 = no value (sensor fault: channel stuck at rail)")
    elif s:
        ppm = ff.no_negative(ff.nh3_ppm(nh3_mv, s["we_zero_mv"], s["sensitivity"]))
        print(f"NH3 = ({nh3_mv:.2f} - {s['we_zero_mv']:g}) / {s['sensitivity']:g} = {ppm:.4f} ppm  ({s['source']}, {s['record_id']})")
    s = sheets.get("H2S")
    if s and (ff.channel_at_rail(h2s_we_mv) or ff.channel_at_rail(h2s_ae_mv)):
        print("H2S = no value (sensor fault: channel stuck at rail)")
    elif s:
        ppb = ff.no_negative(ff.h2s_ppb(h2s_we_mv, s["we_zero_mv"], h2s_ae_mv, s["ae_zero_mv"], s["sensitivity"]))
        print(f"H2S = {ppb:.1f} ppb  ({s['source']}, {s['record_id']})")
    else:
        print("H2S = no value (no calibration values entered)")
    s = sheets.get("VOC")
    if s:
        print(f"VOC = {ff.no_negative(ff.voc_ppm(voc_mv, s['we_zero_mv'], s['sensitivity'])):.4f} ppm  ({s.get('source', 'factory')}: {s['factory_sheet_ref']})")
    else:
        print("VOC = no value (no calibration values entered)")


if __name__ == "__main__":
    main()
