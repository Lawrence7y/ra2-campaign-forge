#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
W102 §A-8 · g_far 的 4.9064 pp 极差住在哪？
已从 A_recompute.txt §A-6 看到：逐 10 s 段间差最大 +10.005 pp @ 80-90 s。
本脚本逐点构造：若把某一臂的采样窗裁掉，rate 会变成多少 ⇒ 反推"哪一段单独贡献了极差"。

顺带回答 §634 与 ABBA 都要用的一个问题：
  「一个 60 s 段落在不同相位，rate 差多少」—— 这是 ABBA 段长定 60 s 的直接后果。
"""
import json, os

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r08\W98_clean\out"
NS_MS = 1_000_000.0


def load_s(trip):
    rows = []
    with open(os.path.join(OUT, trip, "run.ndjson"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return [r for r in rows if r.get("kind") == "sample"
            and r.get("elapsed_ingame_s") is not None]


def rate(win):
    if len(win) < 5:
        return None
    t0, t1 = win[0]["t_perf_ns"], win[-1]["t_perf_ns"]
    wall_ms = (t1 - t0) / NS_MS
    sm = 0.0
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        if a.get("read_status") != "ok" or b.get("read_status") != "ok":
            continue
        d = b.get("win_cpu_ms_delta")
        if d is not None:
            sm += d
    return sm / wall_ms * 100.0


def slice_t(s, lo, hi):
    return [r for r in s if lo <= r["elapsed_ingame_s"] < hi]


TRIPS = ["trip_g_idle_r1", "trip_g_idle_r2", "trip_g_near_r1", "trip_g_near_r2",
         "trip_g_far_r1", "trip_g_far_r2"]
S = {t: load_s(t) for t in TRIPS}

print("=" * 108)
print("W102 §A-8-1 · 逐 30 s 切片的 rate（每 cell 两趟并排；给出 60 s 段的相位敏感性）")
print("=" * 108)
print("{:<8}".format("窗口 s") + "".join("{:>17}".format(t.replace("trip_", "")) for t in TRIPS))
for lo in range(0, 150, 30):
    row = "{:<8}".format("{}-{}".format(lo, lo + 30))
    for t in TRIPS:
        v = rate(slice_t(S[t], lo, lo + 30))
        row += "{:>17}".format("{:.3f}".format(v) if v is not None else "-")
    print(row)

print()
print("=" * 108)
print("W102 §A-8-2 · 若用 60 s 段（ABBA 的段长），同一 cell 内不同位置的段 rate 差多少")
print("=" * 108)
print("{:<18}{:>10}{:>10}{:>10}{:>10}{:>12}".format(
    "trip", "0-60", "30-90", "60-120", "90-150", "段间极差"))
for t in TRIPS:
    vals = [rate(slice_t(S[t], lo, lo + 60)) for lo in (0, 30, 60, 90)]
    ok = [v for v in vals if v is not None]
    print("{:<18}{:>10}{:>10}{:>10}{:>10}{:>12.3f}".format(
        t, *["{:.3f}".format(v) if v is not None else "-" for v in vals],
        max(ok) - min(ok)))

print()
print("=" * 108)
print("W102 §A-8-3 · g_far 极差的定位：裁掉某一段后两趟是否收敛")
print("=" * 108)
f1, f2 = S["trip_g_far_r1"], S["trip_g_far_r2"]
for lo, hi, tag in [(0, 150, "全窗"), (0, 60, "只 0-60 s"), (60, 150, "只 60-150 s"),
                    (80, 150, "裁掉 0-80 s"), (0, 80, "只 0-80 s"),
                    (90, 150, "只 90-150 s"), (110, 150, "只 110-150 s")]:
    a = rate(slice_t(f1, lo, hi))
    b = rate(slice_t(f2, lo, hi))
    if a is None or b is None:
        continue
    print("  {:<14} far_r1={:>7.3f}  far_r2={:>7.3f}  差={:>+7.3f} pp".format(tag, a, b, b - a))

print()
print("=" * 108)
print("W102 §A-8-4 · 全窗 rate 的分解：Σ分段（30 s）加权 == 全窗？")
print("=" * 108)
for t in TRIPS:
    parts = []
    tot_ms = 0.0
    tot_wall = 0.0
    for lo in range(0, 150, 30):
        w = slice_t(S[t], lo, lo + 30)
        if len(w) < 5:
            continue
        wall = (w[-1]["t_perf_ns"] - w[0]["t_perf_ns"]) / NS_MS
        sm = sum((w[i]["win_cpu_ms_delta"] or 0.0) for i in range(1, len(w))
                 if w[i].get("read_status") == "ok" and w[i-1].get("read_status") == "ok")
        parts.append((lo, sm, wall))
        tot_ms += sm
        tot_wall += wall
    recomp = tot_ms / tot_wall * 100.0
    full = rate(S[t])
    print("  {:<18} 分段合成={:>8.4f}  全窗={:>8.4f}  差={:>+8.4f}".format(
        t, recomp, full, recomp - full))

print()
print("=" * 108)
print("W102 §A-8-5 · 一个 cell 内的\"相位位置\"配错能造出多大的虚假 d（ABBA 反例的准备数）")
print("=" * 108)
print("  用 g_idle（最平稳的 cell）与 g_far（交战臂）分别算：60 s 段在 0/30/60/90 四个位置的极差")
for t in TRIPS:
    vals = [rate(slice_t(S[t], lo, lo + 60)) for lo in (0, 30, 60, 90)]
    ok = [v for v in vals if v is not None]
    print("    {:<18} 极差 = {:>7.3f} pp".format(t, max(ok) - min(ok)))
