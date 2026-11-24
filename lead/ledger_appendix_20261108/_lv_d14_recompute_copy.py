# -*- coding: utf-8 -*-
"""_d14_recompute.py —— _d14 必要性补证 · 原始语料独立重算（只读，不写任何既有件）。

目的：为 O1–O4 必要性构造性证明提供本轮自跑的数值基础：
  1) 母体 B（isRealMatch==True 且 startTick>0）逐事件 U = (t[startTick]-t[startTick-1])*1000；
  2) U>50ms 计数（O1 反例的事件池）；
  3) max U 事件的 (trip, window, startTick) 与原始 t 实值（O1 反例的场景参数）；
  4) O1 括注算术（50ms 预算 / 20ms 裕量两种读法）。
纪律：零真机；零采样代码；只读既有件；输出仅落本写域 _d14_recompute_out.txt。
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
EVENTS = ROOT / "lead" / "stall_event_def_20261106" / "STALL_EVENTS.json"
BASE = ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead" / "qc161_u0400_trip"
OUT = ROOT / "lead" / "ledger_appendix_20261108" / "_lv_d14_recompute_out.txt"

_buf = []


def out(s=""):
    _buf.append(str(s))


def main():
    events = json.loads(EVENTS.read_bytes())
    real = [e for e in events if e.get("isRealMatch") is True]
    out("STALL_EVENTS 全量 n=%d；isRealMatch==True n=%d" % (len(events), len(real)))
    pred = [e for e in real if e.get("startTick", 0) > 0]
    out("真实事件有前序者（startTick>0）n=%d；startTick=0 n=%d" % (len(pred), len(real) - len(pred)))

    cache = {}

    def tarr(trip, window):
        key = (trip, window)
        if key not in cache:
            p = BASE / trip / ("measure_%s.json" % window)
            d = json.loads(p.read_bytes())
            cache[key] = (d["samples"]["t"], d["samples"]["f"])
        return cache[key]

    us = []
    for e in pred:
        t, _f = tarr(e["trip"], e["window"])
        i = e["startTick"]
        if i <= 0 or i >= len(t):
            out("!! 越界事件 %s/%s startTick=%d (len t=%d)" % (e["trip"], e["window"], i, len(t)))
            continue
        u_ms = (t[i] - t[i - 1]) * 1000.0
        us.append((u_ms, e["trip"], e["window"], i))

    us.sort()
    n = len(us)
    vals = [u[0] for u in us]
    out("有效 U 样本 n=%d" % n)
    out("min U = %.3f ms" % vals[0])
    out("median U = %.3f ms" % vals[n // 2])
    out("max U = %.3f ms  出处 trip=%s window=%s startTick(sample index)=%d"
        % (vals[-1], us[-1][1], us[-1][2], us[-1][3]))

    gt50 = [u for u in us if u[0] > 50.0]
    out("U > 50.0ms 计数 = %d（占全集 1681 = %.4f%%）" % (len(gt50), len(gt50) / len(real) * 100.0))
    out("U > 50.0ms 的事件是否全部 startTick>0（即 ⊆1677 窗内可还原母体）：%s"
        % ("是" if len(gt50) == len([u for u in gt50]) else "否"))
    gt100 = [u for u in us if u[0] > 100.0]
    out("U > 100.0ms 计数 = %d" % len(gt100))

    # 极值事件的原始样本实值（O1 反例场景参数）
    umax, tmax, wmax, imax = us[-1]
    t, f = tarr(tmax, wmax)
    out("")
    out("[O1 反例场景参数 · 极值事件原始实值]")
    out("事件 = %s/%s, 停滞首拍样本索引 i = %d" % (tmax, wmax, imax))
    out("t[i-1] (S_low, 帧号 f=%d) = %.6f s" % (f[imax - 1], t[imax - 1]))
    out("t[i]   (S_obs/S_hat, 帧号 f=%d) = %.6f s" % (f[imax], t[imax]))
    out("U = t[i]-t[i-1] = %.6f ms" % umax)
    j = imax
    while j + 1 < len(f) and f[j + 1] == f[imax]:
        j += 1
    out("帧号恒定段末样本索引 = %d, t = %.6f s, 平台时长 = %.6f ms"
        % (j, t[j], (t[j] - t[imax]) * 1000.0))
    out("下一帧号推进样本索引 = %d, f = %d" % (j + 1, f[j + 1]) if j + 1 < len(f) else "")

    # O1 括注算术（更正件数值）
    out("")
    out("[O1 括注算术 · 50ms 预算]")
    out("单项读法 1/50 = %.4f%%" % (1.0 / 50.0 * 100.0))
    out("求和读法 (1+1)/50 = %.4f%%" % (2.0 / 50.0 * 100.0))
    out("[O1 括注算术 · :190 的 20ms 安全裕量]")
    out("单项读法 1/20 = %.4f%%" % (1.0 / 20.0 * 100.0))
    out("求和读法 (1+1)/20 = %.4f%%" % (2.0 / 20.0 * 100.0))
    out("求和绝对量 2ms ≤ 20ms 裕量：%s" % ("成立" if 2.0 <= 20.0 else "不成立"))

    # O1 反例数值（缺 O1，有 O2/O3/O4）
    out("")
    out("[O1 反例数值 · 缺 O1 时极值事件 C-S 的可行区间]")
    s_low_ms, s_obs_ms = t[imax - 1] * 1000.0, t[imax] * 1000.0
    c_ms = s_obs_ms + 10.0  # 场景取值：C 读数 = S_hat + 10ms
    out("设 C 读数 = S_hat + 10.000 ms（O2 ≤1ms、O3 残差 ≤1ms 到位）")
    out("世界 A：S = S_hat = %.3f ms  =>  C - S = %.3f ms  (≤50 合规)" % (s_obs_ms, c_ms - s_obs_ms))
    out("世界 B：S → S_low+ = %.3f ms  =>  C - S → %.3f ms (>50 违规)" % (s_low_ms, c_ms - s_low_ms))
    out("两世界在全部在案观测量上无差别；区间宽度 = U = %.3f ms" % umax)

    # O2 反例数值（缺 O2，有 O1/O3/O4；约束只有下界 C ≥ S_hat）
    out("")
    out("[O2 反例数值 · 缺 O2 时 C 无值可算]")
    s_ms = s_obs_ms  # 设 O1 已给 S（取观测首拍，±1ms）
    out("O1 给 S = %.3f ms（±1ms）；语料对 C 的仅有约束 = 下界 C ≥ S_hat（CRITERIA_COMPARE.md:96）" % s_ms)
    out("世界 A：C = S + 40.000 ms => C - S = 40.000 ms (≤50 合规)")
    out("世界 B：C = S + 90.000 ms => C - S = 90.000 ms (>50 违规)")
    out("两世界 C 均满足 C ≥ S_hat 下界与 O4 标记（标记无时刻字段）；在案观测全同")

    # O3 反例数值（缺 O3，有 O1/O2/O4）
    out("")
    out("[O3 反例数值 · 缺 O3 时跨钟系统偏差 δ 不受约束]")
    out("S 类读数（采样器钟）：S_read = 5000.000 ms；C 类读数（保存机制钟）：C_read = 5040.000 ms")
    out("名义差 C_read - S_read = 40.000 ms")
    out("世界 A：δ = 0    => 真 C - S = 40.000 ms (≤50 合规)")
    out("世界 B：δ = -15.0（C 类钟读数 = 真时刻 - 15ms）=> 真 C - S = 40.000 - δ = 55.000 ms (>50 违规)")
    out("δ ∈ [-20, +20] ms 时真 C - S ∈ [20.000, 60.000] ms，跨越 50ms 判定线")
    out("补 O3（残差上界 ≤1ms）后真 C - S ∈ [39.000, 41.000] ms，判定闭合（本构造远离边缘）")

    text = "\n".join(_buf) + "\n"
    OUT.write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
