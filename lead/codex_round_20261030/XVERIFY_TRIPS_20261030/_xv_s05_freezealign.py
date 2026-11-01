#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s05：核 (11) 冻结起点 vs units 停变点时间对齐，
   判定台账「W1/W2 帧冻结 = 关卡终局，非战斗卡顿」是否成立，
   并检查有无战斗期内冻结被误归终局。
"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
T = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"


def freeze_runs(t, f, thr=0.5):
    segs, i, n = [], 0, len(t)
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        if t[j] - t[i] >= thr:
            segs.append((f[i], round(t[i] - t[0], 3), round(t[j] - t[0], 3), round(t[j] - t[i], 3)))
        i = j + 1
    return segs


for d in ("l3_20261023q", "l3_20261023r"):
    print("=" * 74)
    print("###", d)
    for w in ("w0", "w1", "w2"):
        m = f"{T}\\{d}\\measure_{w}.json"
        x = json.load(open(m, encoding="utf-8"))
        t, f = x["samples"]["t"], x["samples"]["f"]
        cs = x.get("counters") or []
        u = [c["units"] for c in cs]
        tt = [c["t_rel"] for c in cs]
        b = [c.get("b") for c in cs]
        segs = freeze_runs(t, f)
        lastchg = None
        for i in range(1, len(u)):
            if u[i] != u[i - 1]:
                lastchg = i
        flatstart = None
        for i in range(1, len(u)):
            if all(u[k] == u[i] for k in range(i, len(u))):
                flatstart = i
                break
        print(f"  -- window {w}: t_abs0={x.get('t_abs0')} span={round(t[-1]-t[0],3)}s frame {f[0]}->{f[-1]} "
              f"冻结区段(>=0.5s) 数={len(segs)} 明细={segs}")
        lc_t = (round(tt[lastchg], 3) if lastchg is not None else None)
        fs_t = (round(tt[flatstart], 3) if flatstart is not None else None)
        print(f"     units first={u[0]} last={u[-1]} 最后变化步 idx={lastchg}(t_rel={lc_t}) "
              f"全程持平起点 idx={flatstart}(t_rel={fs_t}, 值={u[flatstart] if flatstart is not None else None})")
        zidx = [i for i, v in enumerate(b) if v == 0]
        print(f"     对方 b first={b[0]} last={b[-1]} 首次归零 idx={zidx[0] if zidx else None}"
              f"(t_rel={round(tt[zidx[0]],3) if zidx else None})")
        if segs:
            fz0 = segs[0][1]
            pre = [i for i in range(1, len(u)) if tt[i] < fz0 and u[i] != u[i - 1]]
            print(f"     冻结起点窗内 t_rel={fz0} ; 冻结起点前 units 仍在变化的步数={len(pre)} idx={pre[-8:] if pre else []}")
            if flatstart is not None:
                print(f"     冻结起点 - units停变点 = {round(fz0 - tt[flatstart], 3)} s (正=冻结晚于停变)")
