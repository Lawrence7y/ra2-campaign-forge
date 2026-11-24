import json, sys

BASE = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/"
TRIPS = ["l3_1101v4e", "l3_1101v4f", "l3_1101v4g"]

def load(d):
    rows = json.load(open(BASE + d + "/qc151_fields.json", encoding="utf-8"))
    out = {}
    for r in rows:
        k = (r.get("group"), r.get("key"))
        # keep last occurrence, note if duplicates
        if k in out:
            out[k + ("dup",)] = r.get("value")
        out[k] = r.get("value")
    return out, rows

maps = {}
rows = {}
for d in TRIPS:
    maps[d], rows[d] = load(d)

allkeys = sorted({k for d in TRIPS for k in maps[d] if len(k) == 2})
print("total distinct (group,key):", len(allkeys))

groups = {}
for d in TRIPS:
    groups[d] = {}
    for (g, k) in allkeys:
        groups[d].setdefault(g, []).append(k)
print("groups per trip:")
for d in TRIPS:
    print("  ", d, {g: len(v) for g, v in sorted(groups[d].items())})

only = {d: [] for d in TRIPS}
for (g, k) in allkeys:
    present = [d for d in TRIPS if (g, k) in maps[d]]
    if len(present) != 3:
        only[present[0] if present else None].append((g, k))
for d in TRIPS:
    print("\n### keys present ONLY in", d, "(count", len(only[d]), ")")
    for g, k in only[d]:
        print("   ", g, "|", k, "=", repr(maps[d][(g, k)])[:120])

print("\n### DIFFERING VALUES (key present in all 3)")
n = 0
for (g, k) in allkeys:
    vals = [maps[d].get((g, k)) for d in TRIPS]
    if len(set(map(repr, vals))) > 1:
        n += 1
        print(f"  {g} | {k}: v4e={vals[0]!r}  v4f={vals[1]!r}  v4g={vals[2]!r}"[:300])
print("differing count:", n)
