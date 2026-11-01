#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p01：②批 2C 趟（20261031T154139，hold=14.0）§485 主张逐字段独立重算。

口径：
 - Δ = 首个 hwnd==0 行 t − close_rows[0].t（本 ask 指定自实现，同 _xv481_q01 口径）；
 - 闩→退 = close_rows 原始时间戳相减（§477 R-1 纪律）：闩沿 = 首个 exitstate==1 行的 t，
   退沿 = 末个「数值形态行」（非 DICT 尾行）的 t；两条并列打印以显式暴露 DICT 尾行影响；
 - 闩/不闩族归属由盘上原始行 exitstate==1 计数判定，不采信 _rec.latch_detected 单一字段；
 - exitstate 值分布逐位统计（0×n / 1×m / dict 尾行）；
 - 量化律 closed = a + ceil(hold) + post，a = hold_tl[0].t − t0（t0 反推 = close_delivery.t −
   closed_at_s，Y-481-D 锚=popen t0）、post = t_close − hold_tl[-1].t 的余量分解。
只读，不改任何产物。
"""
import json, io, sys, os, math, hashlib
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

T = "lead/qc161_u0400_trip/c2ab_x/20261031T154139_9001_P3e_E12_T1"
rec = json.load(open(f"{T}/_rec.json", encoding="utf-8"))
tl = json.load(open(f"{T}/timeline.json", encoding="utf-8"))
hold_tl, rows = tl["hold_tl"], tl["close_rows"]

print("=" * 78)
print("(0) 件哈希 / 规模")
print("=" * 78)
for f in ["_rec.json", "timeline.json", "ra2render_close_last.log", "ra2render_after_kill.log"]:
    p = f"{T}/{f}"
    b = open(p, "rb").read()
    print(f"  {f:32s} bytes={len(b):7d} sha256={hashlib.sha256(b).hexdigest()[:16]}")
print(f"  hold_tl n={len(hold_tl)}  close_rows n={len(rows)}  rec.close_rows_n={rec['close_rows_n']}")

print("\n" + "=" * 78)
print("(1) §485 主张字段逐项 vs 原始件")
print("=" * 78)
claims = [
    ("verdict", rec.get("verdict"), "OK"),
    ("exited", rec.get("exited"), True),
    ("exit_kind", rec.get("exit_kind"), "natural"),
    ("final_exitcode", rec.get("final_exitcode"), 0),
    ("closed_at_s", rec.get("closed_at_s"), 15.194),
    ("latch_detected", rec.get("latch_detected"), True),
    ("hold_tl_n", rec.get("hold_tl_n"), 14),
    ("a8_verdict", rec.get("a8_verdict"), "PASS"),
    ("a8_remaining", rec.get("a8_remaining"), []),
    ("carrier_deleted", rec.get("carrier_deleted"), True),
    ("stop_triggered", rec.get("stop_triggered"), None),
    ("except_changed", rec.get("except_changed"), False),
    ("exit_after_close_s(_rec)", rec.get("exit_after_close_s"), 7.53),
    ("latch_after_close_s(_rec)", rec.get("latch_after_close_s"), 5.526),
    ("latch_row_index(_rec)", rec.get("latch_row_index"), 55),
    ("close_rows_n(_rec)", rec.get("close_rows_n"), 58),
]
for name, got, want in claims:
    print(f"  {name:28s} got={got!r:22s} claim={want!r:22s} {'MATCH' if got == want else '**DIFF**'}")

print("\n  killed_on_cleanup 键存在? ", "killed_on_cleanup" in rec,
      "值=", rec.get("killed_on_cleanup", "<键不存在>"))
print("  _rec 全部键数 =", len(rec))

print("\n" + "=" * 78)
print("(2) Δ 轴（自实现：首个 hwnd==0 行 t − rows[0].t）")
print("=" * 78)
t0 = rows[0]["t"]
hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
sg = [i for i, x in enumerate(rows) if x.get("singleton") == 0]
d = round(rows[hz[0]]["t"] - t0, 3) if hz else None
print(f"  rows[0].t={t0}  首个 hwnd==0 idx={hz[0]} t={rows[hz[0]]['t']}  Δ={d}  (§485 主张 0.101)")
print(f"  首个 singleton==0 idx={sg[0]}  与 hwnd 同行? {sg[0] == hz[0]}  (idx=1 主张)")
print(f"  close_delivery.t={rec['close_delivery']['t']}  与 rows[0].t 差={round(rec['close_delivery']['t']-t0,4)}")
print(f"  反推 t0 = close_delivery.t − closed_at_s = {round(rec['close_delivery']['t']-rec['closed_at_s'],3)}")
# 持续性
cont = [i for i in range(hz[0], len(rows)) if rows[i].get("hwnd") == 0]
print(f"  hwnd==0 连续行数（自归零起，数值行）= {len(cont)} / 总 {len(rows)}；回弹次数 = "
      f"{sum(1 for i in range(hz[0]+1, len(rows)) if isinstance(rows[i].get('hwnd'), int) and rows[i]['hwnd'] != 0)}")

print("\n" + "=" * 78)
print("(3) 闩→退（R-1：close_rows 原始时间戳，闩沿=首个 exitstate==1 行）")
print("=" * 78)
ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
dict_rows = [i for i, x in enumerate(rows) if isinstance(x.get("exitstate"), dict)]
numeric = [i for i, x in enumerate(rows) if isinstance(x.get("exitstate"), int)]
print(f"  exitstate==1 行 idx={ones}  (n={len(ones)})")
print(f"  DICT 尾行 idx={dict_rows}  值={rows[dict_rows[0]]['exitstate'] if dict_rows else None}")
print(f"  闩沿 t={rows[ones[0]]['t']}  (idx={ones[0]}, t−closed_delivery={round(rows[ones[0]]['t']-rec['close_delivery']['t'],3)})")
last_num = rows[numeric[-1]]
print(f"  末个数值行 idx={numeric[-1]} t={last_num['t']}  t−close_delivery={round(last_num['t']-rec['close_delivery']['t'],3)}")
print(f"  ★闩→退（数值行末 − 闩沿）= {round(last_num['t'] - rows[ones[0]]['t'], 3)} s   (§485 主张 2.003)")
print(f"  （对照：用 DICT 尾行作退沿 = {round(rows[dict_rows[0]]['t'] - rows[ones[0]]['t'], 3) if dict_rows else None}）")
zeros = [i for i, x in enumerate(rows) if x.get("exitstate") == 0]
print(f"  exitstate 值分布 = {Counter(type(rows[i]['exitstate']).__name__ + ':' + (json.dumps(rows[i]['exitstate']) if isinstance(rows[i]['exitstate'], dict) else str(rows[i]['exitstate'])) for i in range(len(rows)))}")
print(f"  形态检查：0×{len(zeros)} → 1×{len(ones)} + DICT尾行×{len(dict_rows)}；0..54 连续? "
      f"{zeros == list(range(0,55))}")

print("\n" + "=" * 78)
print("(4) hold_tl 与量化律")
print("=" * 78)
t0b = rec["close_delivery"]["t"] - rec["closed_at_s"]
a = round(hold_tl[0]["t"] - t0b, 3)
post = round(rec["close_delivery"]["t"] - hold_tl[-1]["t"], 3)
hold = rec["e2_params"]["hold_after_window_s"]
ceilh = math.ceil(hold)
print(f"  hold={hold}  ceil(hold)={ceilh}  hold_tl_n={len(hold_tl)} == ceil? {len(hold_tl)==ceilh}")
print(f"  a = hold_tl[0].t − t0(反推) = {a}   (主张带 [0.623,0.645])")
print(f"  post = close_delivery.t − hold_tl[-1].t = {post}   (主张带 [0.373,0.644])")
print(f"  a + ceil + post = {round(a+ceilh+post,3)}  vs closed_at_s={rec['closed_at_s']}  "
      f"差={round(rec['closed_at_s']-(a+ceilh+post),3)}")
print(f"  a+post = {round(a+post,3)}  (主张 1.194)  ∈ [0.996,1.289]? {0.996 <= a+post <= 1.289}")
print(f"  hold_tl 相邻间隔: min={round(min(b['t']-a_['t'] for a_,b in zip(hold_tl,hold_tl[1:])),3) if len(hold_tl)>1 else None} "
      f"max={round(max(b['t']-a_['t'] for a_,b in zip(hold_tl,hold_tl[1:])),3) if len(hold_tl)>1 else None}")
print(f"  hold 窗实际跨度 = {round(hold_tl[-1]['t']-hold_tl[0]['t'],3)} (期望 <{hold})")
print(f"  hold_tl 各帧 frame/tick 恒? frame={set(r['frame'] for r in hold_tl)} tick={set(r['tick'] for r in hold_tl)}")
print(f"  hold_tl hwnd 全非零? {all(r['hwnd'] for r in hold_tl)}  singleton 全非零? {all(r['singleton'] for r in hold_tl)}")

print("\n" + "=" * 78)
print("(5) 采样节律 / wait 码 / 帧-时间")
print("=" * 78)
iv = [round(rows[i+1]["t"]-rows[i]["t"], 3) for i in range(len(rows)-1)]
print(f"  close_rows 间隔 前 55 行样本: {sorted(set(iv[:54]))}")
print(f"  idx54→55 间隔={iv[54]} idx55→56={iv[55]} idx56→57={iv[56]} (1Hz 慢采样段)")
waits = Counter(r["wait"] for r in rows)
print(f"  wait 值分布 = {dict(waits)}")
print(f"  尾行 wait={rows[-1]['wait']} code={rows[-1]['code']} code_read_ok={rows[-1]['code_read_ok']}")
print(f"  frame 数值分布 = {Counter(str(r['frame']) for r in rows).most_common(4)}")
print(f"  tick 数值分布 = {Counter(str(r['tick']) for r in rows).most_common(4)}")

print("\n" + "=" * 78)
print("(6) except / 守卫日志 / 载体 / boot")
print("=" * 78)
ex = {rec.get("except_before"), rec.get("except_at", {}).get("close_last"), rec.get("except_at", {}).get("after_kill")}
print(f"  except sha16 三读 = {ex}  恒? {len(ex)==1}")
for f in ["ra2render_close_last.log", "ra2render_after_kill.log"]:
    b = open(f"{T}/{f}", "rb").read().decode("utf-8", "replace")
    print(f"  --- {f} ({len(b)} chars) ---")
    for ln in b.splitlines():
        print("     |", ln)
print(f"  shots: {[(s['tag'], s['t']) for s in rec['shots']]}")
for s in rec['shots']:
    _pth = os.path.join(T, "shots", s['tag'] + ".png")
    print(f"    shot {s['tag']}: path_exists={os.path.isfile(_pth)} size={os.path.getsize(_pth) if os.path.isfile(_pth) else None}")
print(f"  boot_ms_at_start={rec['boot_ms_at_start']} wallclock={rec['wallclock_ms_at_start']} "
      f"boot_wallclock={rec['boot_wallclock_ms_at_start']} 自洽(wall−boot==bootwall)? "
      f"{rec['wallclock_ms_at_start'] - rec['boot_ms_at_start'] == rec['boot_wallclock_ms_at_start']}")
print(f"  loader_pid={rec['loader_pid']} gamemd_pid={rec['gamemd_pid']} hwnd={rec['hwnd']} "
      f"window_tid={rec['window_tid']} close_delivery.target_hwnd={rec['close_delivery']['target_hwnd']} "
      f"win_pid={rec['close_delivery']['win_pid']}")
print(f"  e2 慢采样 n={len(rec['slow_sample_rows'])} pair_close_row_index="
      f"{[r['pair_close_row_index'] for r in rec['slow_sample_rows']]}")
print(f"  hook6_state_counts={rec['hook6_state_counts']} → hook6_state={rec['hook6_state']}")
print(f"  cpu_delta_median_s={rec['cpu_delta_median_s']} ws_delta_kb={rec['ws_delta_kb']} "
      f"fork_label={rec['e2_fork_label']}")
print(f"  hold_override={rec['hold_override']}")
print(f"  载体目录存在? {os.path.isdir(f'{T}/ct')}  out_dir={rec['out_dir']}")

print("\n" + "=" * 78)
print("(7) 闩边界收窄口径复算：(14.997,16.272] ⇒ (15.194,16.272]")
print("=" * 78)
print(f"  本趟 closed_at_s={rec['closed_at_s']} ∈ 预测带 [14.996,15.289]? "
      f"{14.996 <= rec['closed_at_s'] <= 15.289}")
print(f"  本趟闩 + closed={rec['closed_at_s']} ⇒ 已知闩点 max=closed（下界上移 = 该值，开区间）")
print(f"  收窄前下界 14.997（=212148 趟 closed）→ 新下界 {rec['closed_at_s']}：上移 "
      f"{round(rec['closed_at_s']-14.997,3)} s（§485 主张 0.197）")
