#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 脚本 s02：② 深挖 —— E2 慢采样来源行、闩行前后节拍、hold15 观察窗与闩盲区量化、
   闩绝对时刻、close_rows 时间间隔分布（是否 0.1s 节律）、以及 (11.19,16.09) 缝内实测点是否成立。
"""
import json, os, io, statistics, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
BASE = os.path.join(ROOT, "lead", "qc161_u0400_trip", "c2ab_x")
TRIPS = {"hold13": "20261030T211741_9001_P3e_E12_T1",
         "hold14": "20261030T212148_9001_P3e_E12_T1",
         "hold15": "20261030T212233_9001_P3e_E12_T1"}

def J(tag, name): return json.load(open(os.path.join(BASE, TRIPS[tag], name), encoding="utf-8"))

for tag in TRIPS:
    rec, tl = J(tag, "_rec.json"), J(tag, "timeline.json")
    rows, slow = tl["close_rows"], tl.get("slow_sample_rows", rec.get("slow_sample_rows", []))
    print(f"===== {tag}")
    dt = [round(rows[i+1]["t"] - rows[i]["t"], 4) for i in range(len(rows)-1)]
    if dt:
        print(f"  close_rows 相邻 dt: n={len(dt)} min={min(dt)} max={max(dt)} median={statistics.median(dt)}")
        print(f"  dt>0.5s 的间隙数={sum(1 for x in dt if x>0.5)} 值={[x for x in dt if x>0.5][:10]}")
    if tag != "hold15":
        e2 = tl["_e2"]
        sl = e2["slow_sample_rows"]
        print(f"  _e2.slow_sample_rows n={len(sl)}")
        for i, r in enumerate(sl):
            print(f"    slow[{i}] t={r['t']} pair_close_row_index={r['pair_close_row_index']} "
                  f"hook6={r.get('hook6')} ws_kb={r.get('ws_kb')} cpu={ (r.get('cpu') or {}).get('state')}/{(r.get('cpu') or {}).get('delta_s')} "
                  f"visible_windows={r.get('visible_windows')} except_check={r.get('except_check')}")
            pi = r["pair_close_row_index"]
            if pi < len(rows):
                pr = rows[pi]
                print(f"      paired close_row[{pi}]: t={pr['t']} wait={pr['wait']} exitstate={pr.get('exitstate')} "
                      f"hwnd={pr.get('hwnd')} singleton={pr.get('singleton')} frame={pr.get('frame')} tick={pr.get('tick')}")
        latch = e2["latch"]
        if latch:
            print(f"  _e2.latch = {json.dumps(latch, ensure_ascii=False)[:600]}")
        summ = e2.get("summary")
        print(f"  _e2.summary = {json.dumps(summ, ensure_ascii=False)}")
    else:
        print(f"  _e2 latch={tl['_e2']['latch']} slow n={len(tl['_e2']['slow_sample_rows'])} summary={json.dumps(tl['_e2']['summary'],ensure_ascii=False)}")
    # 闩绝对时刻（相对进程启动 t0，t0 = close_delivery.t - closed_at_s）
    t0 = rec["close_delivery"]["t"] - rec["closed_at_s"]
    print(f"  t0(推算启动时刻)={round(t0,3)} loader_pid={rec['loader_pid']} gamemd_pid={rec['gamemd_pid']}")
    if rec["latch_detected"]:
        li = rec["latch_row_index"]
        print(f"  闩绝对时刻(相对t0)={round(rows[li]['t']-t0,3)}  exitstate==1 行={[i for i,r in enumerate(rows) if r.get('exitstate')==1]}")
    # 闩前最后一行 exitstate=0 的时刻
    zs = [i for i, r in enumerate(rows) if r.get("exitstate") == 0]
    print(f"  exitstate==0 行范围: first={zs[0] if zs else None} last={zs[-1] if zs else None}")
    # frame 轴退化检查（菜单早窗：frame 恒 0）
    fr = set()
    for r in rows:
        v = r.get("frame"); fr.add(f"dict:{v.get('state')}" if isinstance(v, dict) else v)
    print(f"  frame 值域={fr}")
    # tick 轴
    tk = set()
    for r in rows:
        v = r.get("tick"); tk.add(f"dict:{v.get('state')}" if isinstance(v, dict) else v)
    print(f"  tick 值域={tk}")
    # hwnd/singleton 值域转换点
    def seq(key):
        o = []
        for i, r in enumerate(rows):
            v = r.get(key); k = f"dict:{v.get('state')}" if isinstance(v, dict) else v
            if not o or o[-1][0] != k: o.append([k, i, r["t"]])
        return o
    print(f"  hwnd 变化序列={seq('hwnd')}")
    print(f"  singleton 变化序列={seq('singleton')}")
    print(f"  hold_tl 尾行(关窗前) t={tl['hold_tl'][-1]['t']} exitstate={tl['hold_tl'][-1]['exitstate']} hwnd={tl['hold_tl'][-1]['hwnd']}")

print("\n##### 缝内实测点 / 边界重算（close∈?）")
cs = {t: J(t, "_rec.json")["closed_at_s"] for t in TRIPS}
la = {t: J(t, "_rec.json")["latch_detected"] for t in TRIPS}
for t in TRIPS: print(f"  {t}: closed_at_s={cs[t]} latch={la[t]}")
lo = max(cs[t] for t in ("hold13", "hold14"))
hi = min(cs[t] for t in TRIPS if not la[t]) if any(not la[t] for t in TRIPS) else None
print(f"  同侧最大闩 close={lo} 同侧最小不闩 close={hi} => 边界 (close ∈ ({lo}, {hi}] 仅在 n=1/点 假设下成立)")
print("\n##### hold15 闩盲区量化：采样节律 vs 若发生闩的可检测性")
rec15, tl15 = J("hold15", "_rec.json"), J("hold15", "timeline.json")
r15 = tl15["close_rows"]
d15 = [round(r15[i+1]["t"]-r15[i]["t"], 4) for i in range(len(r15)-1)]
print(f"  采样间隔 max={max(d15)} => 若闩只存在 <max_dt 的瞬态则可能漏；但 exitstate 是内存值(非脉冲)，持续态不漏")
print(f"  观察窗绝对=[{round(r15[0]['t']-(rec15['close_delivery']['t']-rec15['closed_at_s']),3)}, "
      f"{round(r15[-1]['t']-(rec15['close_delivery']['t']-rec15['closed_at_s']),3)}] 覆盖 hold13/14 闩绝对时刻 21.867/22.029?")
for t in ("hold13", "hold14"):
    rr = J(t, "_rec.json"); tt = J(t, "timeline.json"); li = rr["latch_row_index"]
    t0 = rr["close_delivery"]["t"] - rr["closed_at_s"]
    ab = round(tt["close_rows"][li]["t"] - t0, 3)
    print(f"    {t} 闩绝对={ab} 在 hold15 窗内? {'YES' if 16.272 <= ab <= 136.213 else 'NO'}")
