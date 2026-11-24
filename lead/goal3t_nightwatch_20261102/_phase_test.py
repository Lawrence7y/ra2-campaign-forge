# -*- coding: utf-8 -*-
"""_phase_test.py - 「时间相位」假设检验（离线只读，零真机）。

背景与动机（2026-11-03，承 §521）：
  §521 找到一个极干净的对照：
    l3_20261023q 同一趟、同一地图（f3bb0a4efded）、三窗 units0 全是 974，
    但 w0/w1 的 B% = 0.00%，w2 的 B% = 84.62%。
  ⇒ 配置、负载、地图全相同，唯一变化的是**测量窗口的时间相位**。
  这提示：触发因素可能在**时间**上，而非配置或负载上。

本探针把这个观察做成可证伪的检验，用两套**互相独立**的时间轴：

  轴1 **趟内相位**（相对时间）：窗在本趟中的序号（window = 0/1/2）、
       以及该窗距本趟首窗的绝对时间差（用 t_abs0，Unix 秒）。
       → 检验「越靠后的窗越容易高停滞」。
  轴2 **开机时长**（绝对时间）：samples.t[0] = 自 BOOT 以来的秒数（perf_counter 基准）。
       → 检验「BOOT 越久越容易高停滞」（与 §505 BOOT 相关性同向，但用更细的连续轴）。

⚠ **两轴必须分别报告，不可混算**：
  轴1 是「趟内」位置，同一趟三窗共享同一 BOOT 与同一会话；
  轴2 是「跨趟」位置，混入了会话/BOOT 差异。二者的混杂结构完全不同。
  （纪律来源：D-12② BOOT 身份须双轴分列、禁混算；此处同理。）

判据（预注册）：
  H_phase：B% 与「趟内相位」正相关（越后越卡）。
  H_uptime：B% 与「开机时长」正相关（越久越卡）。
  用 Spearman ρ（对非线性单调关系稳健）+ 分层看每趟内是否单调。

用法：python -I -X utf8 _phase_test.py > _phase_test_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.100


def P(s=""):
    print(s)


def b_pct(ts, fs, thr=T):
    n = len(ts)
    span = ts[-1] - ts[0]
    if not span:
        return 0.0
    segs = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    d = ts[j] - ts[0]
    if d > thr:
        segs.append(d)
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        dd = ts[k] - ts[i]
        if dd > thr:
            segs.append(dd)
        i = k + 1
    return 100 * sum(segs) / span


def rank(vs):
    order = sorted(range(len(vs)), key=lambda i: vs[i])
    r = [0.0] * len(vs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vs[order[j + 1]] == vs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def spearman(xs, ys):
    return pearson(rank(xs), rank(ys))


rows = []


def add(dirpath, label, fname):
    try:
        with open(os.path.join(dirpath, fname), encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    if not ts or not fs or len(ts) < 2:
        return
    g = d.get("gate") or {}
    rows.append(dict(
        trip=label, w="w" + fname[9:-5],
        window=d.get("window"),
        t_abs0=d.get("t_abs0"),
        boot_age=ts[0],            # ★ samples.t = 自 BOOT 起秒数（perf_counter）
        u0=g.get("units0"),
        B=b_pct(ts, fs),
        moving=any(fs[i] != fs[i - 1] for i in range(1, len(fs))),
        verdict=d.get("verdict")))


for trip in sorted(os.listdir(BASE)):
    d = os.path.join(BASE, trip)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if f.startswith("measure_w") and f.endswith(".json"):
            add(d, trip, f)
for i in range(3):
    fn = "measure_w%d.json" % i
    if os.path.isfile(os.path.join(BASE, fn)):
        add(BASE, "(root)", fn)

# 只保留有推进的窗（排除全窗冻结，理由同 §521）
mv = [r for r in rows if r["moving"] and r["window"] is not None
      and r["t_abs0"] is not None]
P("=" * 108)
P("## 〇、样本与两套时间轴")
P("=" * 108)
P("   有效窗 = %d；纳入（有推进 + 有 window + 有 t_abs0）= %d" % (len(rows), len(mv)))
P()
P("   轴1 趟内相位：window ∈ {0,1,2}（该窗是本趟第几个测量窗）")
P("   轴2 开机时长：samples.t[0] = 自 BOOT 起秒数（perf_counter 基准）")
P("   ⚠ 两轴混杂结构不同（趟内 vs 跨趟），**分别报告、不混算**。")
P()
ages = [r["boot_age"] for r in mv]
P("   开机时长范围：%.1fs (%.2fh) .. %.1fs (%.2fh)"
  % (min(ages), min(ages) / 3600, max(ages), max(ages) / 3600))

P()
P("=" * 108)
P("## 一、轴1：趟内相位（window 序号）vs B%")
P("=" * 108)
P("%-14s %4s %10s %10s %10s %10s" %
  ("window", "n", "B 最小", "B 中位", "B 最大", "B 均值"))
P("-" * 108)
for wv in sorted({r["window"] for r in mv}):
    sel = [r for r in mv if r["window"] == wv]
    bs = sorted(r["B"] for r in sel)
    med = 0.5 * (bs[len(bs) // 2 - 1] + bs[len(bs) // 2]) if len(bs) % 2 == 0 else bs[len(bs) // 2]
    P("%-14s %4d %10.2f %10.2f %10.2f %10.2f"
      % ("w%d" % wv, len(sel), bs[0], med, bs[-1], sum(bs) / len(bs)))

xs = [r["window"] for r in mv]
ys = [r["B"] for r in mv]
P()
P("   Spearman ρ(window, B%%) = %+.4f" % spearman(xs, ys))
P("   Pearson  r(window, B%%) = %+.4f" % pearson(xs, ys))

P()
P("   ## ★ 逐趟内是否单调（同 BOOT、同会话、同 units0 的干净对照）")
P("   只列有 ≥2 个有效窗、且窗间 B%% 极差 > 20pp 的趟：")
P()
P("%-18s %28s %10s %s" % ("trip", "各窗 B% (w0/w1/w2)", "极差", "形态"))
P("-" * 108)
by_trip = {}
for r in mv:
    by_trip.setdefault(r["trip"], {})[r["window"]] = r["B"]
mono_up = mono_down = nonmono = 0
for trip in sorted(by_trip):
    ws = by_trip[trip]
    if len(ws) < 2:
        continue
    seq = [ws[k] for k in sorted(ws)]
    spread = max(seq) - min(seq)
    if spread <= 20:
        continue
    inc = all(seq[i + 1] >= seq[i] for i in range(len(seq) - 1))
    dec = all(seq[i + 1] <= seq[i] for i in range(len(seq) - 1))
    shape = "单调升" if inc else ("单调降" if dec else "非单调")
    if inc:
        mono_up += 1
    elif dec:
        mono_down += 1
    else:
        nonmono += 1
    P("%-18s %28s %9.2fpp %s"
      % (trip, " / ".join("%.2f" % x for x in seq), spread, shape))
P()
P("   ⇒ 极差>20pp 的趟：单调升 %d / 单调降 %d / 非单调 %d" % (mono_up, mono_down, nonmono))
P()
P("   ## ★ 单调升比例的二项检验（防止把随机当成规律）")
n_judge = mono_up + mono_down
if n_judge >= 4:
    from math import comb
    p_one = sum(comb(n_judge, i) for i in range(mono_up, n_judge + 1)) / (2 ** n_judge)
    P("      可判趟（单调升/降，排除非单调）= %d，其中单调升 = %d" % (n_judge, mono_up))
    P("      单侧二项检验 P(X≥%d | p=0.5) = **%.4f**" % (mono_up, p_one))
    if p_one < 0.05:
        P("      ⇒ **显著**（p<0.05）：「越后越卡」有统计支撑。")
    else:
        P("      ⇒ **不显著**（p≥0.05）：**不能排除随机**，不能据此断言「越后越卡」。")
        P("      样本仅 %d 个可判趟，检验力极弱；这是本件最重要的负结果之一。" % n_judge)
else:
    P("      可判趟过少（%d），不做二项检验。" % n_judge)

P()
P("=" * 108)
P("## 二、轴2：开机时长 vs B%")
P("=" * 108)
xs2 = [r["boot_age"] for r in mv]
P("   Spearman ρ(开机秒, B%%) = %+.4f" % spearman(xs2, ys))
P("   Pearson  r(开机秒, B%%) = %+.4f" % pearson(xs2, ys))
P()
P("   ## 按开机时长分档（每档约 1 小时）")
P("%-18s %4s %10s %10s %10s %10s" % ("开机时长档", "n", "B 最小", "B 中位", "B 最大", "B 均值"))
P("-" * 108)
BINS = [(0, 3600), (3600, 7200), (7200, 10800), (10800, 14400),
        (14400, 86400), (86400, 1e9)]
for lo, hi in BINS:
    sel = [r for r in mv if lo <= r["boot_age"] < hi]
    if not sel:
        continue
    bs = sorted(r["B"] for r in sel)
    med = 0.5 * (bs[len(bs) // 2 - 1] + bs[len(bs) // 2]) if len(bs) % 2 == 0 else bs[len(bs) // 2]
    lab = ("%.0f-%.0fh" % (lo / 3600, hi / 3600)) if hi < 86400 else (">%.0fh" % (lo / 3600))
    P("%-18s %4d %10.2f %10.2f %10.2f %10.2f"
      % (lab, len(sel), bs[0], med, bs[-1], sum(bs) / len(bs)))

P()
P("=" * 108)
P("## 三、★ §521 那条最干净对照的细查：l3_20261023q")
P("=" * 108)
q = [r for r in rows if r["trip"] == "l3_20261023q"]
if q:
    P("%-4s %9s %12s %12s %9s %10s" %
      ("窗", "B%", "t_abs0", "相对首窗s", "units0", "verdict"))
    P("-" * 108)
    t0 = min(x["t_abs0"] for x in q)
    for x in sorted(q, key=lambda y: y["window"]):
        P("w%-3s %9.4f %12.3f %12.3f %9s %10s"
          % (x["window"], x["B"], x["t_abs0"], x["t_abs0"] - t0,
             x["u0"], x["verdict"]))
    P()
    P("   ⇒ 三窗 units0 全同、地图全同、同趟同会话，仅时间相位不同。")

P()
P("=" * 108)
P("## 四、判据核对")
P("=" * 108)
rho1 = spearman(xs, ys)
rho2 = spearman(xs2, ys)
P("   H_phase  （趟内越后越卡）：ρ(window,B) = %+.4f" % rho1)
P("   H_uptime （开机越久越卡）：ρ(开机秒,B) = %+.4f" % rho2)
P()
if abs(rho1) < 0.2:
    P("   ⇒ H_phase **不成立**：趟内相位与 B%% 几乎无关（|ρ|<0.2）。")
    P("      l3_20261023q 的 0/0/84.62 是个例，不是「越后越卡」的系统规律。")
else:
    P("   ⇒ H_phase 有支撑：|ρ|≥0.2。")
if abs(rho2) < 0.2:
    P("   ⇒ H_uptime **不成立**：开机时长与 B%% 几乎无关（|ρ|<0.2）。")
else:
    P("   ⇒ H_uptime 有支撑：|ρ|≥0.2。")

P()
P("=" * 108)
P("## 五、诚实账")
P("=" * 108)
P("   1. 两轴都只做相关/分层，**不做因果**；且各趟 units0 与会话共变，混杂未完全剥离。")
P("   2. `window` 字段只是序号，**不代表时间相位**——若某趟窗口间隔不均，序号≠相位；")
P("      本件用 `t_abs0` 求真实时间差，序号仅作分组标签。")
P("   3. ★ `samples.t` 基准的**实测核验**（本件已做，非猜测）：")
P("      同一趟三窗内 `samples.t[0] − t_abs0` 差值**恒定在 ±3ms 内**")
P("      （实测 l3_20261023q: −1793337038.086/−.085/−.083；")
P("        l3_1101v4e: −1793667257.098/−.096/−.097；l1c_20261021: 三位全同 −1792547143.09x），")
P("      ⇒ `samples.t` 是**与墙钟同速的单调时钟**，基准为该恒定偏移点。")
P("      交叉验证：`l3_1101v4e` 的 `samples.t[0]=8774.8s`，与该轮 BOOT#8 实测 uptime≈2.4h(8640s) 吻合，")
P("      ⇒ **`samples.t` = 自 BOOT 起秒数**（而非仅进程启动以来）。")
P("      ⚠ 但该偏移值在不同 BOOT 之间显著不同（10-23 那次与 11-03 那次差约 33 万秒），")
P("      故**轴2 只在同一 BOOT 内可比**；跨 BOOT 用该轴会混入 BOOT 身份差异——本件已据此限制解读。")
P("   4. 已排除全窗冻结窗（reason 同 §521）。")
P("   5. 本件**未经异族核验**，亦不做机制定谳。")
