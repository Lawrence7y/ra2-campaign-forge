#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s16：固化最后三处内联验证，使判定书每个断言都有可复跑脚本留档。
 (1) 四趟的 hold_override / e2_params.hold_after_window_s / protocol / boot 键态 ⇒ 驱动指纹适用边界
 (2) 三副本 protocol 串的写法（A/C 恒拼常量，B 拼 normalize_hold_s）
 (3) 五趟 31 档战斗趟 W0 帧时表（支撑 §7「同量级」与 e4 不可引申）
"""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"
T = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

print("### (1) 键态（驱动排他指纹的适用范围）")
for tag, d in (("1029T2228", "20261029T222811_9001_P3e_E12_T1"), ("1029T2316", "20261029T231621_9001_P3e_E12_T1"),
              ("E5h10", "20261030T072242_9001_P3e_E12_T1"), ("hold13", "20261030T211741_9001_P3e_E12_T1"),
              ("hold14", "20261030T212148_9001_P3e_E12_T1"), ("hold15", "20261030T212233_9001_P3e_E12_T1")):
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    print(f"  {tag:9s} hold_override={r.get('hold_override', 'KEY_ABSENT')} "
          f"e2.hold_after_window_s={r['e2_params'].get('hold_after_window_s', 'KEY_ABSENT')} "
          f"protocol={r['protocol']!r} boot={r.get('boot_wallclock_ms_at_start')} "
          f"closed={r['closed_at_s']} latch={r.get('latch_detected')}")

print("\n### (2) 三副本 protocol 串写法")
for nm, p in (("A root", "lead/qc161_u0400_trip/_drive_c2_x_e12.py"),
              ("B e5candidate", "lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_e12.py"),
              ("C fix20261029", "lead/qc161_u0400_trip/codex_e12_fix_20261029/candidate/_drive_c2_x_e12.py")):
    s = open(p, encoding="utf-8").read().splitlines()
    for i, ln in enumerate(s, 1):
        if '"protocol"' in ln and "early-close" in ln:
            print(f"  {nm}: :{i} {ln.strip()[:110]}")
    if "normalize_hold_s(hold_after_window_s)[0]" in "\n".join(s):
        print(f"  {nm}: 使用 normalize_hold_s 拼 protocol ⇒ 可产 window+13/14/15")
    else:
        print(f"  {nm}: 无 normalize_hold_s ⇒ protocol 恒 window+6.0")

print("\n### (3) 31 档战斗趟 W0 帧时表（原始 stats + 自算变化步）")
for d in ("l1a_20261020", "t55k_20261020", "l1_20261023e4", "l3_20261023q", "l3_20261023r"):
    m = json.load(open(f"{T}/{d}/measure_w0.json", encoding="utf-8"))
    st, g = m["stats"], m["gate"]
    u = [c["units"] for c in m["counters"]]
    ch = sum(1 for i in range(1, len(u)) if u[i] != u[i - 1])
    inc = [i for i in range(1, len(u)) if u[i] >= u[i - 1]]
    print(f"  {d:16s} units0={g['units0']} pre={g['pre_fps15']} p50={st['frame_ms_p50']:.2f} p90={st['frame_ms_p90']:.2f} "
          f"p99={st['frame_ms_p99']:.2f} max={st['frame_ms_max']:.2f} fps={st['fps_avg']:.3f} max_stall={st['max_stall_s']} "
          f"| W0内≥0.5s停顿=0? max_stall<0.5 -> {st['max_stall_s'] < 0.5}")
    print(f"       units {u[0]}->{u[-1]} dU={u[-1]-u[0]} 变化步={ch}/{len(u)-1} 非严格降的步 idx={inc}")
