# -*- coding: utf-8 -*-
"""步骤5：r=0.921 的出处溯源
台账 §817-2 给了一张 9 行的 10 秒窗口表（来源是 W126_probe 的 50 ms 采样器）。
本脚本：把那张表原样抄进来，自己算 r，看能否精确复现 0.921 / 0.442 / 0.329。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []

# 台账 §817-2 的表（file:line = GOAL_THREE_TARGETS_20261018.md:18302-18312）
WIN = [0, 10, 20, 30, 40, 50, 60, 70, 80]
FRAMES = [199, 196, 262, 311, 308, 313, 313, 313, 313]
SCANS_PER_FRAME = [8.21, 17.28, 16.82, 14.97, 12.61, 11.34, 9.63, 8.27, 8.14]
BULLETS = [106.6, 87.5, 55.4, 27.3, 18.3, 15.7, 13.1, 9.3, 0.8]
MS_PER_FRAME = [50.40, 50.40, 50.30, 25.30, 25.35, 25.30, 25.30, 25.30, 25.30]


def main():
    OUT.append("=== §817-2 原表（9 个 10 秒窗口，单趟 trip_scan_near_r1，50 ms 采样器）===")
    OUT.append("  %5s %7s %10s %9s %10s" % ("win", "frames", "scans/fr", "bullets", "ms/frame"))
    for i in range(len(WIN)):
        OUT.append("  %5d %7d %10.2f %9.1f %10.2f" % (
            WIN[i], FRAMES[i], SCANS_PER_FRAME[i], BULLETS[i], MS_PER_FRAME[i]))

    r1, n1 = C.pearson(BULLETS, MS_PER_FRAME)
    r2, _ = C.pearson(SCANS_PER_FRAME, MS_PER_FRAME)
    r3, _ = C.pearson(SCANS_PER_FRAME, BULLETS)
    OUT.append("")
    OUT.append("=== 我用这张表自己算的相关（n=%d）===" % n1)
    OUT.append("  r(子弹, ms/frame)      = %.4f   ← 台账报 0.921" % r1)
    OUT.append("  r(scans/frame, ms/fr)  = %.4f   ← 台账报 0.442" % r2)
    OUT.append("  r(scans/frame, 子弹)   = %.4f   ← 台账报 0.329" % r3)

    # 顺带：如果 ms/frame 只有两档，r 对"档位"极敏感
    OUT.append("")
    OUT.append("=== ms/frame 在本表的取值 ===")
    OUT.append("  不同值 = %s （最大/最小 = %.2f）" % (
        sorted(set(MS_PER_FRAME)), max(MS_PER_FRAME) / min(MS_PER_FRAME)))
    # 档位二值化后与子弹的关系
    hi = [1 if m > 40 else 0 for m in MS_PER_FRAME]
    OUT.append("  高档(>40ms) 窗口 = %s" % [WIN[i] for i in range(len(WIN)) if hi[i]])
    OUT.append("  高档窗口的子弹均值 = %.1f ; 低档 = %.1f" % (
        C.mean([BULLETS[i] for i in range(len(WIN)) if hi[i]]),
        C.mean([BULLETS[i] for i in range(len(WIN)) if not hi[i]])))
    OUT.append("  高档窗口的 frames = %s ; 低档 = %s" % (
        [FRAMES[i] for i in range(len(WIN)) if hi[i]],
        [FRAMES[i] for i in range(len(WIN)) if not hi[i]]))

    # 960 → 帧数 vs ms 的一致性检查：若 ms/frame 真的是 1000*dt/frames, dt 应 ≈ 10 s
    OUT.append("")
    OUT.append("=== 自洽性检查：ms/frame × frames 应 ≈ 10000 ms（10 秒窗口）===")
    OUT.append("  %5s %12s %12s" % ("win", "ms*fr (ms)", "隐含 dt"))
    for i in range(len(WIN)):
        OUT.append("  %5d %12.1f %12s" % (WIN[i], MS_PER_FRAME[i] * FRAMES[i],
                                          "=窗口长" if abs(MS_PER_FRAME[i] * FRAMES[i] - 10000) < 400 else "**与 10 s 不符**"))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("05_provenance.txt", txt)


if __name__ == "__main__":
    main()
