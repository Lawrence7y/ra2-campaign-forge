# -*- coding: utf-8 -*-
"""§533 probe E -- 用**既有真机趟数据**检验「帧冻结 = MainLogicFrame 焦点门不自旋」假设。

只读。零真机、零进程、零写入（除 stdout）。

假设 H-focus（probe A/B 从字节推出）：
  0x55D377  mov al,[0xA8ED80]   ; 焦点/快进旗标
  0x55D385  jne 0x55D3BB        ;   !=0  -> 直落帧体
  ---- 否则进入自旋： --------------------------------------------------
  0x55D38D  mov eax,[0xA8B238]  ; GameMode
  0x55D39B  push 0x1F4; call Sleep     (Mode∈{0,5} -> 500ms)
  0x55D3A2  call 0x5D4D50       ; MessagePump
  0x55D3A7  mov al,[0xA8ED80]
  0x55D3AE  je 0x55D38D         ; ★ 旗标仍 0 -> 回到循环顶（永不推进帧）
  0x55D3B2  push 0xA; call Sleep        (其它 Mode -> 10ms)
  ⇒ 预测：凡是「帧号长时间不推进」的测量窗，同一时刻的 [0xA8ED80] 必须 == 0。
    反之旗标==1 时帧号必须推进（除非世界更新自身耗时）。

数据源（既有、零新增）：
  lead/qc161_u0400_trip/c2ab_x/*/timeline.json   —— battle_tl 行内有 {t, frame, tick}
"""
import glob
import json
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
PAT = os.path.join(ROOT, "lead", "qc161_u0400_trip", "c2ab_x", "*", "timeline.json")
files = sorted(glob.glob(PAT))
print("timeline files: %d" % len(files))

rows = []          # (file, source, t, frame, tick, gamemode?)
for fp in files:
    d = json.load(open(fp, encoding="utf-8"))
    tag = os.path.basename(os.path.dirname(fp))
    for src in ("battle_tl", "pre5"):
        for r in d.get(src) or []:
            rr = r.get("sent", r)
            if not isinstance(rr, dict):
                continue
            t, f, tk = rr.get("t"), rr.get("frame"), rr.get("tick")
            if isinstance(t, (int, float)) and isinstance(f, int) and isinstance(tk, int):
                rows.append((tag, src, t, f, tk))
print("rows with (t,frame,tick): %d" % len(rows))

print()
print("=" * 76)
print("T1 tick 值分布（全样本）")
print("=" * 76)
from collections import Counter
c = Counter(r[4] for r in rows)
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print("  tick=%r : %d (%.1f%%)" % (k, v, 100.0 * v / len(rows)))

print()
print("=" * 76)
print("T2 逐趟：tick 值与帧增量（按趟归组，battle_tl 按 t 排序）")
print("=" * 76)
by = {}
for tag, src, t, f, tk in rows:
    by.setdefault(tag, []).append((src, t, f, tk))

for tag in sorted(by):
    rs = sorted(by[tag], key=lambda x: x[1])
    ticks = set(r[3] for r in rs)
    fr = [r[2] for r in rs]
    steps = [(rs[i + 1][1] - rs[i][1], rs[i + 1][2] - rs[i][2], rs[i][3])
             for i in range(len(rs) - 1)]
    stall = [(dt, df, tk) for dt, df, tk in steps if df == 0 and dt > 0.3]
    print("\n%-34s n=%2d frames[%d..%d] ticks=%s" % (
        tag, len(rs), min(fr), max(fr), sorted(ticks)))
    if stall:
        print("    ★ Δf==0 且 Δt>0.3s 的区间 %d 个:" % len(stall))
        for dt, df, tk in stall[:10]:
            print("       Δt=%.3fs Δf=%d  tick(前样本)=%r" % (dt, df, tk))
    else:
        print("    无 Δf==0 长区间")

print()
print("=" * 76)
print("T3 ★ 假设检验核心表：每个「Δt>0.3s 且 Δf==0」样本对照其 tick")
print("=" * 76)
viol = 0
total = 0
for tag in sorted(by):
    rs = sorted(by[tag], key=lambda x: x[1])
    for i in range(len(rs) - 1):
        _, t0, f0, k0 = rs[i]
        _, t1, f1, k1 = rs[i + 1]
        dt, df = t1 - t0, f1 - f0
        if dt > 0.3:
            total += 1
            if df == 0 and k0 != 0:
                viol += 1
                print("  VIOLATION? %-30s Δt=%.3f Δf=%d tick=%r" % (tag, dt, df, k0))
print("  Δt>0.3s 的相邻样本对：%d；其中 Δf==0 但 tick!=0 的违例：%d" % (total, viol))

print()
print("=" * 76)
print("T4 反向检验：tick==0 的样本，帧号是否真的不动")
print("=" * 76)
zero = [r for r in rows if r[4] == 0]
print("  tick==0 样本数：%d" % len(zero))
for tag, src, t, f, tk in zero[:20]:
    print("     %-30s %s t=%.1f frame=%d" % (tag, src, t, f))
