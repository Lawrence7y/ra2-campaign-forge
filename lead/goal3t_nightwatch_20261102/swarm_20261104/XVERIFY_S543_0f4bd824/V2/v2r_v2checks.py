"""Verify the remaining V2 claims I have not yet reproduced myself:
 (a) stall position: does last advance + max_stall == span for the big-stall windows?
 (b) which window actually has fps_avg ~2.9 (S543:154 attributes a '2.9fps slow crawl' to v4-b)
 (c) longest observable non-recovery across consecutive windows of one trip
 (d) counters/units0 + the quasi-frozen ADV windows V2 lists in its §2

Run: python -I -X utf8 v2r_v2checks.py
"""
import os, glob, json
from collections import defaultdict

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(R, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(R, "measure_w*.json")))


def cls(d):
    fe = d.get("frame_edges") or []
    if not fe:
        return "NO_EDGES", None, None
    f0, f1 = fe[0][0], fe[-1][0]
    df = f1 - f0
    return ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK"))), f0, df


D = {}
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    rel = os.path.relpath(p, R).replace("\\", "/")
    k, f0, df = cls(d)
    D[rel] = dict(k=k, f0=f0, df=df, d=d, dir=("." if p in ROOT else rel.split("/")[0]))

print("[A] stall position for windows with max_stall >= 10 s  (V2 §4.4 claims 7/8 land at the window tail)")
for rel, v in sorted(D.items()):
    st = (v["d"].get("stats") or {})
    ms, span = st.get("max_stall_s"), v["d"].get("span_s")
    if not ms or ms < 10 or not span:
        continue
    fe = v["d"]["frame_edges"]
    t0 = fe[0][1]
    last_up = None
    for i in range(1, len(fe)):
        if fe[i][0] > fe[i - 1][0]:
            last_up = fe[i][1]
    if last_up is None:
        print(f"    {rel:36s} {v['k']:4s} n_edges={len(fe)} max_stall={ms:9.3f} span={span} "
              f"no rising edge inside window (f constant)")
        continue
    last_rel = last_up - t0
    print(f"    {rel:36s} {v['k']:4s} df={v['df']:5d} max_stall={ms:9.3f} last_rise_at={last_rel:9.3f} "
          f"sum={last_rel + ms:9.3f} span={span:6.2f} match={abs(last_rel + ms - span) <= 0.05}")

print("\n[B] every ADV window sorted by fps_avg (looking for the 2.9 fps one §543 attributes to v4-b)")
adv = sorted([(v["d"]["stats"].get("fps_avg"), rel) for rel, v in D.items() if v["k"] == "ADV"])
for f, rel in adv[:14]:
    v = D[rel]
    st = v["d"]["stats"]
    print(f"    {rel:38s} fps_avg={f:8.3f} df={v['df']:6d} trip_id={v['d'].get('trip_id')} max_stall={st.get('max_stall_s')}")
print("    ... windows whose dir contains 'v4b' or 'v4-b':", [rel for rel in D if "v4b" in rel])

print("\n[C] longest observable non-recovery (FRZ window plus all later windows of the same trip)")
for rel, v in sorted(D.items()):
    if v["k"] != "FRZ":
        continue
    dr = v["dir"]
    sib = sorted([r for r, w in D.items() if w["dir"] == dr and w["k"] != "NO_EDGES"], key=lambda r: D[r]["d"].get("window"))
    last = sib[-1]
    t_end = D[last]["d"]["t_abs0"] + (D[last]["d"].get("span_s") or 0)
    frz_edge = v["d"]["frame_edges"][0][1]
    # frame_edges times are perf_counter; use window span instead: frozen start = that window's t_abs0
    span_total = t_end - v["d"]["t_abs0"]
    print(f"    {rel:36s} frozen from w{v['d']['window']} of {dr:20s} windows_after={len(sib) - 1 - sib.index(rel)} observable_no_recover_s={span_total:7.2f}")

print("\n[D] the 8 quasi-frozen ADV windows V2 §2 lists, recomputed from raw json")
for rel in ["archive_T34/measure_w0.json", "archive_T38/measure_w1.json", "archive_T39/measure_w1.json",
            "l3_20261023q/measure_w2.json", "archive_T36/measure_w0.json", "archive_T43/measure_w0.json",
            "archive_T49_u0800/measure_w0.json", "archive_T33/measure_w0.json"]:
    v = D.get(rel)
    if not v:
        print("    MISSING:", rel)
        continue
    st = v["d"]["stats"]
    span = v["d"].get("span_s")
    print(f"    {rel:38s} fps_avg={st['fps_avg']:8.3f} df={v['df']:6d} max_stall={st['max_stall_s']:9.3f} "
          f"span={span} stall/span={st['max_stall_s']/span:6.3f} logic_frames={st.get('logic_frames')}")

print("\n[E] counters: distinct tuples inside each FRZ window (V2 claims 29/29 constant)")
n_const = 0
for rel, v in sorted(D.items()):
    if v["k"] != "FRZ":
        continue
    cs = v["d"].get("counters") or []
    keys = ("units", "infantry", "aircraft", "g", "b", "techno", "g_items", "b_items")
    tup = {tuple(c.get(k) for k in keys) for c in cs}
    if len(tup) == 1:
        n_const += 1
    else:
        print("    NOT constant:", rel, tup)
print(f"    FRZ windows with a single constant counter tuple: {n_const} / {sum(1 for v in D.values() if v['k'] == 'FRZ')}")
