#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p01：本批 2 趟 _rec/timeline 全字段亲算核验。
   口径来源：台账 §477（R-1：闩→退用 timeline.close_rows 原始时间戳相减）、§481；
   Δ 算法参考上轮 lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s11_delaydisc.py:27-34，
   本件为**独立重写实现**（Δ = rows[hz0].t − rows[0].t，不用 close_delivery 反推 t0）。
   只读；输出落 _raw/p01_stdout.txt。
"""
import json, io, sys, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CB = "lead/qc161_u0400_trip/c2ab_x"
D = ["20261031T083340_9001_P3e_E12_T1", "20261031T083611_9001_P3e_E12_T1"]

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

for d in D:
    base = f"{CB}/{d}"
    r = json.load(open(f"{base}/_rec.json", encoding="utf-8"))
    tl = json.load(open(f"{base}/timeline.json", encoding="utf-8"))
    rows = tl["close_rows"]
    print("=" * 100)
    print(f"[趟] {d}")
    print(f"  sha256(_rec.json)      = {sha(base + '/_rec.json')}")
    print(f"  sha256(timeline.json)  = {sha(base + '/timeline.json')}")
    print(f"  bytes: rec={os.path.getsize(base+'/_rec.json')} tl={os.path.getsize(base+'/timeline.json')}")
    # ---- 主张字段
    hold = r["e2_params"]["hold_after_window_s"]
    print(f"  protocol              = {r['protocol']}")
    print(f"  hold_after_window_s   = {hold}  hold_override={r['hold_override']}")
    print(f"  closed_at_s           = {r['closed_at_s']}")
    print(f"  latch_detected        = {r['latch_detected']}  latch_row_index={r['latch_row_index']} "
          f"latch_after_close_s={r['latch_after_close_s']}")
    print(f"  close_rows_n(rec)     = {r['close_rows_n']}   len(rows)={len(rows)}  match={r['close_rows_n']==len(rows)}")
    es = sorted({x.get("exitstate") for x in rows})
    print(f"  exitstate 值域        = {es}   n(==1)={sum(1 for x in rows if x.get('exitstate')==1)}")
    wv = sorted({x.get("wait") for x in rows})
    print(f"  wait 值域             = {wv}   恒258={wv == [258]}")
    print(f"  a8_verdict={r['a8_verdict']} a8_enum_ok={r['a8_enum_ok']} a8_remaining={r['a8_remaining']}")
    print(f"  carrier_deleted={r['carrier_deleted']} carrier_retained={r['carrier_retained']}")
    print(f"  except_changed={r['except_changed']}  except_before={r['except_before']} "
          f"except_at={r['except_at']}")
    print(f"  exited={r['exited']} exit_kind={r['exit_kind']} exit_after_close_s={r['exit_after_close_s']} "
          f"final_exitcode={r['final_exitcode']} stop_triggered={r['stop_triggered']}")
    print(f"  loader_pid={r['loader_pid']} gamemd_pid={r['gamemd_pid']} hwnd={r['hwnd']} window_tid={r['window_tid']}")
    print(f"  killed_on_cleanup     = {r['killed_on_cleanup']}")
    pairs = {tuple(x) for x in r["killed_on_cleanup"]}
    expect = {(r["loader_pid"], "rc4_loader.exe"), (r["gamemd_pid"], "gamemd.exe")}
    print(f"    killed ⊇ (loader_pid,gamemd_pid) 逐位?  {pairs == expect}   顺序 loader 先? "
          f"{[x[0] for x in r['killed_on_cleanup']] == [r['loader_pid'], r['gamemd_pid']]}")
    print(f"  boot_ms_at_start={r['boot_ms_at_start']} wallclock_ms_at_start={r['wallclock_ms_at_start']} "
          f"boot_wallclock_ms_at_start={r['boot_wallclock_ms_at_start']}")
    print(f"    boot_wallclock == wallclock − boot ? {r['boot_wallclock_ms_at_start'] == r['wallclock_ms_at_start'] - r['boot_ms_at_start']}")
    print(f"  e2_fork_label={r['e2_fork_label']} hook6_state={r['hook6_state']} slow_rows_n={r['slow_rows_n']} "
          f"slow_sample_rows={len(r['slow_sample_rows'])}")
    print(f"  frozen_masters_sha256_at_import = {json.dumps(r['e2_params']['frozen_masters_sha256_at_import'])}")
    # ---- Δ 轴（独立实现）
    t0 = rows[0]["t"]
    hz = [i for i, x in enumerate(rows) if x.get("hwnd") == 0]
    sg = [i for i, x in enumerate(rows) if x.get("singleton") in (0, None)]
    sg0 = [i for i, x in enumerate(rows) if x.get("singleton") == 0]
    print(f"  rows[0].t={t0}  close_delivery.t={r['close_delivery']['t']}  相等={t0 == r['close_delivery']['t']}")
    if hz:
        i = hz[0]
        delta = round(rows[i]["t"] - t0, 3)
        absz = round(r["closed_at_s"] + delta, 3)
        print(f"  首个 hwnd==0 行 idx={i}  t={rows[i]['t']}")
        print(f"  Δ = rows[idx].t − rows[0].t = {rows[i]['t']} − {t0} = {delta} s")
        print(f"  hwnd 归零绝对时刻 = closed_at_s + Δ = {r['closed_at_s']} + {delta} = {absz} s")
        print(f"  Δ(反推 t0 口径) = rows[idx].t −(close_delivery.t − closed_at_s) = "
              f"{round(rows[i]['t'] - (r['close_delivery']['t'] - r['closed_at_s']), 3)}")
        sgi = sg0[0] if sg0 else None
        print(f"  singleton 归零首行 idx={sgi}  与 hwnd 同行={sgi == i if sgi is not None else 'singleton 从未==0'}")
        print(f"  该行 singleton={rows[i].get('singleton')}  hwnd同行字段={json.dumps(rows[i])}")
        prev = rows[i - 1]
        print(f"  前一行 idx={i-1}: t={prev['t']} hwnd={prev['hwnd']} singleton={prev['singleton']} "
              f"exitstate={prev['exitstate']} frame={prev['frame']} tick={prev['tick']}")
        print(f"  采样间隔 row[i-1]→row[i] = {round(rows[i]['t'] - prev['t'], 3)} s")
        ones = [i2 for i2, x in enumerate(rows) if x.get("exitstate") == 1]
        print(f"  exitstate==1 行数={len(ones)} → 闩族判据(有1)= {bool(ones)}")
    else:
        print("  无 hwnd==0 行 ⇒ Δ 不可算")
    # ---- 采样节律
    gaps = [round(rows[k]["t"] - rows[k - 1]["t"], 3) for k in range(1, len(rows))]
    gaps_sorted = sorted(gaps)
    print(f"  行间隔 median={gaps_sorted[len(gaps_sorted)//2]} max={max(gaps)} min={min(gaps)} "
          f">0.5s 空洞数={sum(1 for g in gaps if g > 0.5)}")
    print(f"  末行 t={rows[-1]['t']} 覆盖时长(自 rows[0]) = {round(rows[-1]['t'] - t0, 3)} s")
    # ---- 守卫日志逐字
    for lg in ("ra2render_close_last.log", "ra2render_after_kill.log"):
        p = f"{base}/{lg}"
        if os.path.isfile(p):
            txt = open(p, encoding="utf-8", errors="replace").read()
            print(f"  {lg}: sha16={hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]} bytes={os.path.getsize(p)}")
            print("    " + "\n    ".join(txt.splitlines()[:6]))
        else:
            print(f"  {lg}: 缺文件")
    print(f"  shots 目录: {os.listdir(base+'/shots') if os.path.isdir(base+'/shots') else '缺'}")
    for s in r["shots"]:
        print(f"    shot {s['tag']}: t={s['t']} exists={os.path.isfile(s['path'])}")
