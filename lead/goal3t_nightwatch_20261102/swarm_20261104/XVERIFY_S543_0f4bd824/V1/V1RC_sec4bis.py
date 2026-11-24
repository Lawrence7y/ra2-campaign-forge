"""Read-only probe #13 (mine): S543 Sec 4-bis row 5 - the trip the report labels
'l1_20261020' is actually the directory l1a_20261020 (trip_id QC161-U0800-L1-E2-shortpath).
Print the three-window RPM-read frames (independent of screenshots) and the measure json frames.
Also print the measured fps_avg of those healthy windows, which is where '31.2' most plausibly comes from."""
import os, json
ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
for td in ("l1a_20261020", "t55k_20261020", "l3_1101v4d", "archive_T34", "archive_T40"):
    d = os.path.join(ROOT, td)
    fields = {}
    fp = os.path.join(d, "qc151_fields.json")
    if os.path.exists(fp):
        for e in json.load(open(fp, encoding="utf-8")):
            if e.get("group") == "MEASURE" and str(e.get("key", "")).startswith("measure_forensics_w"):
                v = e["value"]
                fields[v.get("window")] = (v.get("current_frame"), v.get("empty_window"), v.get("focus_ok"))
    js = {}
    for w in (0, 1, 2):
        p = os.path.join(d, "measure_w%d.json" % w)
        if os.path.exists(p):
            dd = json.load(open(p, encoding="utf-8"))
            fe = dd.get("frame_edges") or []
            js[w] = ((fe[0][0] if fe else None), (fe[-1][0] if fe else None),
                     (dd.get("stats") or {}).get("fps_avg"), dd.get("trip_id"))
    print(f"{td}: fields(frames/empty/focus) {fields}")
    for w, v in js.items():
        print(f"    measure_w{w}: f0={v[0]} f1={v[1]} fps_avg={None if v[2] is None else round(v[2],4)} trip={v[3]}")
