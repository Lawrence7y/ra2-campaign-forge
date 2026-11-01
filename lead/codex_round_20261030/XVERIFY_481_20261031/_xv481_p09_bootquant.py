#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p09：boot_ms 量化粒度检验（433000 是否可疑整千）+ preflight/trip 时钟一致性 + 13 趟开销表。"""
import json, io, sys, os, glob, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"

print("== boot_ms_at_start 是否落在 15.625 ms（1/64 s）量化格上 ==")
for p in sorted(glob.glob(f"{CB}/2*/_rec.json")):
    r = json.load(open(p, encoding="utf-8"))
    b = r.get("boot_ms_at_start")
    if b is None:
        print(f"  {os.path.basename(os.path.dirname(p))[:42]:<44} boot_ms=None（旧 schema）"); continue
    q = b / 15.625
    print(f"  {os.path.basename(os.path.dirname(p))[:42]:<44} boot_ms={b:<12} /15.625={q:<14} 整? {q == int(q)}  /1000整? {b % 1000 == 0}")

print("\n== preflight 读数与 trip1 起始的一致性（同一会话交叉旁证）==")
pt = open("lead/codex_round_20261030/LEADER_battle/preflight_batch2_20261031.txt", encoding="utf-8", errors="replace").read()
up = int(re.search(r"UPTIME\(GetTickCount64\)=(\d+) ms", pt).group(1))
mt = os.path.getmtime("lead/codex_round_20261030/LEADER_battle/preflight_batch2_20261031.txt")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    du = r["boot_ms_at_start"] - up
    dw = r["wallclock_ms_at_start"] / 1000 - mt
    print(f"  {tag}: Δuptime={du/1000:.3f}s  Δwallclock={dw:.3f}s  差={abs(du/1000 - dw)*1000:.1f} ms ⇒ 同会话一致={abs(du/1000 - dw) < 0.2}")

print("\n== 13 趟 closed_at_s − hold 的分解（launch→窗口 vs 循环过冲 vs 投递）本批 2 趟 ==")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    tl = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))
    ht = tl["hold_tl"]; rows = tl["close_rows"]
    hold = r["e2_params"]["hold_after_window_s"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    th = ht[0]["t"]
    last_read = ht[-1]["t"]
    tclose = r["close_delivery"]["t"]
    print(f"  {tag}: t0(启动)={t0:.3f} hold首读={th:.3f} ⇒ 启动→hold开始={th - t0:.3f}s")
    print(f"          hold末读={last_read:.3f} 读数数={len(ht)} 实测跨度={last_read - th:.3f}s (hold_s={hold})")
    print(f"          末读→t_close={tclose - last_read:.3f}s（含 sleep 1.0 后循环退出判定 + 截图）")
    print(f"          closed_at_s={r['closed_at_s']} = (启动→hold开始)+(hold 循环跨度)+(末读→t_close) = "
          f"{round((th - t0) + (last_read - th) + (tclose - last_read), 3)}")
    print(f"          §481 口径 closed−hold = {round(r['closed_at_s'] - hold, 3)} = 启动→hold {th - t0:.3f} + 循环过冲/量化 "
          f"{round((last_read - th) + (tclose - last_read) - hold, 3)}")
    shot = [s for s in r["shots"] if s["tag"] == "pre_close"][0]
    print(f"          pre_close 截图 t={shot['t']:.3f}（与 close_delivery.t 同值={shot['t'] == tclose}）")
