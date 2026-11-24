import json, os, sys

ROOT = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
T42 = os.path.join(ROOT, "archive_T42")
E4 = os.path.join(ROOT, "l1_20261023e4")

def probe(path):
    with open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    print("== ", path)
    print("top keys:", sorted(d.keys()))
    for k in sorted(d.keys()):
        v = d[k]
        if isinstance(v, list):
            print(f"  {k}: list len={len(v)} head={v[:2]} tail={v[-2:]}" if v and not isinstance(v[0], dict) else f"  {k}: list len={len(v)}")
        elif isinstance(v, dict):
            print(f"  {k}: dict keys={sorted(v.keys())}")
        else:
            print(f"  {k}: {v!r}")

for w in ("w0", "w1", "w2"):
    probe(os.path.join(T42, f"measure_{w}.json"))
print("\n\n######## E4")
for w in ("w0", "w1", "w2"):
    probe(os.path.join(E4, f"measure_{w}.json"))
