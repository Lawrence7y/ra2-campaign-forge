#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 同族标注版（GLM）亲验探针 v1：核心读数全部从原始件直读重算。
覆盖：②2C 趟 / ①ha+hb / q/r 基线 / frame 起点语义（l1k units>0 首样）/ 发射 tee 预检行。
只读。跑法：python -I -X utf8 _b2g_v1_core.py（repo 根目录）。
"""
import json, io, sys, os, math
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
C2C = "lead/qc161_u0400_trip/c2ab_x/20261031T154139_9001_P3e_E12_T1"
HA  = f"{ROOT}/l3_20261031ha"
HB  = f"{ROOT}/l3_20261031hb"
QR  = f"{ROOT}"
Q   = f"{ROOT}/l3_20261023q"
R   = f"{ROOT}/l3_20261023r"

def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

print("=" * 78)
print("(A) ②批 2C 趟 154139 原始件直读")
print("=" * 78)
rec = jload(f"{C2C}/_rec.json")
tl  = jload(f"{C2C}/timeline.json")
rows, ht = tl["close_rows"], tl["hold_tl"]
t0 = rows[0]["t"]
print(f"  closed_at_s={rec['closed_at_s']}  latch_detected={rec['latch_detected']}  "
      f"exit_kind={rec['exit_kind']}  final_exitcode={rec['final_exitcode']}  verdict={rec['verdict']}")
print(f"  exited={rec['exited']}  a8_verdict={rec['a8_verdict']}  carrier_deleted={rec['carrier_deleted']}  "
      f"stop_triggered={rec.get('stop_triggered')}  except_changed={rec['except_changed']}  hold_tl_n={rec['hold_tl_n']}")
print(f"  killed_on_cleanup 键在? {'killed_on_cleanup' in rec}   (§485 写 None)")
hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
sg = [i for i, x in enumerate(rows) if x.get("singleton") == 0]
ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
dicts = [i for i, x in enumerate(rows) if isinstance(x.get("exitstate"), dict)]
nums = [i for i, x in enumerate(rows) if isinstance(x.get("exitstate"), int)]
zeros = [i for i, x in enumerate(rows) if x.get("exitstate") == 0]
print(f"  Δ = rows[{hz[0]}].t-rows[0].t = {round(rows[hz[0]]['t']-t0,3)}  "
      f"singleton 首归零 idx={sg[0]} 同行={sg[0]==hz[0]}")
print(f"  exitstate 形态 = 0×{len(zeros)} → 1×{len(ones)}{ones} + DICT×{len(dicts)}{dicts}  "
      f"DICT 值={rows[dicts[0]]['exitstate'] if dicts else None}")
lt, le_last, le_num = rows[ones[0]]["t"], rows[-1]["t"], rows[nums[-1]]["t"]
print(f"  闩沿 idx={ones[0]} t-rel={round(lt-t0,3)}  数值末 idx={nums[-1]} t-rel={round(le_num-t0,3)}  "
      f"末行(含DICT) t-rel={round(le_last-t0,3)}")
print(f"  ★闩→退 末行口径 = {round(le_last-lt,3)}   数值末口径 = {round(le_num-lt,3)}")
hold = rec["e2_params"]["hold_after_window_s"]
t0b = rec["close_delivery"]["t"] - rec["closed_at_s"]
a = round(ht[0]["t"] - t0b, 3)
post = round(rec["closed_at_s"] - a - math.ceil(hold), 3)
print(f"  hold={hold} ceil={math.ceil(hold)} n读={len(ht)}  a={a}  post(closed-a-ceil)={post}  "
      f"a+post={round(a+post,3)}  ∈[0.996,1.289]={0.996<=a+post<=1.289}")
fr = Counter(str(x.get("frame")) for x in rows)
print(f"  rows frame 取值 = {dict(fr)}  (菜单恒 0 ⇒ frame 不在菜单期累计)")

print("\n" + "=" * 78)
print("(B) ①批 ha/hb：C-1 武装 + 发射面")
print("=" * 78)
for tag, d in [("ha", HA), ("hb", HB)]:
    fld = jload(f"{d}/qc151_fields.json")
    def gv(grp, key):
        v = [e["value"] for e in fld if isinstance(e, dict) and e.get("group") == grp and e.get("key") == key]
        return v[-1] if v else None
    mfw = gv("MEASURE", "h7_frame_wait")
    m400 = gv("META", "h7_measure_start_frame")
    print(f"  [{tag}] META.h7_measure_start_frame={m400}  MEASURE.h7_frame_wait={json.dumps(mfw, ensure_ascii=False)}")
    lr = jload(f"{d}/_launch_result.json")
    keys = {k: lr.get(k) for k in ("rc", "duration_s", "harness_sha16", "carrier_deleted") if k in lr}
    print(f"        _launch_result.json: {keys}  (全键={sorted(lr.keys())[:12]})")

print("\n" + "=" * 78)
print("(C) hb units0 两口径 + 窗首末")
print("=" * 78)
m0 = jload(f"{HB}/measure_w0.json")
print(f"  gate.units0={m0['gate'].get('units0')}  w0.verdict={m0.get('verdict')}")
print(f"  samples 键={sorted(m0['samples'].keys())}")
cnt = m0.get("counters") or []
if cnt:
    print(f"  counters n={len(cnt)} 首行={cnt[0]}  末行={cnt[-1]}")
m1 = jload(f"{HB}/measure_w1.json"); m2 = jload(f"{HB}/measure_w2.json")
print(f"  w1 counters 首末={[ (c.get('units')) for c in (m1.get('counters') or []) ][:1]}…"
      f"{[(c.get('units')) for c in (m1.get('counters') or [])][-1:]}  "
      f"w2 末={[(c.get('units')) for c in (m2.get('counters') or [])][-1:]}")

print("\n" + "=" * 78)
print("(D) q/r 基线：battle→w0 墙钟与隐含早相 fps（同一 perf_counter 轴）")
print("=" * 78)
for tag, d in [("q", Q), ("r", R)]:
    fld = jload(f"{d}/qc151_fields.json")
    def gv(grp, key):
        v = [e["value"] for e in fld if isinstance(e, dict) and e.get("group") == grp and e.get("key") == key]
        return v[-1] if v else None
    net = gv("NAV", "h7_nav_end_t")
    fw = gv("MEASURE", "h7_frame_wait")
    m400 = gv("META", "h7_measure_start_frame")
    mw = jload(f"{d}/measure_w0.json")
    f0, tt0 = mw["samples"]["f"][0], mw["samples"]["t"][0]
    W = round(tt0 - net, 3)
    print(f"  [{tag}] nav_end={net}  w0 t[0]={tt0}  W={W}s  f[0]={f0}  ⇒ 平均={round(f0/W,2)} fps")
    print(f"        META.h7_measure_start_frame={m400}（H7 未武装应为 None）  MEASURE.h7_frame_wait={'在' if fw else '无'}")
    print(f"        stage_seconds:frame={gv('BUDGET','stage_seconds:frame')}  settle={gv('MEASURE','settle_seconds')}")
    cnt = mw.get("counters") or []
    print(f"        w0 counters 首行 units={cnt[0].get('units') if cnt else None}  "
          f"samples units 首={mw['samples'].get('units',[None])[0] if isinstance(mw['samples'].get('units'),list) else '<无 units 列>'}")

print("\n" + "=" * 78)
print("(E) frame 起点语义决定性检验：units>0 首样的 frame 值")
print("=" * 78)
for d in ["l1_20261023k", "l1_20261023e1", "l1_20261023hb"]:
    try:
        mw = jload(f"{QR}/{d}/measure_w0.json")
    except Exception as e:
        print(f"  {d}: 读取失败 {e!r}"); continue
    s = mw.get("samples") or {}
    fl, ul = s.get("f"), s.get("units")
    if not fl or ul is None:
        print(f"  {d}: samples.f/units 缺（f={bool(fl)}, units 列={isinstance(ul,list)}）"); continue
    first = next((i for i, u in enumerate(ul) if isinstance(u, (int, float)) and u > 0), None)
    print(f"  {d}: units 序列={ul[:6]}…  units>0 首样 idx={first}  该样 f={fl[first] if first is not None else None}  "
          f"f 全程=[{fl[0]}..{fl[-1]}]")

print("\n" + "=" * 78)
print("(F) 发射 tee 预检行（A11/A8）")
print("=" * 78)
for t in ("launcher_h8_t1_20261031.txt", "launcher_h8_t2_20261031.txt"):
    p = f"lead/codex_round_20261030/LEADER_battle/{t}"
    if not os.path.isfile(p):
        print(f"  {t}: 缺件"); continue
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
    hits = [(i, ln) for i, ln in enumerate(lines) if ("A11" in ln or "A8" in ln or "A1 " in ln or "A2 " in ln)]
    print(f"  --- {t}（{len(lines)} 行）预检命中 {len(hits)} 行 ---")
    for i, ln in hits[:14]:
        print(f"     {i}: {ln[:150]}")
