#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s10：(i) ①段前提件（t55k/l1a/e4 31 档趟「长停顿全是终局冻结」+「同量级」）自算；
   (ii) 「(11.19,16.09] 缝内从未测点」的历史事实核查（扫全部 c2ab_x 趟的 closed_at_s）。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
T = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"


def freeze(t, f, thr=0.5):
    segs, i, n = [], 0, len(t)
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        if t[j] - t[i] >= thr:
            segs.append((f[i], round(t[i] - t[0], 3), round(t[j] - t[i], 3)))
        i = j + 1
    return segs


print("### (i) 既有 31 档战斗趟：W0 无冻结？W1/W2 冻结是否伴 units 停变（终局）")
for d in ("t55k_20261020", "l1a_20261020", "l1_20261023e4"):
    for w in ("w0", "w1", "w2"):
        p = f"{T}/{d}/measure_{w}.json"
        if not os.path.isfile(p):
            continue
        m = json.load(open(p, encoding="utf-8"))
        t, f = m["samples"]["t"], m["samples"]["f"]
        segs = freeze(t, f)
        cs = m.get("counters") or []
        u = [c["units"] for c in cs]
        tt = [c["t_rel"] for c in cs]
        flat = None
        for i in range(1, len(u)):
            if all(u[k] == u[i] for k in range(i, len(u))):
                flat = round(tt[i], 3)
                break
        st = m["stats"]
        print(f"  {d}/{w}: gate units0={m['gate']['units0']} pre={m['gate']['pre_fps15']} "
              f"frame {f[0]}->{f[-1]} 冻结={len(segs)} {segs[:3]} units {u[:1]}->{u[-1:]} 全程持平起点={flat} "
              f"p99={None if st.get('frame_ms_p99') is None else round(st['frame_ms_p99'],2)} "
              f"max={None if st.get('frame_ms_max') is None else round(st['frame_ms_max'],2)} "
              f"fps_avg={None if st.get('fps_avg') is None else round(st['fps_avg'],2)}")

print("\n### (ii) 历史 c2ab_x 趟：close∈(11.19,16.09) 缝内是否从未测点")
CB = "lead/qc161_u0400_trip/c2ab_x"
rows = []
for d in sorted(os.listdir(CB)):
    p = f"{CB}/{d}/_rec.json"
    if not os.path.isfile(p):
        continue
    r = json.load(open(p, encoding="utf-8"))
    if r.get("closed_at_s") is not None:
        rows.append((d, r["closed_at_s"], r.get("latch_detected"), r.get("boot_wallclock_ms_at_start"), r["mode"]))
print(f"  有 closed_at_s 的趟数={len(rows)}")
seam = [x for x in rows if 11.19 < x[1] < 16.09]
print(f"  落缝 (11.19,16.09) 内的趟（含本批）={seam}")
pre = [x for x in seam if not x[0].startswith("20261030T21")]
print(f"  本批之前落缝内的趟={pre}  => 台账『缝内从未测点』{'成立' if not pre else '不成立'}")
print("\n  全部趟 close/latch 一览：")
for d, c, l, b, md in rows:
    print(f"   {d}  close={c}  latch={l}  mode={md}  boot={str(b)[:13]}")
