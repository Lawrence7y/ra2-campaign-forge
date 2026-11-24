# -*- coding: utf-8 -*-
"""A7 第二探针：帧时长序列的 lag-k 自相关（直接测周期性）。

为什么前两次 ACF 失败，这次不会：
  失败1「时间重标定 ACF」：点对估计器在邻域样本极少时除以总体方差 ⇒ 慢窗给 ACF>1 伪值。
  失败2「50ms 固定分箱 ACF」：>120ms/帧 ⇒ 每箱不足 2 帧 ⇒ 慢窗全丢。
本探针用在**帧序号上等间隔**的序列（每帧一个时长），不做时间重标定、不做固定时间分箱
⇒ 慢窗快窗一视同仁。lag-k Pearson 自相关，n=220~780，标准误 ~1/sqrt(n)。

判定口径先写死：
  r(k) = corr(dur[i], dur[i+k])
  若存在 k* 帧周期，r(k*) 应显著为正且远高于其它 lag。
  显著性界限：|r| > 2/sqrt(n) 约当 p<0.05（白噪声近似）。
"""
import collections
import io
import json
import math
import os
import random
import statistics

random.seed(20261106)
ROOT = r"D:\Project\ra2-campaign-forge"
OUT = []


def P(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s)


def load(rel):
    return json.load(io.open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8"))


def durations(d):
    fe = d["frame_edges"]
    return [(fe[i][1] - fe[i - 1][1]) * 1000.0 for i in range(1, len(fe))]


def acf(x, k):
    n = len(x)
    if n <= k + 2:
        return None
    a = x[: n - k]
    b = x[k:]
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    va = sum((v - ma) ** 2 for v in a)
    vb = sum((v - mb) ** 2 for v in b)
    if va <= 0 or vb <= 0:
        return None
    cov = sum((u - ma) * (v - mb) for u, v in zip(a, b))
    return cov / math.sqrt(va * vb)


P("=" * 78)
P("A7 第二探针：帧时长序列 lag-k 自相关（在帧序号上等间隔，不做时间重标定/分箱）")
P("=" * 78)

CAND = []
for dp, dns, fns in os.walk(os.path.join(ROOT, "lead")):
    dns[:] = [x for x in dns if x not in ("__pycache__", ".git")]
    for fn in fns:
        if fn.startswith("measure_w") and fn.endswith(".json"):
            CAND.append(os.path.join(dp, fn).replace(ROOT + os.sep, "").replace(os.sep, "/"))

rows = []
for rel in sorted(CAND):
    try:
        d = load(rel)
    except Exception:
        continue
    if d.get("verdict") != "ok":
        continue
    st = d.get("stats") or {}
    hz = st.get("hz_effective")
    if hz is None or hz < 100:
        continue
    rows.append((rel, st))

P("\n[0] 合格窗 = %d（verdict=ok 且 hz_effective>=100）" % len(rows))

MAXK = 16
P("\n[1] 每窗的 lag 1..%d 自相关；粗体为 |r| > 2/sqrt(n)（约 p<0.05）" % MAXK)
P("    以及 lag=8 的置换 p 值（把时长序列随机重排 2000 次）")
P("\n  %-40s %5s %8s %8s %8s %8s" % ("window", "n", "r(8)", "p(r8)", "r(1)", "max|r|,k"))

summary = []
for rel, st in rows:
    d = load(rel)
    x = durations(d)
    n = len(x)
    if n < 40:
        continue
    thr = 2.0 / math.sqrt(n)
    rs = {}
    for k in range(1, MAXK + 1):
        r = acf(x, k)
        if r is not None:
            rs[k] = r
    if not rs:
        continue
    r8 = rs.get(8)
    # 置换检验：shuffle 时长序列，看 r(8)
    null = []
    work = x[:]
    for _ in range(2000):
        random.shuffle(work)
        rr = acf(work, 8)
        if rr is not None:
            null.append(rr)
    null.sort()
    p8 = None
    if null and r8 is not None:
        p8 = sum(1 for v in null if v >= r8) / len(null)
    kmax = max(rs, key=lambda k: abs(rs[k]))
    summary.append((rel, n, r8, p8, rs.get(1), kmax, rs[kmax], thr))
    P("  %-40s %5d %8.3f %8.4f %8.3f  %2d (%.3f)  thr=%.3f" % (
        rel[-40:], n, r8 if r8 is not None else float("nan"),
        p8 if p8 is not None else float("nan"),
        rs.get(1) if rs.get(1) is not None else float("nan"),
        kmax, rs[kmax], thr))

P("\n[2] 汇总")
n8_sig = sum(1 for s in summary if s[3] is not None and s[3] < 0.05)
n8_pos = sum(1 for s in summary if s[2] is not None and s[2] > 0)
P("  窗数 = %d" % len(summary))
P("  r(8) > 0 的窗 = %d" % n8_pos)
P("  r(8) 置换 p < 0.05 的窗 = %d" % n8_sig)
if summary:
    r8s = [s[2] for s in summary if s[2] is not None]
    p8s = [s[3] for s in summary if s[3] is not None]
    P("  r(8) 中位 = %.4f，范围 [%.3f, %.3f]" % (statistics.median(r8s), min(r8s), max(r8s)))
    P("  r(8) 的 p 值中位 = %.4f" % statistics.median(p8s))
    P("  ⇒ 在 15 次检验、alpha=0.05 下，期望假阳性 = %.2f，P(至少一个假阳性) = %.3f"
      % (0.05 * len(summary), 1 - 0.95 ** len(summary)))

P("\n" + "=" * 78)
P("判定")
P("=" * 78)
if n8_sig == 0:
    P("  ⇒ **所有窗的 lag-8 自相关都不显著**（置换 p 全 > 0.05）")
    P("  ⇒ 「帧时长按 8 帧周期变化」在现有 500 Hz 语料上**无信号**")
else:
    P("  ⇒ %d 个窗 lag-8 显著，需核对是否同一周期" % n8_sig)
P("")
P("  ★ 与 mod-8 探针的联合读法：")
P("    mod-8（按帧号分组）与 ACF lag-8（序列自相关）是两个独立角度；")
P("    两者都无信号 ⇒ 不是单一探针的假阴性。")
P("  ★ 与「同进程连续窗图样不复现」的联合读法：")
P("    若周期性绑定在引擎帧号上，同进程 w0/w1/w2 的 argmin/argmax 应一致；")
P("    实测 l1c 三窗分别是 (1,3)/(6,7)/(4,7)，全不一致 ⇒ 不支持帧号相位锁定。")
P("")
P("  ⚠ 本探针**能排除的**：在 220~780 帧的窗口尺度上、按帧号相位锁定的 8 帧周期。")
P("  ⚠ 本探针**不能排除的**：①相位漂移的周期（会抹平 ACF）")
P("    ②周期长于窗口（>220 帧）③只影响某一小段而非整窗的周期")

io.open(os.path.join(ROOT, r"lead\re_line_20261105\_leader\_a7_acf_probe_out.txt"),
        "w", encoding="utf-8").write("\n".join(OUT) + "\n")
P("\nDONE")
