#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p10：frame 计数器起点语义定谳 + q/r 早相可行性界（承重计算，逐步留痕）。

(1) 语义：短路臂三趟（l1_20261023e1/hb/k）nav 收口后 0.11-0.23 s 即进 measure，
    f[0]=0 ⇒ 进 battle 瞬间计数器为 0；同窗 counters 首行 units 由 0 爬到 971，
    用 frame_edges 内插求「units 首次 >0 时刻的 frame 值」⇒ 若计数器自进程起累计则此时应≫0。
    交叉证据：菜单趟（E12 未进 battle）同一 VA 恒 0（p03 §(1)）。
(2) 可行性界：设 q/r 的 battle→w0 墙钟 W、f0=F0；把帧域 [A,B]（本批 hb 的 437→991 同域）
    的 fps 记 x，其余帧按族内可持续上限 V（49 个可测窗 fps_avg 最大值=31.32 ⇒ 取 31.4 为乐观上限）
    ⇒ W ≥ (B−A)/x + (F0−(B−A))/V ⇒ 解 x 下界。x 下界 ≫ hb 实测 ⇒ 「q 早相与 hb 同慢」被否。
(3) 敏感性：V ∈ {31.4, 32, 40}（40/50 为超族内上限的放宽，仅用于说明对 V 的依赖强度）。
只读。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
R = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def edges_of(m):
    return [(int(f), t) for f, t in (m.get("frame_edges") or [])]

def t2f(E, t):
    if not E:
        return None
    if t <= E[0][1]:
        return E[0][0]
    for (fa, ta), (fb, tb) in zip(E, E[1:]):
        if ta <= t <= tb:
            return fb if tb == ta else fa + (fb - fa) * (t - ta) / (tb - ta)
    return E[-1][0]

print("=" * 78)
print("(1) units 首次 >0 时的 frame 值（battle 起点语义）")
print("=" * 78)
for d in ("l1_20261023e1", "l1_20261023hb", "l1_20261023k"):
    m = json.load(open(f"{R}/{d}/measure_w0.json", encoding="utf-8"))
    E = edges_of(m)
    cs = m["counters"]
    f0 = m["samples"]["f"][0]
    base = E[0][1] if E else None
    first = next((c for c in cs if (c.get("units") or 0) > 0), None)
    fr_at = t2f(E, base + first["t_rel"]) if (first and base) else None
    print(f"  {d}: verdict={m['verdict']} f[0]={f0} f[-1]={m['samples']['f'][-1]} "
          f"span={m['span_s']}s  units 序列={[c['units'] for c in cs]}")
    if first:
        print(f"      units 首 >0：t_rel={first['t_rel']} units={first['units']} ⇒ 内插 frame={None if fr_at is None else round(fr_at,1)}"
              f"（进程此刻已活 ≈44-58 s：导航+窗口稳定段）")

print("\n" + "=" * 78)
print("(2) q/r 早相可行性界（hb 同帧域 437→991 若也发生在 q/r，需多快才塞得进墙钟）")
print("=" * 78)
A, B = 437, 991
for d in ("l3_20261023q", "l3_20261023r"):
    m = json.load(open(f"{R}/{d}/measure_w0.json", encoding="utf-8"))
    f = json.load(open(f"{R}/{d}/qc151_fields.json", encoding="utf-8"))
    net = [e["value"] for e in f if e.get("group") == "NAV" and e.get("key") == "h7_nav_end_t"][-1]
    F0 = m["samples"]["f"][0]
    T0 = m["samples"]["t"][0]
    W = round(T0 - net, 3)
    seg = B - A
    rest = F0 - seg
    print(f"\n  {d}: NAV.h7_nav_end_t={net}  w0 t[0]={T0}（同一 perf_counter 轴）⇒ W(battle→w0)={W} s；f0={F0}")
    print(f"    平均 = {F0/W:.2f} fps（ask 问「是否真 ≥23」⇒ {'是' if F0/W>=23 else '否'}）")
    print(f"    设帧域 [{A},{B}]（宽 {seg} 帧）以 x fps 通过，其余 {rest} 帧以族内上限 V：")
    for V in (31.4, 32.0, 40.0, 50.0):
        rem_t = W - rest / V
        x_min = seg / rem_t if rem_t > 0 else float("inf")
        print(f"      V={V:<5} ⇒ 该域可用时 {rem_t:7.2f} s ⇒ x ≥ {x_min:5.2f} fps"
              f"   [hb 实测同域 {A}->{B}: w0 6.79 / w1 4.73 / w2 10.60 fps_avg]")
    print(f"    ⇒ 结论：x 下界 {seg/(W-rest/31.4):.1f} fps（V=31.4）远高于 hb 同域实测 4.7~10.6 fps"
          f" ⇒ 「q/r 早相与 hb 早相一样慢」与盘上时间戳+帧数不相容（需 x≤{seg/(W-rest/31.4):.1f} 的倍数级证据才可能成立）")

print("\n" + "=" * 78)
print("(3) 对照：若假设 frame 自进程起累计（另一语义），预测 q 的 f0 应是多少")
print("=" * 78)
for d in ("l3_20261023q", "l3_20261023r"):
    f = json.load(open(f"{R}/{d}/qc151_fields.json", encoding="utf-8"))
    def gv(g, k):
        v = [e["value"] for e in f if e.get("group") == g and e.get("key") == k]
        return v[-1] if v else None
    proc_to_nav = gv("WIN", "seconds_to_window")
    fr_s = gv("BUDGET", "stage_seconds:frame")
    m = json.load(open(f"{R}/{d}/measure_w0.json", encoding="utf-8"))
    F0 = m["samples"]["f"][0]
    print(f"  {d}: 实得 f0={F0}；进程起累计假设 ⇒ f0 须 ≥ 菜单/加载段时长 × 该段 fps。"
          f"菜单段仅窗口稳定即花 {proc_to_nav} s（WIN.seconds_to_window），"
          f"而 E12 菜单趟同 VA 读数恒 0（p03 §(1)）⇒ 该假设被否。")
