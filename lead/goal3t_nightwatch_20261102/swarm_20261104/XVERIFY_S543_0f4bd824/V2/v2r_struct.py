"""Dump full structure of one frozen + one advancing measure json."""
import json, os
R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
for rel in ["archive_T42/measure_w1.json", "archive_T42/measure_w0.json"]:
    p = os.path.join(R, rel.replace("/", os.sep))
    d = json.load(open(p, encoding="utf-8"))
    print("=" * 70)
    print(rel)
    for k in sorted(d.keys()):
        v = d[k]
        if k == "samples":
            print(f"  samples: list({len(v)}) first={json.dumps(v[0])[:200]}")
            print(f"           last={json.dumps(v[-1])[:200]}")
        elif k == "counters":
            print(f"  counters: list({len(v)}) first={json.dumps(v[0])[:300]}")
            print(f"            last={json.dumps(v[-1])[:300]}")
        elif k == "frame_edges":
            print(f"  frame_edges: list({len(v)}) head={json.dumps(v[:3])} tail={json.dumps(v[-3:])}")
        else:
            print(f"  {k}: {json.dumps(v)[:400]}")
