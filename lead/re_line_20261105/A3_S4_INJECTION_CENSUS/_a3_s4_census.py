# -*- coding: utf-8 -*-
"""A3 普查：历史趟件的 S-4 模块表里有没有 ra2render / ra2loader。

背景：W4 的 `card_00A8EC34.md` §6.2 发现 `ra2render.dll` 会在 `0x6F8DF0`
打 9 字节 Inline Hook 并节流跳过 `0x00A8EC34` 的自增。若历史趟件里该 DLL 在场，
则那些趟的该字段读数（若曾采过）不可信；反之若 S4 闸全绿，则镜像字节证据成立。

只读 out/re_work 下的 s4_module_table.txt 与 measure_w*.json。零真机。
"""
import glob
import io
import json
import os
import re

TRIP = r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

tables = sorted(glob.glob(os.path.join(TRIP, '*', 's4_module_table.txt')))
print("s4_module_table.txt found:", len(tables))

BAD = ("ra2render", "ra2loader", "RA2RENDER", "RA2LOADER")
rows = []
for p in tables:
    try:
        s = io.open(p, encoding="utf-8", errors="replace").read()
    except Exception as exc:
        rows.append({"path": p, "err": repr(exc)})
        continue
    low = s.lower()
    hits = [b for b in ("ra2render", "ra2loader") if b in low]
    # 统计模块行数
    nlines = len([l for l in s.splitlines() if l.strip().startswith("[")])
    rows.append({
        "path": p,
        "trip": os.path.basename(os.path.dirname(p)),
        "n_mods": nlines,
        "hits": hits,
        "empty": len(s.strip()) == 0,
    })

ok = [r for r in rows if "err" not in r]
print("parsed:", len(ok), " errors:", len(rows) - len(ok))
empty = [r for r in ok if r["empty"]]
print("empty tables:", len(empty))
for r in empty:
    print("   EMPTY", r["trip"])

hit = [r for r in ok if r["hits"]]
print("\n=== ★ 含 ra2render / ra2loader 的模块表 ===")
print("  数量 =", len(hit))
for r in hit:
    print("   HIT", r["trip"], r["hits"], "mods=%d" % r["n_mods"])

clean = [r for r in ok if not r["hits"] and not r["empty"]]
print("\n=== 干净（无注入模块、非空）===")
print("  数量 =", len(clean))
if clean:
    ns = sorted(r["n_mods"] for r in clean)
    print("  模块数 min=%d median=%d max=%d" % (ns[0], ns[len(ns)//2], ns[-1]))
    # 抽查：gamemd.exe 必须是模块 0
    p = clean[0]["path"]
    first = io.open(p, encoding="utf-8", errors="replace").readline().strip()
    print("  抽查首行:", first[:120])

# 交叉：有 measure_w*.json 的趟 是否都有 s4 表
mw = sorted(glob.glob(os.path.join(TRIP, '*', 'measure_w*.json')))
mw_trips = set(os.path.basename(os.path.dirname(p)) for p in mw)
tbl_trips = set(r["trip"] for r in ok)
print("\n=== 覆盖交叉 ===")
print("  有 measure_w*.json 的趟 =", len(mw_trips))
print("  有 s4 模块表的趟     =", len(tbl_trips))
print("  两者都有             =", len(mw_trips & tbl_trips))
print("  有 measure 但无 s4 表 =", len(mw_trips - tbl_trips))
for t in sorted(mw_trips - tbl_trips)[:10]:
    print("     ", t)
print("  有 s4 表但无 measure =", len(tbl_trips - mw_trips))

# 顺带：那些 HIT 趟若有 measure，看它们的 stats 是否被引用过
print("\n=== HIT 趟的 measure 读数（若有）===")
for r in hit:
    mp = sorted(glob.glob(os.path.join(TRIP, r["trip"], 'measure_w*.json')))
    print("  ", r["trip"], "measure files=%d" % len(mp))
    for q in mp:
        d = json.load(io.open(q, encoding="utf-8"))
        st = d.get("stats") or {}
        print("     w%s p50=%s verdict=%s" %
              (d.get("window"), st.get("frame_ms_p50"), d.get("verdict")))

print("\nDONE")
