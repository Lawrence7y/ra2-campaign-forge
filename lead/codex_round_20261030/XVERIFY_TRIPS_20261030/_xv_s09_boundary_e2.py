#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s09：(a) 闩边界上界跨会话合并收紧检查；(b) E2 各轴是否跨越进程退出时刻；
   (c) 菜单退化轴（frame/tick 恒值）确认；(d) 汇总逐字段对照表所需数值。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
BATCH = {"本批 hold13": "20261030T211741_9001_P3e_E12_T1",
         "本批 hold14": "20261030T212148_9001_P3e_E12_T1",
         "本批 hold15": "20261030T212233_9001_P3e_E12_T1",
         "E5 hold10": "20261030T072242_9001_P3e_E12_T1",
         "E5 hold15": "20261030T072353_9001_P3e_E12_T1",
         "E5 hold20": "20261030T072630_9001_P3e_E12_T1"}

rows_all = {}
print("### (a) 边界点总表（close 实测值 / latch / 闩绝对 / hwnd 归零绝对 / 会话 boot 墙钟）")
for k, d in BATCH.items():
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    li = r.get("latch_row_index")
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
    rows_all[k] = dict(closed=r["closed_at_s"], latch=r["latch_detected"], sess=str(r["boot_wallclock_ms_at_start"])[:11])
    print(f"  {k}: close={r['closed_at_s']} latch={r['latch_detected']} 闩绝对="
          f"{(round(rows[li]['t']-t0,3) if li is not None else None)} hwnd归零绝对="
          f"{(round(rows[hz[0]]['t']-t0,3) if hz else None)} 会话boot={r['boot_wallclock_ms_at_start']}"
          f"({'本会话' if str(r['boot_wallclock_ms_at_start']).startswith('1793337038') else '另一会话'})")

latched = [(k, v["closed"]) for k, v in rows_all.items() if v["latch"]]
unlatched = [(k, v["closed"]) for k, v in rows_all.items() if not v["latch"]]
same_sess_lat = [c for k, c in latched if rows_all[k]["sess"] == "179333703811"] + [c for k, c in latched if k.startswith("本批")]
sl = max(c for k, c in latched if k.startswith("本批"))
uh_same = min(c for k, c in unlatched if k.startswith("本批"))
uh_all = min(c for k, c in unlatched)
print(f"\n  闩侧最大 close（本批）={sl}")
print(f"  不闩侧最小 close：本会话={uh_same}  合并全部会话={uh_all}")
print(f"  ⇒ 台账『同会话』边界=({sl}, {uh_same}] ；若合并跨会话可比点 ⇒ 上界收到 ({sl}, {uh_all}]")
print(f"  ⇒ 台账称『较 E5 (11.19,16.09] 显著窄』：宽度 E5={round(16.091-11.193,3)}s 本批={round(uh_same-sl,3)}s "
      f"合并建议={round(uh_all-sl,3)}s")

print("\n### (b) E2 轴是否跨越进程退出时刻（hold13/14）")
for k in ("本批 hold13", "本批 hold14"):
    r = json.load(open(f"{CB}/{BATCH[k]}/_rec.json", encoding="utf-8"))
    tl = json.load(open(f"{CB}/{BATCH[k]}/timeline.json", encoding="utf-8"))
    rows = tl["close_rows"]
    tex = rows[-1]["t"]  # 进程已退出（wait==0）时刻
    latch_t = rows[r["latch_row_index"]]["t"]
    print(f"  {k}: 闩 t={latch_t} 退出 t={tex}")
    for i, s in enumerate(tl["_e2"]["slow_sample_rows"]):
        paired = rows[s["pair_close_row_index"]]
        cross = "跨退出(paired wait==0)" if paired["wait"] == 0 else "退出前"
        ws = s.get("ws_kb")
        print(f"    slow[{i}] t={s['t']} [{cross}] hook6={s['hook6']['state']} ws_kb={ws} "
              f"cpu_delta={ (s.get('cpu') or {}).get('delta_s') } 区间宽度={round(s['t']-(tl['_e2']['slow_sample_rows'][i-1]['t'] if i else latch_t),4)}s")
    ds = [ (s.get("cpu") or {}).get("delta_s") for s in tl["_e2"]["slow_sample_rows"]]
    print(f"    cpu deltas={ds} rec.cpu_delta_median_s={r['cpu_delta_median_s']} 自算median={round(sum(sorted(ds)[len(ds)//2-1:(len(ds)//2+1)]) / 2, 4) if len(ds)==2 else sorted(ds)[len(ds)//2]}")
    print(f"    ⇒ SPIN_MIN_DELTA=0.7（_drive_c2_x_e12.py:103）；其中跨退出的 delta 数={sum(1 for i,s in enumerate(tl['_e2']['slow_sample_rows']) if rows[s['pair_close_row_index']]['wait']==0)}")
    print(f"    ws_delta_kb={r['ws_delta_kb']} 自算={ws - tl['_e2']['slow_sample_rows'][0]['ws_kb']}")

print("\n### (c) 菜单退化轴（close_rows 的 frame/tick 是否恒值）")
for k, d in BATCH.items():
    tl = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))
    rows = tl["close_rows"]
    fr = set((x["frame"] if not isinstance(x.get("frame"), dict) else "dict") for x in rows)
    tk = set((x["tick"] if not isinstance(x.get("tick"), dict) else "dict") for x in rows)
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    print(f"  {k}: frame值域={fr} tick值域={tk} mode={r['mode']} protocol={r['protocol']!r}")

print("\n### (d) 逐字段对照表所需（_rec 值 vs 原始时间戳实算）")
for k in ("本批 hold13", "本批 hold14", "本批 hold15"):
    r = json.load(open(f"{CB}/{BATCH[k]}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{BATCH[k]}/timeline.json", encoding="utf-8"))["close_rows"]
    li = r.get("latch_row_index")
    print(f"  {k}: closed(rec)={r['closed_at_s']} vs raw={round(rows[0]['t']-(r['close_delivery']['t']-r['closed_at_s']),3)}"
          f" | latch_after(rec)={r.get('latch_after_close_s')} vs raw={round(rows[li]['t']-rows[0]['t'],4) if li is not None else None}"
          f" | exit_after(rec)={r.get('exit_after_close_s')} vs raw={round(rows[-1]['t']-rows[0]['t'],4)}"
          f" | 闩→退(rec相减)={(round(r['exit_after_close_s']-r['latch_after_close_s'],4) if li is not None and r.get('exit_after_close_s') else None)}"
          f" vs raw={round(rows[-1]['t']-rows[li]['t'],4) if li is not None else None}")
