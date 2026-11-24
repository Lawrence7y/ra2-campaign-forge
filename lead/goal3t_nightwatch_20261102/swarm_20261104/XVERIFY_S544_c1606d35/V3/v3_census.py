# -*- coding: utf-8 -*-
"""V3 §544 分诊：全库 no_advance 普查 + 007CFC9F 地址普查 + 回归排查辅助字段。"""
import json, os, re, hashlib
from collections import Counter

ROOT = "D:/Project/ra2-campaign-forge/"
OUT = ROOT + "lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3/"
TRIPS = ROOT + "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

mfiles = [x.strip() for x in open(OUT + "measure_files.txt", encoding="utf-8") if x.strip()]
efiles = [x.strip() for x in open(OUT + "except_files.txt", encoding="utf-8") if x.strip()]
print("measure files:", len(mfiles), " except files:", len(efiles))

print("=" * 100)
print("SECTION 5A: 全库 units0=0 且 verdict=no_advance 的完整清单")
print("=" * 100)
allrows = []
for rel in mfiles:
    p = ROOT + rel.lstrip("./")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as ex:
        print("  JSON ERR", rel, ex)
        continue
    u = d.get("gate", {}).get("units0")
    v = d.get("verdict")
    pf = d.get("gate", {}).get("pre_fps15")
    allrows.append((rel, u, v, pf, d))
hits = [(r, u, v, pf, d) for (r, u, v, pf, d) in allrows if u == 0 and v == "no_advance"]
print("units0==0 且 verdict=='no_advance' 命中数:", len(hits))
for (r, u, v, pf, d) in hits:
    print("  HIT", r)
    print("     trip_id:", d.get("trip_id"), " gate:", d.get("gate"),
          " span_s:", d.get("span_s"), " samples:", d.get("stats", {}).get("samples"),
          " note:", d.get("stats", {}).get("note"))
    fs = d.get("samples", {}).get("f", [])
    print("     samples.f distinct:", sorted(Counter(fs).items())[:6], "len", len(fs),
          " all_zero:", all(x == 0 for x in fs))
# broader: any units0==0 regardless of verdict
u0 = [(r, u, v, pf) for (r, u, v, pf, d) in allrows if u == 0]
print("\nunits0==0（不限 verdict）:", len(u0))
for x in u0:
    print("   ", x)
na = [(r, u, v, pf) for (r, u, v, pf, d) in allrows if v == "no_advance"]
print("\nverdict=='no_advance'（不限 units0）:", len(na))
for x in na:
    print("   ", x)

print()
print("=" * 100)
print("SECTION 5B: 每个 no_advance 趟的 except 地址 007CFC9F")
print("=" * 100)
hitdirs = sorted({os.path.dirname(ROOT + r.lstrip("./")) for (r, u, v, pf, d) in hits})
print("命中趟目录数:", len(hitdirs))
for dd in hitdirs:
    exfs = sorted(fn for fn in os.listdir(dd) if fn.startswith("except_post_") and fn.endswith(".txt"))
    for fn in exfs:
        p = os.path.join(dd, fn)
        raw = open(p, "rb").read()
        txt = raw.decode("utf-8", errors="replace").upper()
        has = "007CFC9F" in txt
        exc_line = ""
        m = re.search(r"Exception occurred at ([0-9A-F]{8})", txt)
        if m:
            exc_line = m.group(1)
        print(f"  {dd.replace(ROOT,'')}/{fn}: 007CFC9F={has} ExceptionAddr={exc_line} "
              f"Eip={re.search(r'EIP:([0-9A-F]{8})',txt).group(1) if re.search(r'EIP:([0-9A-F]{8})',txt) else '-'} "
              f"sha={hashlib.sha256(raw).hexdigest()[:16]}")

print()
print("=" * 100)
print("SECTION 5C: 全库 112 份 except_post_*.txt 中 007CFC9F 出现统计")
print("=" * 100)
with_addr, without = [], []
addr_hist = Counter()
for rel in efiles:
    p = ROOT + rel.lstrip("./")
    raw = open(p, "rb").read()
    txt = raw.decode("utf-8", errors="replace")
    m = re.search(r"Exception occurred at ([0-9A-Fa-f]{8})", txt)
    a = m.group(1).upper() if m else "NO_EXCEPTION_LINE"
    addr_hist[a] += 1
    (with_addr if "007CFC9F" in txt.upper() else without).append((rel, a))
print("except_post 总数:", len(efiles), " 含 007CFC9F:", len(with_addr), " 不含:", len(without))
print("Exception occurred at 地址直方图:")
for a, n in addr_hist.most_common():
    print(f"   {a}: {n}")
print("不含 007CFC9F 的 except 文件（前 20）:")
for rel, a in without[:20]:
    print("   ", rel, "addr=", a)
print("含 007CFC9F 的 except 文件（前 10 示例）:")
for rel, a in with_addr[:10]:
    print("   ", rel, "addr=", a)

print()
print("=" * 100)
print("SECTION 6: 三趟 launch/version/回归排查字段")
print("=" * 100)
TAGS = ["l3_1101v4e", "l3_1101v4f", "l3_1101v4g"]
for aux in ["_launch_result.json", "qc151_run_log.json", "qc151_fields_post.json",
            "carrier_post_state.json", "s4_module_table.txt", "T0_T1_diff.json"]:
    print(f"\n--- {aux}")
    for t in TAGS:
        p = os.path.join(TRIPS, t, aux)
        if not os.path.exists(p):
            print(f"  {t}: MISSING")
            continue
        raw = open(p, "rb").read()
        print(f"  {t}: bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()[:24]}")
        if aux.endswith(".json"):
            d = json.loads(raw.decode("utf-8", errors="replace"))
            s = json.dumps(d, ensure_ascii=False)
            print("     ", s[:600])
        else:
            print("     ", raw.decode("utf-8", errors="replace")[:350].replace("\n", " | "))

# harness sha / map sha from fields
print("\n--- qc151_fields.json 中 harness/version/argv/schema/map 相关字段")
for t in TAGS:
    d = json.load(open(os.path.join(TRIPS, t, "qc151_fields.json"), encoding="utf-8"))
    print(f"  === {t}")
    for e in d:
        k = e["key"]
        if re.search(r"harness|sha16|argv|schema|version|map_sha|gamemd_sha|carrier_sha|script|cmdline|trip_id", k, re.I):
            print(f"    {k:45s} = {repr(e['value'])[:160]}")

print("\nDONE")
