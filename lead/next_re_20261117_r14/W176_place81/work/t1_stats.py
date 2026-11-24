import json, collections, os
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
d = json.load(open(os.path.join(OUT, "T1_byte81_all.json"), encoding="utf-8"))
h = d["hits"]
print("total", len(h))
print("mnem", collections.Counter(x["mnem"] for x in h))
print("bases", collections.Counter(x["base"] for x in h))
print("write", sum(x["write"] for x in h), "read", sum(x["read"] for x in h))
print("stack", [(hex(x["va"]), x["text"], x["access"]) for x in h if x["base"] in ("esp", "ebp")])
