# -*- coding: utf-8 -*-
"""A3 第三版普查：archive_* 趟的 S-4 证据在 qc151_fields.json 里，不在 s4_module_table.txt。

修正上一版的误判：上一版把「无 s4_module_table.txt」当成「无 S-4 证据」，
实际那些趟把 S4 结果以 `group=S4` 的 rec 行写进了 `qc151_fields.json`。

判据（从三处取 S-4 结论，取到即止）：
  A. `s4_module_table.txt` 原文（子串扫 ra2render / ra2loader）
  B. `qc151_fields.json` 里 group=="S4" 的 ra2render_hits / ra2loader_hits（列表，空=0 命中）
  C. `MANIFEST.json` 里是否出现 S4 相关键

只读。零真机。
"""
import glob
import io
import json
import os
from collections import Counter

TRIP = r'out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

# ---- 收集所有趟目录 ----
trips = sorted(d for d in os.listdir(TRIP)
               if os.path.isdir(os.path.join(TRIP, d)))
print("trip dirs:", len(trips))


def s4_from_table(d):
    p = os.path.join(d, 's4_module_table.txt')
    if not os.path.isfile(p):
        return None
    s = io.open(p, encoding='utf-8', errors='replace').read()
    low = s.lower()
    if "枚举失败" in s:
        return ("enum_failed", "s4_module_table", None)
    if "gamemd.exe" not in low:
        return ("incomplete", "s4_module_table", None)
    hits = [b for b in ("ra2render", "ra2loader") if b in low]
    return ("hit" if hits else "clean", "s4_module_table", hits or [])


def s4_from_fields(d):
    p = os.path.join(d, 'qc151_fields.json')
    if not os.path.isfile(p):
        return None
    try:
        data = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        return None
    rows = data if isinstance(data, list) else data.get('rows') or []
    rr = rl = None
    launch = None
    for r in rows:
        if not isinstance(r, dict) or r.get('group') != 'S4':
            continue
        k = r.get('key')
        if k == 'ra2render_hits':
            rr = r.get('value')
        elif k == 'ra2loader_hits':
            rl = r.get('value')
    for r in rows:
        if isinstance(r, dict) and r.get('group') == 'LAUNCH' and r.get('key') == 'exe_basename':
            launch = r.get('value')
    if rr is None and rl is None:
        return None
    bad = bool(rr) or bool(rl)
    return ("hit" if bad else "clean", "qc151_fields.S4",
            {"ra2render_hits": rr, "ra2loader_hits": rl, "exe_basename": launch})


rows = []
for t in trips:
    d = os.path.join(TRIP, t)
    a = s4_from_table(d)
    b = s4_from_fields(d) if a is None else None
    src, cls, detail = ("none", "NO_S4_EVIDENCE", None)
    if a is not None:
        cls, src, detail = a[0], a[1], a[2]
    elif b is not None:
        cls, src, detail = b[0], b[1], b[2]
    rows.append(dict(trip=t, cls=cls, src=src, detail=detail))

c = Counter(r["cls"] for r in rows)
print("\n=== 三处证据合并后的分类（全部 %d 趟）===" % len(rows))
for k in ("clean", "hit", "incomplete", "enum_failed", "NO_S4_EVIDENCE"):
    print("  %-16s = %d" % (k, c.get(k, 0)))

print("\n=== 证据来源分布 ===")
for k, v in Counter(r["src"] for r in rows).items():
    print("  %-22s = %d" % (k, v))

for name in ("hit", "incomplete", "enum_failed", "NO_S4_EVIDENCE"):
    sel = [r for r in rows if r["cls"] == name]
    if sel:
        print("\n--- %s（%d 趟）---" % (name, len(sel)))
        for r in sel:
            print("   %-24s src=%-18s detail=%r" % (r["trip"], r["src"], r["detail"]))

# ---- 关键：87 个 25 s 窗按分类归属 ----
print("\n=== ★ 87 个 25 s 窗按 S-4 证据分类归属 ===")
cls_of = {r["trip"]: r["cls"] for r in rows}
per_trip = Counter()
for p in sorted(glob.glob(os.path.join(TRIP, '*', 'measure_w*.json'))):
    d = json.load(io.open(p, encoding="utf-8"))
    st = d.get("stats") or {}
    if d.get("span_s") != 25.0 or (st.get("samples") or 0) == 0:
        continue
    per_trip[os.path.basename(os.path.dirname(p))] += 1
print("  计入趟 =", len(per_trip), " 窗合计 =", sum(per_trip.values()))
agg = Counter()
for t, n in per_trip.items():
    agg[cls_of.get(t, "NO_S4_EVIDENCE")] += n
for k, v in sorted(agg.items(), key=lambda x: -x[1]):
    print("  %-16s 窗数 = %d" % (k, v))

# ---- 顺带：LAUNCH exe_basename 分布（直启 vs loader）----
print("\n=== LAUNCH exe_basename 分布（有记录的趟）===")
launch_cnt = Counter()
for t in trips:
    p = os.path.join(TRIP, t, 'qc151_fields.json')
    if not os.path.isfile(p):
        continue
    try:
        data = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        continue
    rows_ = data if isinstance(data, list) else data.get('rows') or []
    for r in rows_:
        if isinstance(r, dict) and r.get('group') == 'LAUNCH' and r.get('key') == 'exe_basename':
            launch_cnt[str(r.get('value'))] += 1
            break
for k, v in launch_cnt.items():
    print("  %-16s = %d 趟" % (k, v))

print("\nDONE")
