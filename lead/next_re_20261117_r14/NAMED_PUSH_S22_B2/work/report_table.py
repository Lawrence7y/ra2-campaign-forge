# -*- coding: utf-8 -*-
"""Emit a compact per-row anchor table (markdown) for the REPORT, so every row has its own addresses."""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "verdicts.json"), encoding="utf-8") as f:
    V = json.load(f)

print("| # | entry | ②槽/vt/COL→TD | ③ QI站点/对象ctor→主vt/release | ④ alloc/ctor/reg/CLSID/host-atexit |")
print("|---:|---|---|---|---|")
for i, v in enumerate(V, 1):
    r2 = v["r2"]; r3 = v["r3b"]; r4 = v["r4"]
    r2s = "%s / %s / %s→%s" % (r2["slot_va"], r2["vtable"], r2["col"], r2["td"])
    r3s = "%s / %s→%s / %s" % (r3["qi_site"]["addr"], r3["obj_ctor"], r3["mainvt"]["vt"], r3["release"]["addr"])
    r4s = "%s / %s / %s / %s / []" % (r4["alloc"], r4["ctor_call"], r4["reg_call"], r4["clsid"])
    print("| %d | %s | %s | %s | %s |" % (i, v["entry"], r2s, r3s, r4s))
