# -*- coding: utf-8 -*-
import json, os, sys, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3")
from verify import (Image, EXE, COV, split_rows, parse_ring4, col_name_match,
                    enum_tables_of_entry, rtti_class, find_install_sites)

img = Image(EXE)
raw = open(COV, "rb").read()
rows = split_rows(raw)
cov = {}
dup = []
for i, ln in enumerate(rows[1:], start=2):
    c = ln.split(b"\t")
    if len(c) != 8:
        continue
    e = c[0].decode()
    if e in cov:
        dup.append((e, cov[e]["line"], i))
    cov[e] = {"line": i, "cols": c}

print("duplicate entries in coverage.tsv:", dup)

# 先例总体：所有含「④ 活表槽位见证」的行
prec_ids = [e for e, v in cov.items() if "④ 活表槽位见证" in v["cols"][3].decode("utf-8", "replace")]
print("总先例行数(含④ 活表槽位见证):", len(prec_ids))

def skel(d):
    core = d["core"]
    core = core.replace("→" + d["man"], "→<MAN>")
    core = core.replace(d["cls"], "<CLS>")
    core = re.sub(r"\b[0-9A-F]{8}\b", "<H>", core)
    core = re.sub(r"offset=\d+", "offset=<N>", core)
    core = re.sub(r"slot\d+", "slot<N>", core)
    core = re.sub(r"槽 \d+ 值", "槽 <N> 值", core)
    return core

sk = {}
bad = []
for e in prec_ids:
    if e in ("005B3060","005B3570","005B35E0","005B3650","005B36B0","005B4630",
             "00653100","0065CBF0","006B1850","006B1900","006B8660","006B8710","006F9E50"):
        continue
    p = parse_ring4(cov[e]["cols"][3].decode("utf-8", "replace"))
    if not p or not p.get("ok"):
        bad.append((e, "unparsed"))
        continue
    s = skel(p)
    sk.setdefault(s, []).append(e)

print("先例归一骨架种类数:", len(sk), "| 不可解析:", len(bad))
res = json.load(open(os.path.join(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3",
                                  "verify_out.json"), encoding="utf-8"))
bsk = res["meta"]["precedent_skeleton"]
mine = res["rows"][0]["E"]["skeleton"]
for i, (s, lst) in enumerate(sorted(sk.items(), key=lambda kv: -len(kv[1])), 1):
    print("--- 骨架#%d n=%d  ==本批骨架? %s" % (i, len(lst), s == mine))
    if s != mine:
        print("   ", s)
        print("    members:", lst[:6])
print("\n本批骨架 == 最大先例组 ?", mine in sk)

# 多表：本批行与先例行的表命中数
def ntables(e):
    return [(t["vt"], t["slot"], rtti_class(t["mangled"]), t["class"] if False else rtti_class(t["mangled"]))
            for t in enum_tables_of_entry(img, int(e, 16))]

for e in ("00464AC0", "004DE630", "004F42F0"):
    print(e, "命中表数:", len(ntables(e)), [(x[0], x[1]) for x in ntables(e)])
for e in ("005B3060", "005B3570", "005B35E0", "006F9E50"):
    print(e, "命中表数:", len(ntables(e)), [(x[0], x[1], x[2]) for x in ntables(e)])
