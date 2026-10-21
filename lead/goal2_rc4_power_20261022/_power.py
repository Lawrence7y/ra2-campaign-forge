# -*- coding: utf-8 -*-
"""RC-4 复现率与 A/B 判据功效分析（离线，零真机）。

观测：11 趟中 2 趟复现 RC-4
（见 goal2_corpus_provenance_20261021/CORPUS_PROVENANCE_20261021.md）。
目的：判据「修复关 >=3/5 复现、修复开 0/5」在这个复现率下是否可行，
      以及若不可行，什么设计可行。

输出文件固定落在本脚本所在目录，不依赖调用时的 cwd。
"""
from math import comb
from pathlib import Path

OUTPUT_NAME = "POWER_ANALYSIS_OUTPUT.txt"


def pmf(k, n, p):
    return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def p_atleast(k, n, p):
    if k <= 0:
        return 1.0
    return sum(pmf(i, n, p) for i in range(k, n + 1))


def clopper_pearson(k, n, alpha=0.05):
    """精确二项 CI。

    P(X>=k | p) 随 p 单调递增  -> 下界
    P(X<=k | p) 随 p 单调递减  -> 上界
    """
    tgt = alpha / 2.0

    # 下界：解 P(X>=k) = tgt，f 递增
    lo_l, lo_h = 0.0, 1.0
    for _ in range(200):
        mid = (lo_l + lo_h) / 2.0
        if p_atleast(k, n, mid) > tgt:
            lo_h = mid
        else:
            lo_l = mid
    p_lo = (lo_l + lo_h) / 2.0

    # 上界：解 P(X<=k) = tgt，g 递减
    def g(p):
        return 1.0 - p_atleast(k + 1, n, p)

    hi_l, hi_h = 0.0, 1.0
    for _ in range(200):
        mid = (hi_l + hi_h) / 2.0
        if g(mid) > tgt:
            hi_l = mid
        else:
            hi_h = mid
    p_hi = (hi_l + hi_h) / 2.0

    return p_lo, p_hi


def negbinom_trips(p, r, conf):
    """达到 r 次复现所需趟数 N 的上分位（负二项）。返回满足 P(T<=N)>=conf 的最小 N。"""
    N = r
    while N <= 2000:
        # P(T <= N) = P(>= r successes in N trials)
        if p_atleast(r, N, p) >= conf:
            return N
        N += 1
    return None


