#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s07：(6) 闩→退间隔跨会话复算 + E5 批同侧主张原始回读 + 自检项数静态计数。
台账主张：hold13/14 间隔 2.004/2.008；历史 P3e 204921/205108 的 +2.009/+2.108；E5 hold10 +2.005；
--selftest 110 项红=0。全部回读原始 JSON / 静态计数代码，不采信总结。
"""
import json, io, sys, os, re, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"


def rec_of(d):
    return json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))


def tl_of(d):
    return json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))


print("### (6) 闩→退间隔：_rec 相减口径 vs 原始时间戳口径")
D = {"hold13": "20261030T211741_9001_P3e_E12_T1", "hold14": "20261030T212148_9001_P3e_E12_T1",
     "E5_hold10": "20261030T072242_9001_P3e_E12_T1", "E5_hold15": "20261030T072353_9001_P3e_E12_T1",
     "E5_hold20": "20261030T072630_9001_P3e_E12_T1"}
for k, d in D.items():
    if not os.path.isdir(f"{CB}/{d}"):
        print(f"  {k}: 目录缺失"); continue
    r, rows = rec_of(d), tl_of(d)["close_rows"]
    li = r.get("latch_row_index")
    sub = (round(r["exit_after_close_s"] - r["latch_after_close_s"], 4)
           if li is not None and r.get("exit_after_close_s") is not None else None)
    raw = (round(rows[-1]["t"] - rows[li]["t"], 4) if li is not None else None)
    rawsub = (round((rows[-1]["t"] - rows[0]["t"]) - (rows[li]["t"] - rows[0]["t"]), 4) if li is not None else None)
    print(f"  {k}: closed={r['closed_at_s']} latch={r['latch_detected']} idx={li} "
          f"latch_after(rec)={r.get('latch_after_close_s')} exit_after(rec)={r.get('exit_after_close_s')} "
          f"相减口径={sub} 原始时间戳口径={raw} | exit_kind={r.get('exit_kind')} code={r.get('final_exitcode')} "
          f"lastwait={rows[-1]['wait']}")

print("\n### 历史兑现趟 P3e 204921/205108（早窗批，非 E12 schema）")
for d in ("20261028T204921_9001_P3e_EARLY_MENU", "20261028T205108_9001_P3e_EARLY_MENU",
          "20261028T204123_9001_P3e_EARLY_MENU"):
    p = f"{CB}/{d}/_rec.json"
    if not os.path.isfile(p):
        print(f"  {d}: 无 _rec.json"); continue
    r = json.load(open(p, encoding="utf-8"))
    print(f"  {d}: keys={sorted(k for k in r if 'latch' in k or 'exit' in k or 'close' in k or 'hold' in k or 'boot' in k)}")
    print(f"     closed_at_s={r.get('closed_at_s')} exit_after_close_s={r.get('exit_after_close_s')} "
          f"latch_after_close_s={r.get('latch_after_close_s')} exit_kind={r.get('exit_kind')} "
          f"final_exitcode={r.get('final_exitcode')} boot_wallclock={r.get('boot_wallclock_ms_at_start')} "
          f"watch_s={r.get('watch_s')} verdict={r.get('verdict')}")
    for extra in ("latch_detected", "latch_row_index", "close_rows_n", "protocol", "hold_override"):
        if extra in r:
            print(f"     {extra}={r[extra]}")

print("\n### 自检项数静态计数（E5 候选件 selftest）")
ST = {"E5candidate": "lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_e12_selftest.py",
      "root": "lead/qc161_u0400_trip/_drive_c2_x_e12_selftest.py"}
for k, p in ST.items():
    if not os.path.isfile(p):
        print(f"  {k}: 缺失"); continue
    s = open(p, encoding="utf-8").read()
    calls = re.findall(r'(?m)^\s*t\(\s*"', s)
    print(f"  {k}: sha16={hashlib.sha256(s.encode()).hexdigest()[:16]} 行数={s.count(chr(10))+1} t(\"...\") 调用数={len(calls)}")
    e5 = re.findall(r'E5-\d+', s)
    print(f"     E5-* 标号出现={sorted(set(e5))}")
