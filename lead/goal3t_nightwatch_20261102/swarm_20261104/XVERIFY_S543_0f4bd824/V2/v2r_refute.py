"""V2-RECHECK: recompute from raw JSON the numbers the previous verifier and §543 both assert,
plus the harness's own per-window forensics records (empty_window / forensics_png).

Run: python -I -X utf8 v2r_refute.py
"""
import os, glob, json, hashlib
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


recs = {}
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    rel = os.path.relpath(p, R).replace("\\", "/")
    k, f0, df = cls(d)
    recs[rel] = dict(d=d, kind=k, f0=f0, df=df, dir=("." if p in ROOT else rel.split("/")[0]))

FRZ = [rel for rel, v in recs.items() if v["kind"] == "FRZ"]
FRZ_SUB = [rel for rel in FRZ if recs[rel]["dir"] != "."]

print("[Q1] frozen windows: game time from frame number, and counter delta vs gate.units0")
print(f'     {"dir/window":38s} {"f0":>6s} {"@31.2":>7s} {"@30.0":>7s} {"units0":>7s} {"units@frz":>9s} {"d_units":>8s} '
      f'{"inf":>5s} {"air":>4s} {"g":>5s} {"b":>4s} {"techno":>6s} {"ws_kb":>8s}')
per_dir = defaultdict(list)
for rel in FRZ:
    v = recs[rel]
    d = v["d"]
    g = d.get("gate") or {}
    c0 = (d["counters"] or [{}])[0]
    c1 = (d["counters"] or [{}])[-1]
    n_uniq = len({json.dumps({k: c.get(k) for k in ("units", "infantry", "aircraft", "g", "b", "techno", "g_items", "b_items")}, sort_keys=True) for c in (d["counters"] or [])})
    du = (c0.get("units") or 0) - (g.get("units0") or 0)
    per_dir[v["dir"]].append((rel, v["f0"], g.get("units0"), c0.get("units"), du, n_uniq))
    print(f'     {rel:38s} {v["f0"]:6d} {v["f0"]/31.2:7.2f} {v["f0"]/30.0:7.2f} {str(g.get("units0")):>7s} '
          f'{str(c0.get("units")):>9s} {du:8d} {str(c0.get("infantry")):>5s} {str(c0.get("aircraft")):>4s} '
          f'{str(c0.get("g")):>5s} {str(c0.get("b")):>4s} {str(c0.get("techno")):>6s} {str(c0.get("ws_kb")):>8s}  '
          f'distinct_counter_tuples={n_uniq}')

le30_312 = sum(1 for rel in FRZ_SUB if recs[rel]["f0"] / 31.2 <= 30.0)
le30_300 = sum(1 for rel in FRZ_SUB if recs[rel]["f0"] / 30.0 <= 30.0)
le15 = sum(1 for rel in FRZ_SUB if recs[rel]["f0"] / 31.2 <= 15.0)
print(f"     [V2 claim] subdir FRZ n={len(FRZ_SUB)}  f/31.2<=30.0 : {le30_312}   (V2 said 24/29)")
print(f"     f/30.0<=30.0 : {le30_300} ;  f/31.2<=15.0 : {le15}")
du_minus1 = sum(1 for rel in FRZ_SUB if (recs[rel]["d"]["counters"][0].get("units") or 0) - ((recs[rel]["d"].get("gate") or {}).get("units0") or 0) == -1)
print(f"     windows with d_units == -1 : {du_minus1}   (V2 said 20/29)")

print("\n[Q2] counters: are they per-house or global? keys available in every window")
k0 = recs[FRZ[0]]["d"]["counters"][0]
print("     counter record keys:", sorted(k0.keys()))
print("     sample:", json.dumps(k0, ensure_ascii=False))
print("     house/owner/side field present?", any("house" in k.lower() or "side" in k.lower() or "owner" in k.lower() for k in k0))

print("\n[Q3] unit population across the whole life of a frozen trip (T34, T42, T33): w0 vs w1")
for dr in ("archive_T34", "archive_T42", "archive_T33", "l3_20261023r"):
    for rel in sorted(r for r in recs if recs[r]["dir"] == dr):
        d = recs[rel]["d"]
        cs = d.get("counters") or []
        g = d.get("gate") or {}
        uniq = []
        for c in cs:
            t = (c.get("units"), c.get("infantry"), c.get("g"), c.get("b"), c.get("techno"))
            if not uniq or uniq[-1][1] != t:
                uniq.append((round(c.get("t_rel", 0), 3), t))
        fe = d.get("frame_edges") or []
        print(f"     {rel:34s} {recs[rel]['kind']:4s} f_edges_n={len(fe)} first={fe[0][0] if fe else None} last={fe[-1][0] if fe else None} units0={g.get('units0')}")
        print(f"          counter changes (t_rel, (units,inf,g,b,techno)): {uniq[:8]}{' ...' if len(uniq) > 8 else ''}  n_changes={len(uniq)}")

print("\n[Q4] fps ranking of l3_20261023r (S543 line 46: 'the slowest trip of the whole run')")
ADV = [(rel, recs[rel]["d"]["stats"].get("fps_avg")) for rel in recs if recs[rel]["kind"] == "ADV"]
target = [x for x in ADV if x[0].startswith("l3_20261023r")]
print("     l3_20261023r advancing windows:", target)
low = sorted([x for x in ADV if x[1] is not None], key=lambda kv: kv[1])
print("     advancing windows with fps_avg below l3r's minimum:",
      sum(1 for x in low if x[1] < min(v for _, v in target)))
print("     lowest 5:", low[:5])
per_dir_min = {}
for rel, v in ADV:
    dr = recs[rel]["dir"]
    if v is not None:
        per_dir_min[dr] = min(per_dir_min.get(dr, 1e9), v)
rank = sorted(per_dir_min.items(), key=lambda kv: kv[1])
print("     trips ranked by their slowest window:", [(i + 1, d, round(v, 3)) for i, (d, v) in enumerate(rank)][:12])
print("     l3_20261023r rank:", [i + 1 for i, (d, v) in enumerate(rank) if d == "l3_20261023r"], "of", len(rank))

print("\n[Q5] harness forensics records per frozen dir: empty_window vs forensics_png vs disk")
disk = {os.path.relpath(q, R).replace("\\", "/") for q in glob.glob(os.path.join(R, "*", "measure_w*_end_*.png"))}
for dr in sorted({recs[r]["dir"] for r in FRZ} - {"."}):
    fp = os.path.join(R, dr, "qc151_fields.json")
    if not os.path.exists(fp):
        print(f"     {dr:22s} NO qc151_fields.json")
        continue
    txt = open(fp, encoding="utf-8", errors="replace").read()
    j = json.loads(txt)
    hits = []
    def walk(o, path=""):
        if isinstance(o, dict):
            if "empty_window" in o or "forensics_png" in o or "current_frame" in o:
                hits.append((path, {k: o.get(k) for k in ("window", "empty_window", "forensics_png", "current_frame", "focus_ok", "verdict") if k in o}))
            for k, v in o.items():
                walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + f"[{i}]")
    walk(j)
    print(f"     --- {dr} ({len(hits)} forensics records)")
    for path, h in hits:
        png = h.get("forensics_png")
        exists = (f"{dr}/{png}" in disk) if png else None
        print(f"        {path[-46:]:46s} {json.dumps(h, ensure_ascii=False)[:150]} png_on_disk={exists}")