def main():
    k, n = 2, 11
    p_hat = k / n
    lo, hi = clopper_pearson(k, n)

    out = []
    def P(s=""):
        out.append(s)

    P("=" * 70)
    P("一、RC-4 复现率（观测 %d/%d）" % (k, n))
    P("=" * 70)
    P("  点估计 p = %.4f  (%.1f%%)" % (p_hat, p_hat * 100))
    P("  Clopper-Pearson 95%% CI = [%.4f, %.4f] = [%.1f%%, %.1f%%]"
      % (lo, hi, lo * 100, hi * 100))
    P("  交叉核对：Beta(%d,%d) 2.5%% 分位 ≈ %.4f；Beta(%d,%d) 97.5%% 分位 ≈ %.4f"
      % (k, n - k + 1, lo, k + 1, n - k, hi))
    P()

    P("=" * 70)
    P("二、现行判据「修复关 >=3/5 复现、修复开 0/5」的可行性")
    P("=" * 70)
    P("  在 p = %.4f 下：" % p_hat)
    P("    P(>=3/5 复现) = %.4f   <-- 判据被满足的概率（功效）" % p_atleast(3, 5, p_hat))
    P("    P(0/5 复现)   = %.4f   <-- 一趟都没抓到，会被误判成「没这回事」"
      % pmf(0, 5, p_hat))
    P("    P(1/5)        = %.4f" % pmf(1, 5, p_hat))
    P("    P(2/5)        = %.4f" % pmf(2, 5, p_hat))
    P()
    P("  区间敏感性：")
    P("    p = CI 下界 %.4f（最不利） -> P(>=3/5) = %.4f"
      % (lo, p_atleast(3, 5, lo)))
    P("    p = CI 上界 %.4f（最有利） -> P(>=3/5) = %.4f"
      % (hi, p_atleast(3, 5, hi)))
    P()

    P("=" * 70)
    P("三、判据的另一侧是「弱判据」")
    P("=" * 70)
    P("  「修复开 0/5」只需 0 次复现。即使修复**完全无效**（p 不变），")
    P("  5 趟全不复现的概率 = %.4f  ⇒ 有 %.1f%% 概率假通过。"
      % ((1 - p_hat) ** 5, (1 - p_hat) ** 5 * 100))
    P("  加趟可压：")
    for N in (10, 15, 20, 25):
        P("    N=%2d  P(全不复现 | 修复无效) = %.4f" % (N, (1 - p_hat) ** N))
    P()

    P("=" * 70)
    P("四、固定趟数 N 下的功效（p = %.4f）" % p_hat)
    P("=" * 70)
    P("  %-5s %-16s %-14s %-14s" % ("N", "P(>=3 复现)", "P(0 复现)", "P(>=5 复现)"))
    for N in (5, 8, 10, 12, 15, 20, 25, 30, 40, 50):
        P("  %-5d %-16.4f %-14.4f %-14.4f"
          % (N, p_atleast(3, N, p_hat), pmf(0, N, p_hat), p_atleast(5, N, p_hat)))
    P()

    P("=" * 70)
    P("五、★ 推荐设计：按「复现事件数」配对，不按趟数配对")
    P("=" * 70)
    P("  理由：低复现率下，固定 5 趟的功效只有 4.5%，几乎必然失败；")
    P("        而 0/5 那一侧又有 36.7% 假通过。两边都不可靠。")
    P("  改法：修复关时一直跑到**攒够 r 次复现**为止（记录实际趟数 N_off），")
    P("        修复开时跑**同样 N_off 趟**，要求 0 次复现。")
    P()
    P("  r 次复现所需趟数（负二项，p = %.4f）：" % p_hat)
    P("  %-4s %-14s %-14s %-14s %-14s" % ("r", "期望趟数", "80% 分位", "90% 分位", "95% 分位"))
    for r in (3, 5):
        P("  %-4d %-14.1f %-14s %-14s %-14s"
          % (r, r / p_hat, negbinom_trips(p_hat, r, 0.80),
             negbinom_trips(p_hat, r, 0.90), negbinom_trips(p_hat, r, 0.95)))
    P()
    P("  ★ 这个设计的好处：0/N_off 那一侧的假通过概率随 N_off 自动收紧。")
    for r in (3, 5):
        Nexp = int(round(r / p_hat))
        P("    r=%d：期望 N_off≈%d  ->  P(修复无效却全不复现) = %.4f"
          % (r, Nexp, (1 - p_hat) ** Nexp))
    P()
    P("  ★ 代价：期望趟数从 5 涨到 %d（r=3）。这是复现率 18%% 的必然结果。"
      % int(round(3 / p_hat)))
    P()

    P("=" * 70)
    P("六、若必须限死 5 趟，唯一的出路是提高单趟复现率")
    P("=" * 70)
    P("  要让 P(>=3/5) >= 0.80，需要 p >= ?")
    p_req = 0.0
    while p_req <= 1.0 and p_atleast(3, 5, p_req) < 0.80:
        p_req += 0.0005
    P("    P(>=3/5) >= 80%%  =>  p >= %.3f（是当前 %.3f 的 %.1f 倍）"
      % (p_req, p_hat, p_req / p_hat))
    P("  含义：靠「加长战局 / 加大单位数 / 改收尾为 WM_CLOSE」把单趟命中率")
    P("        提到约 3 倍，5 趟判据才谈得上功效。否则 5 趟判据在统计上不成立。")

    text = "\n".join(out)
    print(text)
    out_path = Path(__file__).resolve().parent / OUTPUT_NAME
    out_path.write_text(text + "\n", encoding="utf-8")
    print()
    print("[written] %s" % out_path)


if __name__ == "__main__":
    main()
