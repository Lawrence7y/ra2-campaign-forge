"""Final data checks:
 (a) v4-b / v4-e wait-trace: does the frame counter advance, and at what rate? (tests V2 row K)
 (b) the 'process gone' fingerprint ws_kb=20/pf_kb=64 in the dropped files and in e4/w2 (V2 §8)
 (c) cross-window counter continuity at the freeze boundary for my 3 samples (V2 §4.2)
 (d) the 1s-quantised band test of displayed time vs 31.2 and vs 30.0, using MY OWN digit reads

Run: python -I -X utf8 v2r_final.py
"""
import os, glob, json, statistics

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"


def J(*p):
    return json.load(open(os.path.join(R, *p), encoding="utf-8"))


print("[K] wait-trace frame progression (the channel §535 used for 'v4-b 慢爬')")
for dr in ["l3_1101v4b", "l3_1101v4e", "l3_1101v3a"]:
    p = os.path.join(R, dr, "h8_wait_trace.json")
    if not os.path.exists(p):
        print("   ", dr, "no h8_wait_trace.json")
        continue
    d = json.load(open(p, encoding="utf-8"))
    sm = d["samples"]
    ts = [x[0] for x in sm]
    fs = [x[1] for x in sm]
    rises = [i for i in range(1, len(fs)) if fs[i] > fs[i - 1]]
    intervals = [ts[i] - ts[i - 1] for i in rises]
    print(f"    {dr}: n_target={d.get('n')} verdict={d.get('verdict')} wait_s={d.get('wait_s')} "
          f"samples={len(sm)} f_min={min(fs)} f_max={max(fs)} rising_edges={len(rises)}")
    if intervals:
        print(f"        median rise interval={statistics.median(intervals):.4f} s -> {1/statistics.median(intervals):.2f} frame/s ; "
              f"mean fps over trace = {(max(fs)-min(fs))/max(ts):.3f} frame/s ; last f={fs[-1]} at t={ts[-1]:.2f}")

print("\n[b] process-gone fingerprint (ws_kb/pf_kb) in the dropped windows and in l1_20261023e4/w2")
for rel in ["l1_20261023c/measure_w0.json", "l3_20261023/measure_w0.json", "l1_20261023e4/measure_w2.json",
            "l3_1101v4b/measure_w0.json", "l3_1101v3c/measure_w0.json"]:
    d = J(*rel.split("/"))
    cs = d.get("counters") or []
    nz = [c for c in cs if c.get("ws_kb") not in (None,)]
    tail = cs[-1] if cs else {}
    print(f"    {rel:34s} verdict={d.get('verdict')} samples={(d.get('stats') or {}).get('samples')} "
          f"error={repr(d.get('error'))[:90]}")
    print(f"        first counter={json.dumps(cs[0], ensure_ascii=False)[:160] if cs else None}")
    print(f"        last  counter={json.dumps(tail, ensure_ascii=False)[:160] if tail else None}")

print("\n[c] counter continuity across the freeze boundary (prev window last second == frozen window first second)")
for dr in ["archive_T42", "archive_T33", "l3_20261023r", "archive_T38", "archive_T39"]:
    keys = ("units", "infantry", "aircraft", "g", "b", "techno", "g_items", "b_items")
    prev = None
    for w in (0, 1, 2):
        rel = f"{dr}/measure_w{w}.json"
        p = os.path.join(R, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        d = J(rel.split("/")[0], f"measure_w{w}.json") if "/" in rel else J(rel)
        cs = d.get("counters") or []
        if not cs:
            continue
        cur = tuple(cs[0].get(k) for k in keys)
        cur_last = tuple(cs[-1].get(k) for k in keys)
        if prev is not None:
            diff = [keys[i] for i in range(len(keys)) if prev[i] != cur[i]]
            print(f"    {dr} w{w}: prev-window-tail vs this-window-head differing fields = {diff}  head={cur}")
        prev = cur_last
        if w == 0:
            print(f"    {dr} w0 head={cur} tail={cur_last}  (gate.units0={d['gate'].get('units0')})")

print("\n[d] displayed time (MY reads from zoomed crops) vs frame number; 1 s quantisation bands")
MINE = [("archive_T33 w1", 738, 24), ("archive_T34 w1", 302, 10), ("archive_T36 w1", 310, 10),
        ("archive_T38 w2", 940, 32), ("archive_T39 w2", 945, 31), ("archive_T40 w1", 908, 30),
        ("archive_T41 w1", 860, 28), ("archive_T43 w1", 314, 10), ("archive_T44 w1", 883, 29),
        ("archive_T45 w1", 845, 28), ("archive_T49 w1", 448, 15), ("<root> T55h w1", 373, 13),
        ("l3_20261023r w2", 4367, 176)]
c312 = c300 = 0
for name, f, s in MINE:
    lo, hi = f / (s + 0.5), f / (s - 0.5)
    a = lo <= 31.2 <= hi
    b = lo <= 30.0 <= hi
    c312 += a
    c300 += b
    print(f"    {name:20s} f={f:5d} screen={s:4d}s band=[{lo:5.2f},{hi:5.2f}] width={hi-lo:4.2f}  31.2:{'Y' if a else 'N'}  30.0:{'Y' if b else 'N'}")
print(f"    31.2 inside band: {c312}/{len(MINE)} ; 30.0 inside band: {c300}/{len(MINE)}")
imp = [f / s for _, f, s in MINE]
print(f"    implied fps: median={statistics.median(imp):.2f} min={min(imp):.2f} max={max(imp):.2f}")
ex_l3r = [f / s for name, f, s in MINE if not name.startswith("l3_")]
print(f"    excluding l3_20261023r: median={statistics.median(ex_l3r):.2f} range=[{min(ex_l3r):.2f},{max(ex_l3r):.2f}]")
