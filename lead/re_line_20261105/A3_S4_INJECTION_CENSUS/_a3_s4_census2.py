# -*- coding: utf-8 -*-
"""A3 修正普查：S-4 模块表必须区分「干净」「枚举失败」「不完整」三种，
不能把「枚举失败」当成「无命中」。

判据（比上一版严格）：
  1. 表里有 "枚举失败" ⇒ 判定 `enum_failed`（不可判，**不得当作干净**）
  2. 表里没有 gamemd.exe ⇒ 判定 `incomplete`（拿不到目标模块，不可判身份）
  3. 命中 ra2render / ra2loader ⇒ 判定 `hit`
  4. 其余 ⇒ `clean`

只读。零真机。
"""
import glob
import io
import json
import os

TRIP = r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

tables = sorted(glob.glob(os.path.join(TRIP, '*', 's4_module_table.txt')))
print("s4_module_table.txt found:", len(tables))

rows = []
for p in tables:
    s = io.open(p, encoding="utf-8", errors="replace").read()
    low = s.lower()
    trip = os.path.basename(os.path.dirname(p))
    nmods = len([l for l in s.splitlines() if l.strip().startswith("[")])
    enum_failed = ("枚举失败" in s) or ("enumprocessmodules" in low and nmods == 0)
    has_gamemd = "gamemd.exe" in low
    hits = [b for b in ("ra2render", "ra2loader") if b in low]
    if hits:
        cls = "hit"
    elif enum_failed:
        cls = "enum_failed"
    elif not has_gamemd:
        cls = "incomplete"
    else:
        cls = "clean"
    rows.append(dict(trip=trip, path=p, nmods=nmods, enum_failed=enum_failed,
                     has_gamemd=has_gamemd, hits=hits, cls=cls))

from collections import Counter
c = Counter(r["cls"] for r in rows)
print("\n=== 严格分类 ===")
for k in ("clean", "hit", "incomplete", "enum_failed"):
    print("  %-12s = %d" % (k, c.get(k, 0)))

for name in ("hit", "incomplete", "enum_failed"):
    sel = [r for r in rows if r["cls"] == name]
    if sel:
        print("\n--- %s（%d）---" % (name, len(sel)))
        for r in sel:
            print("   %-22s nmods=%-3d gamemd=%s" %
                  (r["trip"], r["nmods"], r["has_gamemd"]))

# 干净趟的模块数
clean = [r for r in rows if r["cls"] == "clean"]
if clean:
    ns = sorted(r["nmods"] for r in clean)
    print("\n=== clean 趟的模块数 ===  n=%d min=%d median=%d max=%d"
          % (len(ns), ns[0], ns[len(ns)//2], ns[-1]))

# ---- 与 measure 的交叉，按严格分类 ----
mw = sorted(glob.glob(os.path.join(TRIP, '*', 'measure_w*.json')))
mw_trips = set(os.path.basename(os.path.dirname(p)) for p in mw)
print("\n=== 与 measure 交叉 ===")
print("  有 measure 的趟 =", len(mw_trips))
buckets = {}
for r in rows:
    buckets.setdefault(r["cls"], set()).add(r["trip"])
for cls in ("clean", "incomplete", "enum_failed", "hit"):
    ts = buckets.get(cls, set())
    print("  %-12s 覆盖 measure 趟 = %d" % (cls, len(ts & mw_trips)))

# ---- ★ 关键：87 个 25s 窗分别落在哪一类 ----
print("\n=== ★ 87 个 25 s 窗按 S-4 分类归属 ===")
per_trip = {}
for p in mw:
    d = json.load(io.open(p, encoding="utf-8"))
    st = d.get("stats") or {}
    if d.get("span_s") != 25.0 or (st.get("samples") or 0) == 0:
        continue
    trip = os.path.basename(os.path.dirname(p))
    per_trip.setdefault(trip, 0)
    per_trip[trip] += 1
print("  计入的趟 =", len(per_trip), " 窗合计 =", sum(per_trip.values()))

cls_of = {r["trip"]: r["cls"] for r in rows}
agg = Counter()
for trip, n in per_trip.items():
    agg[cls_of.get(trip, "NO_S4_TABLE")] += n
for k, v in sorted(agg.items(), key=lambda x: -x[1]):
    print("  %-14s 窗数 = %d" % (k, v))

noT = [t for t in per_trip if t not in cls_of]
print("\n  无 S-4 表的趟（窗数）:  %d 趟 / %d 窗"
      % (len(noT), sum(per_trip[t] for t in noT)))
for t in sorted(noT):
    print("     %-24s 窗数=%d" % (t, per_trip[t]))

print("\nDONE")
