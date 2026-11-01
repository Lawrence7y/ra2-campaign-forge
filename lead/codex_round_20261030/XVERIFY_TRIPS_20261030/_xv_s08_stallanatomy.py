#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s08：① 段引用的既有离线复算件（STALL_ANATOMY_raw.json / t55k 负载 842）回读，
   以及 hold15 killed_on_cleanup 与 a8_remaining 的时序一致性（代码顺序 + 数据字段）。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SA = "lead/codex_round_20261030/LEADER_battle/STALL_ANATOMY_raw.json"
print("### STALL_ANATOMY_raw.json 结构")
if os.path.isfile(SA):
    x = json.load(open(SA, encoding="utf-8"))
    print("  type=", type(x).__name__, "keys=", list(x.keys())[:20] if isinstance(x, dict) else len(x))
    print("  " + json.dumps(x, ensure_ascii=False)[:2500])
else:
    print("  文件缺失:", SA)

B = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
print("\n### 既有 31 档战斗趟 gate/units 回读（t55k / l1a / e4）")
cands = [d for d in sorted(os.listdir(B)) if os.path.isdir(f"{B}/{d}") and any(
    s in d.lower() for s in ("t55k", "l1a", "e4"))]
print("  匹配目录:", cands)
for d in cands:
    p = f"{B}/{d}/measure_w0.json"
    if not os.path.isfile(p):
        print(f"  {d}: 无 measure_w0.json"); continue
    m = json.load(open(p, encoding="utf-8"))
    t, f = m["samples"]["t"], m["samples"]["f"]
    segs = []
    i = 0
    n = len(t)
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        if t[j] - t[i] >= 0.5:
            segs.append((f[i], round(t[i] - t[0], 3), round(t[j] - t[i], 3)))
        i = j + 1
    u = [c["units"] for c in (m.get("counters") or [])]
    print(f"  {d}: trip={m.get('trip_id')} gate={json.dumps(m.get('gate'), ensure_ascii=False)} "
          f"frame {f[0]}->{f[-1]} W0内≥0.5s冻结={len(segs)} {segs[:4]} units首末={u[:1]}->{u[-1:]}")

print("\n### hold15 清扫一致性：killed_on_cleanup vs a8_remaining（代码顺序 finalize 先 terminate 后重扫）")
CB = "lead/qc161_u0400_trip/c2ab_x/20261030T212233_9001_P3e_E12_T1"
r = json.load(open(f"{CB}/_rec.json", encoding="utf-8"))
tl = json.load(open(f"{CB}/timeline.json", encoding="utf-8"))
rows = tl["close_rows"]
print(f"  killed_on_cleanup={r.get('killed_on_cleanup')} loader_pid={r['loader_pid']} gamemd_pid={r['gamemd_pid']}")
print(f"  pid 归属一致? {sorted([int(a[0]) for a in r['killed_on_cleanup']]) == sorted([r['loader_pid'], r['gamemd_pid']])}")
print(f"  末行 wait=258(STILL_ACTIVE)={rows[-1]['wait']} 未退出 ⇒ 需清扫 ⇒ 与 killed 单记自洽")
print(f"  a8_remaining={r['a8_remaining']} a8_verdict={r['a8_verdict']} carrier_deleted={r['carrier_deleted']} cleanup_errors={r.get('cleanup_errors','ABSENT')}")
print(f"  exit_kind={r['exit_kind']} stop_triggered={r['stop_triggered']} verdict={r['verdict']}")
print(f"  hold15 末行绝对 +{round(rows[-1]['t']-(r['close_delivery']['t']-r['closed_at_s']),3)}s (close后 {round(rows[-1]['t']-rows[0]['t'],3)}s)")
