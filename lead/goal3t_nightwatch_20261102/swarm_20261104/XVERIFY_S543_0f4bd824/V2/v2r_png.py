"""V2-RECHECK: every measure_w*_end_*.png on disk -> size, mtime, sha256; group byte-duplicates;
compare mtime against that window's own end instant (t_abs0 + span_s); map png availability
onto the 29 (and 32) FRZ windows. Read-only: bytes are read, never decoded.

Run: python -I -X utf8 v2r_png.py
"""
import json, os, glob, re, hashlib, datetime
from collections import defaultdict

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(R, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(R, "measure_w*.json")))


def classify(d):
    fe = d.get("frame_edges") or []
    if not fe:
        return "NO_EDGES", None, None
    f0, f1 = fe[0][0], fe[-1][0]
    df = f1 - f0
    return ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK"))), f0, df


wins = {}
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    k, f0, df = classify(d)
    rel = os.path.relpath(p, R).replace("\\", "/")
    wins[rel] = dict(kind=k, f0=f0, df=df, t_abs0=d.get("t_abs0"), span=d.get("span_s"),
                     dir=("." if p in ROOT else rel.split("/")[0]), w=d.get("window"),
                     map_sha=(d.get("map_sha256") or "")[:8], trip_id=d.get("trip_id"),
                     units0=(d.get("gate") or {}).get("units0"))

PNG = sorted(glob.glob(os.path.join(R, "*", "measure_w*_end_*.png"))) + \
      sorted(glob.glob(os.path.join(R, "measure_w*_end_*.png")))
print("[P0] end pngs found:", len(PNG), "(subdir %d + root %d)" %
      (len([q for q in PNG if os.path.dirname(q).replace("\\", "/") != R]), len([q for q in PNG if os.path.dirname(q).replace("\\", "/") == R])))

recs = []
unmatched = []
for q in PNG:
    rel = os.path.relpath(q, R).replace("\\", "/")
    dr = "." if "/" not in rel else rel.split("/")[0]
    base = rel.split("/")[-1]
    m = re.match(r"^measure_w(\d+)_end_.*\.png$", base)
    if not m:
        unmatched.append(rel)
        continue
    jrel = ("measure_w%s.json" % m.group(1)) if dr == "." else ("%s/measure_w%s.json" % (dr, m.group(1)))
    jw = wins.get(jrel)
    if jw is None:
        unmatched.append(rel + " -> " + jrel)
    b = open(q, "rb").read()
    h = hashlib.sha256(b).hexdigest()
    stt = os.stat(q)
    endabs = (jw["t_abs0"] + jw["span"]) if jw and jw["t_abs0"] and jw["span"] else None
    recs.append(dict(rel=rel, size=stt.st_size, mtime=stt.st_mtime, sha=h, jsonrel=jrel,
                     kind=(jw["kind"] if jw else "NO_JSON"), f0=(jw["f0"] if jw else None),
                     map=(jw["map_sha"] if jw else None), trip_id=(jw["trip_id"] if jw else None),
                     delta=(stt.st_mtime - endabs) if endabs else None,
                     mt=str(datetime.datetime.fromtimestamp(stt.st_mtime)),
                     winend=str(datetime.datetime.fromtimestamp(endabs)) if endabs else "n/a"))

print("[P0b] pngs whose window json does not exist:", unmatched)

print("\n[P1] per-png table (mtime vs that window's own end instant t_abs0+span_s)")
for r in sorted(recs, key=lambda x: x["rel"]):
    ds = "     n/a" if r["delta"] is None else f'{r["delta"]:+9.2f}'
    print(f'    {r["rel"]:46s} size={r["size"]:7d} mtime={r["mt"]} winend={r["winend"]} dt={ds} '
          f'sha={r["sha"][:8]} class={r["kind"]:8s} f0={r["f0"]} map={r["map"]}')

print("\n[P2] byte-duplicate groups (identical sha256 across files)")
g = defaultdict(list)
for r in recs:
    g[r["sha"]].append(r)
for h, lst in sorted(g.items(), key=lambda kv: -len(kv[1])):
    if len(lst) > 1:
        print(f'    sha {h[:8]} n={len(lst)} size={sorted({x["size"] for x in lst})} '
              f'dirs={sorted({x["rel"].split("/")[0] for x in lst})} maps={sorted({str(x["map"]) for x in lst})} '
              f'f0={sorted({str(x["f0"]) for x in lst})} classes={sorted({x["kind"] for x in lst})} '
              f'mtime={sorted({x["mt"] for x in lst})}')
        for x in lst:
            print(f'        {x["rel"]:46s} mtime={x["mt"]} winend={x["winend"]} dt={x["delta"]}')
print(f"    files={len(recs)} distinct sha={len(g)} singletons={sum(1 for h, l in g.items() if len(l) == 1)}")

print("\n[P3] FRZ coverage: does each frozen window have its own end png?")
png_by_json = {r["jsonrel"]: r for r in recs}
frz = {k: v for k, v in wins.items() if v["kind"] == "FRZ"}
frz_sub = {k: v for k, v in frz.items() if v["dir"] != "."}
for label, subset in (("subdir FRZ (the 29)", frz_sub), ("all FRZ (32)", frz)):
    have = [k for k in subset if k in png_by_json]
    none = sorted(k for k in subset if k not in png_by_json)
    print(f'    {label}: windows={len(subset)} with_own_png={len(have)} without_png={len(none)}')
    for k in none:
        print("        NO PNG:", k, "f0=", subset[k]["f0"], "units0=", subset[k]["units0"])
    shas = {png_by_json[k]["sha"] for k in have}
    print(f"        distinct byte-shas among those {len(have)} pngs: {len(shas)}")

print("\n[P4] FRZ windows sharing ONE image across dirs/maps")
bysha = defaultdict(list)
for k, r in png_by_json.items():
    if wins.get(k, {}).get("kind") == "FRZ":
        bysha[r["sha"]].append((k, r["rel"].split("/")[0], r["map"], r["f0"], r["delta"]))
for h, lst in bysha.items():
    if len(lst) > 1:
        print(f"    sha {h[:8]}: n={len(lst)} dirs={sorted({x[1] for x in lst})} maps={sorted({str(x[2]) for x in lst})} f0={sorted({x[3] for x in lst})}")
        for x in lst:
            print("        ", x)

print("\n[P5] other pngs in the frozen dirs: frame_target* + their sha (are they the same image as end_x?)")
endsha = {r["sha"] for r in recs}
for dr in sorted({v["dir"] for v in frz.values()} - {"."}):
    for q in sorted(glob.glob(os.path.join(R, dr, "frame_target*.png"))):
        b = open(q, "rb").read()
        h = hashlib.sha256(b).hexdigest()
        print(f'    {os.path.relpath(q, R).replace(chr(92), "/"):48s} size={len(b):7d} sha={h[:8]} '
              f'in_end_set={h in endsha}')
