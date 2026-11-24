import json

BASE = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/"
TRIPS = ["l3_1101v4e", "l3_1101v4f", "l3_1101v4g"]

def load(d):
    rows = json.load(open(BASE + d + "/qc151_fields.json", encoding="utf-8"))
    out = {}
    for r in rows:
        out[(r.get("group"), r.get("key"))] = r.get("value")
    return out, rows

maps = {}
rawrows = {}
for d in TRIPS:
    maps[d], rawrows[d] = load(d)

GROUPS = ["NAV", "WIN", "TARGET", "MEASURE", "EXCEPT", "S4", "TERM", "CLOSE", "LA", "FRAME", "F", "CTRL", "CTRL1", "CTRL2", "A8", "WER"]
for g in GROUPS:
    keys = sorted({k for d in TRIPS for (gg, k) in maps[d] if gg == g})
    print("\n############ GROUP", g)
    for k in keys:
        vals = [maps[d].get((g, k)) for k2 in [None]]
        same = len({json.dumps(maps[d].get((g, k)), sort_keys=True) for d in TRIPS}) == 1
        print(f"--- {g}|{k}   [SAME across trips]" if same else f"*** {g}|{k}   [DIFFERS]")
        for d in TRIPS:
            print(f"    {d}: {json.dumps(maps[d].get((g, k)), ensure_ascii=False)}")
