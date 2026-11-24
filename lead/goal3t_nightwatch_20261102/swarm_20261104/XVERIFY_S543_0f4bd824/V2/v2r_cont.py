"""Cross-window counter continuity for ALL frozen windows (V2 §4.2 claims 29/29 identical field-by-field),
and within-window constancy. Read-only."""
import os, glob, json

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(R, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(R, "measure_w*.json")))
KEYS = ("units", "infantry", "aircraft", "g", "b", "techno", "g_items", "b_items")


def cls(d):
    fe = d.get("frame_edges") or []
    if not fe:
        return "NO_EDGES", None, None
    f0, f1 = fe[0][0], fe[-1][0]
    df = f1 - f0
    return ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK"))), f0, df


by = {}
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    rel = os.path.relpath(p, R).replace("\\", "/")
    dr = "." if p in ROOT else rel.split("/")[0]
    k, f0, df = cls(d)
    by.setdefault(dr, []).append((d.get("window"), k, rel, d))

print("[X1] cross-window continuity at the freeze boundary, for every FRZ window with a predecessor")
n_equal = n_diff = 0
for dr, lst in sorted(by.items()):
    lst.sort(key=lambda x: (x[0] is None, x[0]))
    for i, (w, k, rel, d) in enumerate(lst):
        if k != "FRZ" or i == 0:
            continue
        pw, pk, prel, pd = lst[i - 1]
        cs_prev = (pd.get("counters") or [])
        cs_cur = (d.get("counters") or [])
        if not cs_prev or not cs_cur:
            print(f"    {rel:36s} predecessor {prel} has no counters (kind={pk}) -> skipped")
            continue
        a = tuple(cs_prev[-1].get(x) for x in KEYS)
        b = tuple(cs_cur[0].get(x) for x in KEYS)
        diff = [KEYS[j] for j in range(len(KEYS)) if a[j] != b[j]]
        if diff:
            n_diff += 1
            print(f"    DIFFERS {rel:36s} vs {prel:36s} fields={diff}")
            print(f"        prev tail = {a}")
            print(f"        this head = {b}")
        else:
            n_equal += 1
print(f"    identical across boundary: {n_equal} ; differing: {n_diff}")

print("\n[X2] within-window distinct counter tuples (V2: 29/29 constant)")
bad = []
tot = 0
for dr, lst in sorted(by.items()):
    for w, k, rel, d in lst:
        if k != "FRZ":
            continue
        tot += 1
        cs = d.get("counters") or []
        t = {tuple(c.get(x) for x in KEYS) for c in cs}
        if len(t) != 1:
            bad.append((rel, len(t), sorted(t)[:2]))
print(f"    FRZ windows total={tot}, with more than one distinct counter tuple: {len(bad)}")
for b in bad:
    print("      ", b)

print("\n[X3] how many windows in the whole corpus change g between consecutive windows (is g alive?)")
ch = 0
for dr, lst in sorted(by.items()):
    lst.sort(key=lambda x: (x[0] is None, x[0]))
    prev = None
    for w, k, rel, d in lst:
        cs = d.get("counters") or []
        if not cs:
            continue
        head = tuple(cs[0].get(x) for x in KEYS)
        if prev is not None and head != prev:
            ch += 1
        prev = tuple(cs[-1].get(x) for x in KEYS)
print("    transitions where the tuple changed between adjacent windows:", ch)
