# -*- coding: utf-8 -*-
"""报告撰写员只读上下文核查：
① T36/T43 w0 counters 死亡行后 g 列是否仍有波动（复核回件减损点 1 的再证）；
② 四个语料趟目录 + 2 个只读 md 在 2026-11-08 19:00 之后是否被改动。
零真机、零采样、只读；仅打印。"""
import datetime
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
CORPUS = os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip")
CUTOFF = datetime.datetime(2026, 11, 8, 19, 0, 0).timestamp()

print("== ① T36/T43 w0 counters 前 8 行（看 units 死亡行后 g 列是否恒定）==")
for trip in ("archive_T36", "archive_T43"):
    p = os.path.join(CORPUS, trip, "measure_w0.json")
    with open(p, "rb") as fh:
        d = json.loads(fh.read().decode("utf-8"))
    print(f"--- {trip} w0")
    for i, row in enumerate(d.get("counters", [])[:8]):
        print(f"  [{i:02d}] t_rel={row.get('t_rel'):>8} units={row.get('units')} inf={row.get('infantry')} "
              f"g={row.get('g')} b={row.get('b')} techno={row.get('techno')} ws_kb={row.get('ws_kb')} pf_kb={row.get('pf_kb')}")

print("== ② 语料/只读件 mtime > 2026-11-08 19:00 的文件 ==")
targets = []
for trip in ("l1_20261023e4", "archive_T34", "archive_T36", "archive_T43"):
    dp = os.path.join(CORPUS, trip)
    for fn in os.listdir(dp):
        targets.append(os.path.join(dp, fn))
targets.append(os.path.join(ROOT, "lead", "slowframe_round2_20261107", "SLOWFRAME_PROXY.md"))
targets.append(os.path.join(ROOT, "lead", "slowwindow_n8_20261108", "SLOW_WINDOW_LIMITS.md"))
hits = 0
for p in targets:
    mt = os.path.getmtime(p)
    if mt > CUTOFF:
        print(f"  MODIFIED-AFTER: {p} mtime={datetime.datetime.fromtimestamp(mt).isoformat()}")
        hits += 1
print(f"  scanned={len(targets)} modified_after_cutoff={hits}")
