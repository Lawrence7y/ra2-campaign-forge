#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s13：全树扫描 measure_w*.json，检验台账主张
   「31 档 × ≥900 单位 × 活动交火 格此前不存在」与「31 档可测战斗负载从 842 推到 974」。
   判据（自算）：pre_fps15>=25（V11-a）∧ gate.units0>=900 ∧ W0 counters 有下降。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
rows = []
for d in sorted(os.listdir(ROOT)):
    p0 = os.path.join(ROOT, d, "measure_w0.json")
    if not os.path.isfile(p0):
        continue
    try:
        m = json.load(open(p0, encoding="utf-8"))
    except Exception as e:
        rows.append((d, "READ_FAIL", None, None, None, None, str(e)[:60]))
        continue
    g = m.get("gate") or {}
    cs = m.get("counters") or []
    u = [c["units"] for c in cs if c.get("units") is not None]
    dU = (u[-1] - u[0]) if len(u) >= 2 else None
    rows.append((d, g.get("pre_fps15"), g.get("units0"), (u[0] if u else None),
                 (u[-1] if u else None), dU, m.get("trip_id")))
print(f"扫描到含 measure_w0.json 的趟目录 {len(rows)} 个")
print(f"{'dir':34s} {'pre_fps15':>10} {'units0':>7} {'u首':>6} {'u末':>6} {'dU':>6}  trip")
for d, pre, u0, uf, ul, dU, tid in rows:
    print(f"{d:34s} {str(pre):>10} {str(u0):>7} {str(uf):>6} {str(ul):>6} {str(dU):>6}  {tid}")
print("\n### 满足 pre_fps15>=25 ∧ units0>=900 的趟（31 档 × ≥900 格）")
hits = [r for r in rows if isinstance(r[1], (int, float)) and r[1] >= 25 and isinstance(r[2], int) and r[2] >= 900]
for r in hits:
    print("  ", r)
print(f"  => 该格共 {len(hits)} 趟，目录={[r[0] for r in hits]}")
print("### 满足 pre_fps15>=25 的全部趟（31 档在场）按 units0 降序")
t31 = [r for r in rows if isinstance(r[1], (int, float)) and r[1] >= 25]
for r in sorted(t31, key=lambda x: -(x[2] or 0)):
    print(f"   {r[0]:34s} units0={r[2]} pre={r[1]}")
print("### 满足 units0>=900 的全部趟（不限档位）按 pre_fps15 降序")
t9 = [r for r in rows if isinstance(r[2], int) and r[2] >= 900]
for r in sorted(t9, key=lambda x: -(x[1] if isinstance(x[1], (int, float)) else -1)):
    print(f"   {r[0]:34s} units0={r[2]} pre={r[1]}")
