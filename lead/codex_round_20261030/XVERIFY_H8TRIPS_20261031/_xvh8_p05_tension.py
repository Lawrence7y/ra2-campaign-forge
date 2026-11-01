#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p05：跨族帧域对比的状态有效性 + 早相可行性上界（族内实测上限标定）。

(A) 全库 measure 窗 fps_avg 分布 ⇒ 族内「可持续平均 fps」上限（用于 q 早相可行性反证）；
(B) Δu/Δf（每逻辑帧 units 变化率）逐窗：q/r vs ha/hb/l3_20261021 ⇒ 「同帧号是否同战场状态」；
(C) 可行性界：q 的 0→f0 若含 L 帧 ≤10fps 慢段，余下 2955−L 帧需 ≥V fps；对 V 取族内上限
    与若干放宽值列表解 L 上界，并与 hb 的慢段帧数（437→991=554 帧）比较；
(D) P2 哨兵快照（house c5574 求和）在场趟 ⇒ 战场实体规模对照（含 ha 全零形态的读侧不可靠标注）。
只读。
"""
import json, io, sys, os, glob, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def fld(d):
    p = f"{ROOT}/{d}/qc151_fields.json"
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else []

def gv(f, g, k):
    v = [e["value"] for e in f if e.get("group") == g and e.get("key") == k]
    return v[-1] if v else None

print("=" * 78)
print("(A) 全库窗 fps_avg 分布（族内可持续平均上限标定）")
print("=" * 78)
vals = []
for p in sorted(glob.glob(f"{ROOT}/*/measure_w*.json")):
    d = os.path.basename(os.path.dirname(p))
    try:
        m = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    st = m.get("stats") or {}
    fa = st.get("fps_avg")
    if isinstance(fa, (int, float)) and fa > 0:
        vals.append((round(fa, 3), d, os.path.basename(p)))
vals.sort(reverse=True)
print(f"  有值窗数 n={len(vals)}   top10 = {[v[0] for v in vals[:10]]}")
print(f"  ⇒ 族内观测到的最大窗平均 fps = {vals[0][0]}（{vals[0][1]}/{vals[0][2]}）")
print(f"  31 档带（>25）窗数={sum(1 for v in vals if v[0]>25)}  低相带（<12）窗数={sum(1 for v in vals if v[0]<12)}")

print("\n" + "=" * 78)
print("(B) Δu/Δf 逐窗（同帧号是否同战场状态）")
print("=" * 78)
print("  注：counters.t_rel 用同窗 frame_edges 内插到帧轴；首末 counters 点求差。")
for d in ("l3_20261031ha", "l3_20261031hb", "l3_20261023q", "l3_20261023r", "l3_20261021",
          "l1_20261023e4", "t55k_20261020", "l1a_20261020"):
    for wp in sorted(glob.glob(f"{ROOT}/{d}/measure_w*.json")):
        m = json.load(open(wp, encoding="utf-8"))
        edges = m.get("frame_edges") or []
        cs = m.get("counters") or []
        if not edges or len(cs) < 2:
            print(f"  {d}/{os.path.basename(wp)}: 边表/counters 不足（n_edges={len(edges)}, n_cnt={len(cs)}）")
            continue
        E = [(int(f), t) for f, t in edges]
        def t2f(t):
            if t <= E[0][1]: return E[0][0]
            for (fa, ta), (fb, tb) in zip(E, E[1:]):
                if ta <= t <= tb:
                    return fb if tb == ta else fa + (fb - fa) * (t - ta) / (tb - ta)
            return E[-1][0]
        # counters.t_rel 是「相对窗起点」秒；frame_edges 的 t 是同窗 samples 的 perf_counter 绝对值
        # ⇒ 先平移：t_abs = E[0][1] + t_rel（窗 0 首样即窗起点，§3.2 settle 之后连续采样）
        base = E[0][1]
        p0 = (t2f(base + cs[0]["t_rel"]), cs[0]["units"])
        p1 = (t2f(base + cs[-1]["t_rel"]), cs[-1]["units"])
        if p0[1] is None or p1[1] is None:
            print(f"  {d:<16}{os.path.basename(wp):<18} units 读数含 null ⇒ 不可算")
            continue
        df = p1[0] - p0[0]
        rate = (p1[1] - p0[1]) / df if df else None
        print(f"  {d:<16}{os.path.basename(wp):<18} frame {round(p0[0]):>5}→{round(p1[0]):<5} "
              f"units {p0[1]:>5}→{p1[1]:<5} Δu/Δf={rate if rate is None else round(rate,4)}")

print("\n" + "=" * 78)
print("(C) q 早相可行性：若含 L 帧慢段（≤10fps），其余帧需 ≥V fps ⇒ 解 L 上界")
print("=" * 78)
for d in ("l3_20261023q", "l3_20261023r"):
    f = fld(d)
    net = gv(f, "NAV", "h7_nav_end_t")
    m = json.load(open(f"{ROOT}/{d}/measure_w0.json", encoding="utf-8"))
    T0 = m["samples"]["t"][0]; F0 = m["samples"]["f"][0]
    wall = round(T0 - net, 3)
    print(f"\n  {d}: NAV.h7_nav_end_t={net}  w0 t[0]={T0}  ⇒ 同一 perf_counter 轴墙钟 battle起→w0 = {wall} s")
    print(f"    f0={F0} ⇒ 平均 = {F0/wall:.2f} fps（≥23 主张 {'成立' if F0/wall >= 23 else '不成立'}）")
    hb_slow_frames = 991 - 437
    print(f"    hb 慢段参照帧数（437→991）= {hb_slow_frames}；若 q 也含 L 帧 ≤10 fps 段，余下按 V fps：")
    for V in (31.4, 32.0, 40.0, 50.0, 60.0):
        # wall >= L/10 + (F0-L)/V  ⇒ L <= (wall - F0/V) / (1/10 - 1/V)
        denom = (1/10 - 1/V)
        L = (wall - F0 / V) / denom
        print(f"      V={V:<5} ⇒ L ≤ {L:7.1f} 帧  {'< hb 慢段 ⇒ q 不可能整段同慢' if L < hb_slow_frames else '≥ hb 慢段 ⇒ 不能排除'}")

print("\n" + "=" * 78)
print("(D) P2 哨兵 house c5574 求和（战场实体规模）+ 读侧可靠性标注")
print("=" * 78)
for d in ("l3_20261031hb", "l3_20261031ha", "l3_20261023q", "l3_20261023r"):
    f = fld(d)
    p2 = [e for e in f if e.get("group") == "QC213P2"]
    snaps = sorted(set(e["key"][:7] for e in p2))
    for s in snaps:
        row = {e["key"]: e["value"] for e in p2 if e["key"].startswith(s + "_")}
        vals = [row.get(f"{s}_qc213p2_h{i}_c5574") for i in range(4)]
        kind = row.get(f"{s}_qc213p2_kind")
        tot = sum(v for v in vals if isinstance(v, int))
        print(f"  {d:<16} snap={s[1:]} kind={kind} houses={vals} sum={tot}")
    fr = gv(f, "MEASURE", "h7_frame_wait")
    n2m = gv(f, "MEASURE", "h7_nav_to_measure")
    print(f"      （时间归属：H8 等待={json.dumps(fr)} / nav→measure={json.dumps(n2m)}）"
          f"⇒ 快照期=等待期/加载期，非采窗期（Y-4 声明：探针不承重）")
