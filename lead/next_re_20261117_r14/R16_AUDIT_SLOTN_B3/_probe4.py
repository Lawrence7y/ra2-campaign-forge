# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3")
from verify import COV, split_rows, parse_ring4

rows = split_rows(open(COV, "rb").read())
cov = {}
for i, ln in enumerate(rows[1:], start=2):
    c = ln.split(b"\t")
    if len(c) == 8:
        cov[c[0].decode()] = {"line": i, "cols": c}

BATCH = {"005B3060","005B3570","005B35E0","005B3650","005B36B0","005B4630",
         "00653100","0065CBF0","006B1850","006B1900","006B8660","006B8710","006F9E50"}
prec = [e for e, v in cov.items() if "④ 活表槽位见证" in v["cols"][3].decode("utf-8", "replace")]
bad = []
for e in prec:
    if e in BATCH:
        continue
    t = cov[e]["cols"][3].decode("utf-8", "replace")
    p = parse_ring4(t)
    if not p or not p.get("ok"):
        bad.append((e, t))

print("unparsable precedents:", len(bad))
for e, t in bad[:6]:
    i = t.find("④ 活表槽位见证：")
    print("\n===", e, "line", cov[e]["line"])
    print("SEG:", t[i:i + 700])
