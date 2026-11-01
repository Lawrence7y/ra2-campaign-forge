#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p04：归零后行为/字段恒定性/Δ 基准口径差/BOOT 会话的独立旁证。
   (a) hwnd、singleton 归零后是否持续 0（防单帧毛刺）；
   (b) rows 全字段值域（wait/code/code_read_ok/frame/tick/exitstate/hwnd/singleton）；
   (c) Δ 两种基准（rows[0].t vs close_delivery.t−closed_at_s）在 13 趟上的逐位差；
   (d) 用 preflight 落盘的 UPTIME + 文件 mtime 独立反推 BOOT 墙钟，与 _rec 记录值比对；
   (e) 载体残留目录；闩→退 R-1 纪律在本批是否可算（latch 无 ⇒ 不可算，须如实标）。
"""
import json, io, sys, os, hashlib
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CB = "lead/qc161_u0400_trip/c2ab_x"
CST = timezone(timedelta(hours=8))
ALL = [("hold13", "20261030T211741_9001_P3e_E12_T1"), ("hold14", "20261030T212148_9001_P3e_E12_T1"),
       ("hold15", "20261030T212233_9001_P3e_E12_T1"), ("E5h10", "20261030T072242_9001_P3e_E12_T1"),
       ("E5h15", "20261030T072353_9001_P3e_E12_T1"), ("E5h20", "20261030T072630_9001_P3e_E12_T1"),
       ("E12-1029T2228", "20261029T222811_9001_P3e_E12_T1"), ("E12-1029T2316", "20261029T231621_9001_P3e_E12_T1"),
       ("P3e-204123(挂死)", "20261028T204123_9001_P3e_EARLY_MENU"), ("P3e-204921", "20261028T204921_9001_P3e_EARLY_MENU"),
       ("P3e-205108", "20261028T205108_9001_P3e_EARLY_MENU"),
       ("b2-hold15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-hold15.8", "20261031T083611_9001_P3e_E12_T1")]

print("== (c) Δ 基准口径逐位差 ==")
print("   基准A（本线自定）：t0 = close_rows[0].t ；基准B（上轮 _xv_s11）：t0 = close_delivery.t − closed_at_s")
print("{:<19} {:>10} {:>10} {:>10} {:>12} {:>12} {:>10}".format(
      "trip", "close_s", "Δ_A", "Δ_B", "t0A", "t0B", "t0A−t0B"))
for tag, d in ALL:
    base = f"{CB}/{d}"
    r = json.load(open(f"{base}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{base}/timeline.json", encoding="utf-8"))["close_rows"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
    if not hz:
        print(f"  {tag}: 无 hwnd==0 → 跳过"); continue
    i = hz[0]
    t0A = rows[0]["t"]
    t0B = r["close_delivery"]["t"] - r["closed_at_s"]
    dA = round(rows[i]["t"] - t0A, 3)
    dB = round(rows[i]["t"] - t0B, 3)
    print("{:<19} {:>10.3f} {:>10} {:>10} {:>12.3f} {:>12.3f} {:>10.6f}".format(
        tag, r["closed_at_s"], dA, dB, t0A, t0B, round(t0A - t0B, 6)))

print("\n== (a) 归零持续性（本批 2 趟）+ (b) 全字段值域 ==")
for tag, d in ALL[-2:]:
    base = f"{CB}/{d}"
    rows = json.load(open(f"{base}/timeline.json", encoding="utf-8"))["close_rows"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
    sg = [i for i, x in enumerate(rows) if x.get("singleton") == 0]
    print(f"  {tag}: hwnd==0 行数={len(hz)} 首={hz[0]} 末={hz[-1]} 连续={len(hz) == hz[-1] - hz[0] + 1}")
    print(f"          singleton==0 行数={len(sg)} 首={sg[0]} 末={sg[-1]} 连续={len(sg) == sg[-1] - sg[0] + 1} 同一行={hz[0]==sg[0]}")
    print(f"          hwnd 归零后是否再非零: {any(x.get('hwnd') != 0 for x in rows[hz[0]:])}")
    print(f"          singleton 归零后是否再非零: {any(x.get('singleton') != 0 for x in rows[sg[0]:])}")
    for k in ("wait", "code", "code_read_ok", "exitstate", "frame", "tick"):
        v = sorted({(str(x.get(k))) for x in rows})
        print(f"          {k:<13} 值域={v}")
    print(f"          frame 非零行数={sum(1 for x in rows if x.get('frame'))}  tick 非零行数={sum(1 for x in rows if x.get('tick'))}"
          f"  （frame=0/tick=1 恒 ⇒ 采样期内无帧推进读数、非闩证据）")
    print(f"          归零前一行 idx={hz[0]-1} hwnd={rows[hz[0]-1]['hwnd']} singleton={rows[hz[0]-1]['singleton']}")
    print(f"          归零后 3 行: " + " | ".join(json.dumps(x) for x in rows[hz[0]:hz[0]+2]))

print("\n== (d) BOOT 会话独立旁证：preflight 落盘 UPTIME + 文件 mtime 反推 ==")
for f in ("lead/codex_round_20261030/LEADER_battle/preflight_batch2_20261031.txt",):
    mt = os.path.getmtime(f)
    txt = open(f, encoding="utf-8", errors="replace").read()
    import re
    m = re.search(r"UPTIME\(GetTickCount64\)=(\d+) ms", txt)
    up = int(m.group(1))
    print(f"  {f}: mtime={mt:.0f} ({datetime.fromtimestamp(mt, CST).strftime('%Y-%m-%dT%H:%M:%S+08')}) UPTIME={up} ms")
    implied = [round(mt - s - up / 1000, 3) for s in (0, 1)]
    print(f"    反推 boot_wallclock ∈ [{min(implied):.3f}, {max(implied):.3f}] (秒)")
    for tag, d in ALL[-2:]:
        r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
        bw = r["boot_wallclock_ms_at_start"] / 1000
        print(f"    {tag} 记录 boot_wall={bw:.3f} ⇒ 落在反推区间? {min(implied) <= bw <= max(implied)}")
print("  对照 §474 批（10-30 会话）boot_wall=1793337038106~119 ⇒ 与本批差 "
      f"{(1793406387119 - 1793337038119)/1000:.0f} s ≈ {(1793406387119 - 1793337038119)/1000/3600:.2f} h（不同会话）")
print("  对照 E5 批（10-29 会话）boot_wall=1793256614227~30 ⇒ 与本批差 "
      f"{(1793406387119 - 1793256614230)/1000/3600:.2f} h")

print("\n== (e) 载体/残留 与 R-1 可算性 ==")
for tag, d in ALL[-2:]:
    base = f"{CB}/{d}"
    r = json.load(open(f"{base}/_rec.json", encoding="utf-8"))
    ct = f"{base}/ct"
    print(f"  {tag}: out_dir/ct 存在? {os.path.exists(ct)}  目录内容={os.listdir(base)}")
    print(f"      latch_row_index={r['latch_row_index']} ⇒ 闩→退间隔(R-1) 可算? {r['latch_row_index'] is not None}")
    print(f"      stop_triggered={r['stop_triggered']} exited={r['exited']} exit_kind={r['exit_kind']} "
          f"final_exitcode={r['final_exitcode']} exit_after_close_s={r['exit_after_close_s']}")
    rows = json.load(open(f"{base}/timeline.json", encoding="utf-8"))["close_rows"]
    span = round(rows[-1]["t"] - rows[0]["t"], 3)
    hz0 = [i for i, x in enumerate(rows) if x.get("hwnd") == 0][0]
    print(f"      观察跨度(末行t − rows[0]t) = {span} s  watch_s={r['watch_s']}")
    print(f"      归零后仍持续观察到窗末 = {rows[-1]['t'] > rows[hz0]['t'] + 100}（归零后余 {round(rows[-1]['t']-rows[hz0]['t'],3)} s）")


