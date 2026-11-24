"""V2-RECHECK census: independent recompute of the window census (both glob levels). Read-only.

Run: python -I -X utf8 v2r_census.py
"""
import json, os, glob
from collections import Counter, defaultdict

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

SUB = sorted(glob.glob(os.path.join(R, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(R, "measure_w*.json")))
print("[C0] ask-glob <TRIP>/*/measure_w*.json files =", len(SUB))
print("[C0] root-level <TRIP>/measure_w*.json files =", len(ROOT), [os.path.basename(p) for p in ROOT])


def classify(d):
    fe = d.get("frame_edges") or []
    if not fe:
        return "NO_EDGES", None, None, None
    f0, f1 = fe[0][0], fe[-1][0]
    df = f1 - f0
    if df > 0:
        return "ADV", f0, f1, df
    if df == 0:
        return ("LOAD" if f0 == 0 else "FRZ"), f0, f1, df
    return "BACK", f0, f1, df


def mkrow(p, at_root):
    d = json.load(open(p, encoding="utf-8"))
    k, f0, f1, df = classify(d)
    st = d.get("stats") or {}
    g = d.get("gate") or {}
    rel = os.path.relpath(p, R).replace("\\", "/")
    return dict(rel=rel, at_root=at_root, dir=("." if at_root else rel.split("/")[0]), kind=k,
                f0=f0, f1=f1, df=df, trip_id=d.get("trip_id"), fps=st.get("fps_avg"),
                span=d.get("span_s"), max_stall=st.get("max_stall_s"),
                logic_frames=st.get("logic_frames"), samples=st.get("samples"),
                n_edges=st.get("n_edges"), verdict=d.get("verdict"), error=d.get("error"),
                map_sha=(d.get("map_sha256") or "")[:8], units0=g.get("units0"),
                pre_fps15=g.get("pre_fps15"), gate_ok=g.get("ok"),
                t_abs0=d.get("t_abs0"), w=d.get("window"), counters=d.get("counters"))


SUB_ROWS = [mkrow(p, False) for p in SUB]
ALL_ROWS = SUB_ROWS + [mkrow(p, True) for p in ROOT]


def summarize(label, rs):
    c = Counter(r["kind"] for r in rs)
    cl = [r for r in rs if r["kind"] != "NO_EDGES"]
    print(f"\n[C1] === {label} ===")
    print("     files:", len(rs), "| class counts:", dict(sorted(c.items())))
    print("     classifiable windows:", len(cl),
          "| distinct <dir> buckets:", len({r["dir"] for r in cl}),
          "| distinct trip_id:", len({r["trip_id"] for r in cl}))
    print("     ADV:", c["ADV"], "FRZ:", c["FRZ"], "LOAD:", c["LOAD"], "BACK:", c["BACK"], "NO_EDGES:", c["NO_EDGES"])


summarize("SUBDIR ONLY  (the glob _leader_scorecensus.py:32 / the ask used)", SUB_ROWS)
summarize("SUBDIR + ROOT (whole corpus on disk)", ALL_ROWS)

adv_s = [r for r in SUB_ROWS if r["kind"] == "ADV"]
adv = [r for r in ALL_ROWS if r["kind"] == "ADV"]
frz_s = [r for r in SUB_ROWS if r["kind"] == "FRZ"]
frz = [r for r in ALL_ROWS if r["kind"] == "FRZ"]
print("\n[C2] ADV fps_avg split, subdir rows: n=%d  >=28:%d  <28:%d" %
      (len(adv_s), sum(1 for r in adv_s if (r["fps"] or 0) >= 28), sum(1 for r in adv_s if (r["fps"] or 0) < 28)))
print("[C2] ADV fps_avg split, all rows : n=%d  >=28:%d  <28:%d" %
      (len(adv), sum(1 for r in adv if (r["fps"] or 0) >= 28), sum(1 for r in adv if (r["fps"] or 0) < 28)))
print("[C2] FRZ count: subdir=%d  all=%d   (V2 reported 29 / 32)" % (len(frz_s), len(frz)))
print("[C2] any ADV window with missing fps_avg:", [r["rel"] for r in adv if r["fps"] is None])

# independent cross-check of df using samples.f instead of frame_edges
print("\n[C3] df via samples.f vs via frame_edges, over all classifiable windows")
bad = []
for r in ALL_ROWS:
    if r["kind"] == "NO_EDGES":
        continue
    d = json.load(open(os.path.join(R, r["rel"].replace("/", os.sep)), encoding="utf-8"))
    fs = d["samples"]["f"]
    s0, s1 = fs[0], fs[-1]
    fe = d["frame_edges"]
    if not (s0 == fe[0][0] and s1 == fe[-1][0]):
        bad.append((r["rel"], s0, s1, fe[0][0], fe[-1][0]))
print("     disagreements:", len(bad), bad[:10])

print("\n[C4] NO_EDGES files (silently dropped by both §538 and §543?)")
for r in [x for x in ALL_ROWS if x["kind"] == "NO_EDGES"]:
    print("    ", r["rel"], "| trip_id=", r["trip_id"], "| verdict=", r["verdict"],
          "| samples=", r["samples"], "| error=", repr(r["error"])[:150])

print("\n[C5] root-level 3 files: trip_id / frame / gate")
for r in [x for x in ALL_ROWS if x["at_root"]]:
    print("    ", r["rel"], "trip_id=", r["trip_id"], "f=", r["f0"], "pre_fps15=", r["pre_fps15"],
          "gate_ok=", r["gate_ok"], "units0=", r["units0"], "t_abs0=", r["t_abs0"])

print("\n[C6] BACK / LOAD windows")
for r in [x for x in ALL_ROWS if x["kind"] in ("BACK", "LOAD")]:
    print("    ", r["rel"], r["kind"], "f0=", r["f0"], "f1=", r["f1"], "df=", r["df"],
          "trip_id=", r["trip_id"], "verdict=", r["verdict"], "error=", repr(r["error"])[:120])

print("\n[C7] pre_fps15 per trip dir (is it a window-level or trip-level reading?)")
bydir = defaultdict(list)
for r in ALL_ROWS:
    if r["kind"] != "NO_EDGES":
        bydir[r["dir"]].append((r["w"], r["pre_fps15"]))
same = diff = 0
for dr, lst in sorted(bydir.items()):
    vals = {v for _, v in lst}
    if len(lst) > 1:
        if len(vals) == 1:
            same += 1
        else:
            diff += 1
            print("     DIFFER within dir:", dr, lst)
print("     multi-window dirs with identical pre_fps15: %d ; differing: %d" % (same, diff))

print("\n[C8] FRZ windows grouped by trip dir (V2 §5 folded w1/w2 rows)")
cnt = Counter(r["dir"] for r in frz_s)
print("     subdir FRZ dirs:", len(cnt), "windows:", sum(cnt.values()))
for dr, n in sorted(cnt.items()):
    f0 = [r["f0"] for r in frz_s if r["dir"] == dr][0]
    u0 = [r["units0"] for r in frz_s if r["dir"] == dr][0]
    print(f"     {dr:22s} windows={n} f0={f0:6d} units0={u0}")
