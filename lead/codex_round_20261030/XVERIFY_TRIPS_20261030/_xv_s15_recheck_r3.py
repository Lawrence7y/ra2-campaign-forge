#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s15：用**正确判据**全量重验台账「既有 31 档战斗趟长停顿全是终局帧冻结」。
   错误判据（我先前所用，作废）：STALL_ANATOMY 的 chpts 是**整窗** units 变化点数，
   它 > 5 并不能说明冻结**期内** units 还在变。
   正确判据：对每条 stall>=0.5s 的长停顿，比较「冻结起点 t_rel」与「units 全程持平起点 t_rel」；
   冻结起点 >= 停变点 ⇒ 属终局（台账成立）；早于 ⇒ 才是反例。并检查 units 是否仍在降/对方是否归零。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SA = "lead/codex_round_20261030/LEADER_battle/STALL_ANATOMY_raw.json"

sa = json.load(open(SA, encoding="utf-8"))
big = [e for e in sa if (e.get("stall") or 0) >= 0.5]
print(f"STALL_ANATOMY 中 stall>=0.5s 条目 = {len(big)}")

TRIPDIR = {e["trip"]: None for e in sa}
# 逐条回原始 measure 文件重算
bad, ok, miss = [], [], []
for e in big:
    trip = e["trip"]
    d = trip
    p = f"{ROOT}/{d}/measure_w{e['w']}.json"
    if not os.path.isfile(p):
        miss.append((trip, e["w"], "原始 measure 文件不在盘"))
        continue
    m = json.load(open(p, encoding="utf-8"))
    t, f = m["samples"]["t"], m["samples"]["f"]
    segs, i, n = [], 0, len(t)
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        if t[j] - t[i] >= 0.5:
            segs.append((f[i], round(t[i] - t[0], 3), round(t[j] - t[i], 3)))
        i = j + 1
    cs = m.get("counters") or []
    u = [c["units"] for c in cs]
    tt = [c["t_rel"] for c in cs]
    b = [c.get("b") for c in cs]
    flat = None
    for k in range(1, len(u)):
        if all(u[q] == u[k] for q in range(k, len(u))):
            flat = round(tt[k], 3)
            break
    bzero = [round(tt[k], 3) for k in range(len(b)) if b[k] == 0]
    fz = segs[0][1] if segs else None
    # 关键判据：冻结起点**之后**是否仍有 units 变化步（而非全窗变化点数）
    after = ([i for i in range(1, len(u)) if tt[i] > fz and u[i] != u[i - 1]]
             if fz is not None else [])
    lastchg = max([i for i in range(1, len(u)) if u[i] != u[i - 1]] or [0])
    print(f"  {trip:18s} w={e['w']} pre={e['pre']} u0={e['u0']} 自算冻结={segs[:2]} "
          f"units停变(全程持平起点)={flat} 最后变化t_rel={round(tt[lastchg],3) if tt else None} "
          f"冻结后仍变化步={len(after)} idx={after[:6]} 对方b归零={bzero[:1]}")
    verdict = None
    if fz is not None:
        if not after:
            verdict = "终局(冻结期内 units 无变化)"
            ok.append((trip, e["w"], fz, flat, len(after), bzero[:1], e["u0"]))
        else:
            verdict = "反例(冻结起点后 units 仍在变)"
            bad.append((trip, e["w"], fz, round(tt[after[0]], 3), len(after), bzero[:1], e["u0"]))
    print(f"       => {verdict}")
print(f"\n终局判定成立 = {len(ok)} / 反例 = {len(bad)} / 原始件不在盘 = {len(miss)}")
if miss:
    print("不在盘条目:", miss)
if bad:
    print("反例:", bad)
else:
    print("=> 台账『31 档战斗趟长停顿全是终局帧冻结』在全部可核条目上 **未被否证**（我的 R-3 撤回）")
