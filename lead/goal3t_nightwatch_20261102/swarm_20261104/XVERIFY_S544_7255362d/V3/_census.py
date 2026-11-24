import json, os, hashlib, glob, re, collections

ROOT = "D:/Project/ra2-campaign-forge/"
LIST = ROOT + "lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/_list_all_measure.txt"
paths = [l.strip().decode('utf-8','ignore') if isinstance(l, bytes) else l.strip() for l in open(LIST, encoding='utf-8', errors='ignore') if l.strip()]
paths = [p.replace('\\', '/') for p in paths]
print("files:", len(paths))

rows = []
for p in paths:
    if not os.path.exists(p):
        # try case fix
        continue
    try:
        j = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        rows.append({"path": p, "readerr": str(e)[:80]})
        continue
    if not isinstance(j, dict):
        rows.append({"path": p, "notdict": True})
        continue
    g = j.get("gate") or {}
    s = j.get("samples") or {}
    f = s.get("f") if isinstance(s, dict) else None
    trip = os.path.dirname(p)
    rows.append({
        "path": p,
        "trip_id": j.get("trip_id"),
        "window": j.get("window"),
        "verdict": j.get("verdict"),
        "span_s": j.get("span_s"),
        "units0": g.get("units0"),
        "pre_fps15": g.get("pre_fps15"),
        "gate_ok": g.get("ok"),
        "nsamples": len(f) if f else None,
        "fmin": min(f) if f else None,
        "fmax": max(f) if f else None,
        "err": (j.get("error") or "")[:160] if isinstance(j.get("error"), str) else j.get("error"),
    })

json.dump(rows, open(ROOT + "lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/_census_measure.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

bad = [r for r in rows if r.get("units0") == 0]
print("\n### trips files with units0 == 0:", len(bad))
for r in bad:
    print(json.dumps(r, ensure_ascii=False))

print("\n### verdict census:", collections.Counter(str(r.get("verdict")) for r in rows))
print("\n### distinct trip dirs:", len({os.path.dirname(r['path']) for r in rows}))
