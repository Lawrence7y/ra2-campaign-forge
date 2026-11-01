#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p13：~21s 带是「自启动锚」还是「自开机锚」——用 boot_ms_at_start(GetTickCount64)
   把事件换算成开机后秒数，跨 3 会话/跨度极大的 uptime 检验锚点归属。"""
import json, io, sys, os
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
CST = timezone(timedelta(hours=8))
ALL = [("hold13", "20261030T211741_9001_P3e_E12_T1", "闩"), ("hold14", "20261030T212148_9001_P3e_E12_T1", "闩"),
       ("hold15", "20261030T212233_9001_P3e_E12_T1", "不闩"), ("E5h10", "20261030T072242_9001_P3e_E12_T1", "闩"),
       ("E5h15", "20261030T072353_9001_P3e_E12_T1", "不闩"), ("E5h20", "20261030T072630_9001_P3e_E12_T1", "不闩"),
       ("E12-2228", "20261029T222811_9001_P3e_E12_T1", "闩"), ("E12-2316", "20261029T231621_9001_P3e_E12_T1", "闩"),
       ("P3e-204123", "20261028T204123_9001_P3e_EARLY_MENU", "闩"),
       ("P3e-204921", "20261028T204921_9001_P3e_EARLY_MENU", "闩"), ("P3e-205108", "20261028T205108_9001_P3e_EARLY_MENU", "闩"),
       ("b2-h15.3", "20261031T083340_9001_P3e_E12_T1", "不闩"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1", "不闩")]
print("{:<12} {:>6} {:>11} {:>13} {:>13} {:>13} {:>13}".format(
      "trip", "族", "boot_ms", "事件(自启动)", "事件墙钟", "事件(自开机)", "launch(自开机)"))
ev_launch, ev_boot = [], []
for tag, d, fam in ALL:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    hz = next((i for i, x in enumerate(rows) if x.get("hwnd") == 0), None)
    ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
    li = r.get("latch_row_index")
    li = ones[0] if (li is None and ones) else li
    idx = li if (fam == "闩" and li is not None) else hz
    if idx is None:
        print(f"  {tag}: 无事件行 → 跳过"); continue
    evs = rows[idx]["t"]
    relaunch = round(evs - t0, 3)
    bm, wm = r.get("boot_ms_at_start"), r.get("wallclock_ms_at_start")
    if bm is None or wm is None:
        print("{:<12} {:>6} {:>11} {:>13} {:>13} {:>13} {:>13}".format(
              tag, fam, "None", str(relaunch),
              datetime.fromtimestamp(evs, CST).strftime("%m-%d %H:%M:%S"), "旧schema 不可算", "旧schema"))
        ev_launch.append((tag, relaunch, fam)); continue
    relboot = round((wm / 1000 + relaunch) - (wm / 1000 - bm / 1000), 3)
    launch_relboot = round(bm / 1000, 3)
    print("{:<12} {:>6} {:>11} {:>13} {:>13} {:>13} {:>13}".format(
          tag, fam, bm, str(relaunch), datetime.fromtimestamp(evs, CST).strftime("%m-%d %H:%M:%S"),
          relboot, launch_relboot))
    ev_launch.append((tag, relaunch, fam)); ev_boot.append((tag, relboot, launch_relboot, fam))

print(f"\n自启动锚：全部 13 趟事件（闩=latch 行 / 不闩=hwnd 归零行）自启动秒数区间 "
      f"[{min(v for _, v, _ in ev_launch):.3f}, {max(v for _, v, _ in ev_launch):.3f}]")
lat = [v for _, v, f in ev_launch if f == "闩"]; nol = [v for _, v, f in ev_launch if f == "不闩"]
print(f"  闩族（latch 行）= {[round(v,3) for v in lat]}  不闩族（hz 归零）= {[round(v,3) for v in nol]}")
print(f"  可算 boot_ms 的趟中，事件(自开机) 与 launch(自开机) 差 = 事件相对启动 ≈ 21 s（非恒定开机秒数）:")
for tag, rb, lb, f in ev_boot:
    print(f"    {tag:<12} {f:<4} 事件自开机={rb:>12.1f}s  launch自开机={lb:>12.1f}s  差={round(rb - lb, 3)}")
print("\n⇒ 若带为「自开机」锚，则各趟事件自开机秒数应相近；实测相差达数万秒 ⇒ 带锚在**本趟启动（loader popen 后取时 t0）**，")
print("   与 §481 用词「绝对引擎事件带」须限定为「自启动绝对」，非「自开机绝对」。")
