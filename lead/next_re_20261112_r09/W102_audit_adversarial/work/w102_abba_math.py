#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
W102 §B · ABBA 设计审计的定量部分

四件事，全部可复算：
  1. 3 区组判据的功效：假设真实 d = 常数 dtrue、每段测量噪声 σ 独立同分布，
     算「3 个 d_block 同号」的概率 = P(|多数方向一致|)。给出 dtrue/σ 扫描表。
     **这不是统计推断，是判据的概率学性质**；假设写在注释里。
  2. 非单调趋势下 ABBA 的反例：用**实测相位曲线**（W98 的 g_far / g_near 逐 10 s rate）
     构造 B 段的"形状"，令 A 与 B 的**期望完全相同**（真实 d = 0），看 ABBA 判出什么。
  3. 判据阈值 0.5 pp 与已知噪声的比值。
  4. 预热 10 s 够不够：用 N 段边界实测的局部 rate 去算"边界污染的半衰距离"。
"""
import json, os, random, itertools

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


S = {t: load_s(t) for t in
     ["trip_g_idle_r1", "trip_g_idle_r2", "trip_g_near_r1", "trip_g_near_r2",
      "trip_g_far_r1", "trip_g_far_r2"]}

print("=" * 108)
print("W102 §B-1 · 3 区组的判据功效：P(3 个 d_block 同号)")
print("=" * 112)
print()
print("模型假设（写死，不事后调）：")
print("  · 真实观测器效应 d_true 为常数（不随相位变）")
print("  · 每个区组内 d_block = mean(A)-mean(B) 的测量误差 e_k ~ iid 零均值，")
print("    方差 σ^2；区组间独立。")
print("  · 判据：3 个 d_block 符号一致 ⇒ 判\"扰动在预算内\"（若均值 <= 0.5 pp）")
print("  · 只用正态/均匀两种最简单形态试算，不做区间估计。")
print()
print("P(3 点同号) 与 d_true/σ 的关系（零均值对称分布下）：")


def p_same_sign(r, trials=200000, seed=11):
    """r = d_true/sigma。返回 P(3 个同号)。"""
    rng = random.Random(seed)
    hit = 0
    for _ in range(trials):
        v = [r + rng.gauss(0, 1) for _ in range(3)]
        s = [1 if x >= 0 else -1 for x in v]
        if s[0] == s[1] == s[2]:
            hit += 1
    return hit / trials


print("{:>10}{:>14}{:>14}{:>14}".format("d_true/σ", "P(3点同号)", "P(判预算内)", "P(判超预算)"))
for r in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
    p = p_same_sign(r)
    # 判"预算内"需要 3 点同号 **且** 均值 <= 0.5 pp；这里只看方向上界，
    # 阈值那一步单独在 §B-3 算（同一模型）。
    print("{:>10.1f}{:>14.3f}{:>14.3f}{:>14.3f}".format(r, p, p if r >= 0 else 0.0, 1 - p))

print()
print("  ⇒ 即使 d_true = 0（观测器完全无扰动），仍有 25.0% 的概率 3 点同号 ——")
print("     也就是说\"3 点同号\"这个条件在 d_true=0 时有 1/4 的机会把**任何**两臂差异")
print("     误判成方向一致。反之，d_true 只有到 ~2σ 才能把\"3 点不同号\"的概率压到 5% 以下。")

print()
print("=" * 108)
print("W102 §B-3 · 判据阈值 0.5 pp vs 已知噪声")
print("=" * 108)
noise = {
    "参照臂(g_idle) 运行间极差": 0.6249,
    "紧贴臂(g_near) 运行间极差": 0.2394,
    "交战臂(g_far)  运行间极差": 4.9064,
    "交战臂历史极差(§626-2, 3 趟)": 2.6,
}
for k, v in noise.items():
    print("  {:<32} = {:>7.4f} pp   → 0.5/极差 = {:.3f}".format(k, v, 0.5 / v))
print()
print("  若一个 60 s 段的测量噪声（每段独立）取参照臂半极差 = {:.4f} pp，".format(0.6249 / 2))
print("  则 d_block 的噪声 ≈ {:.4f} pp（ABBA 区组内 4 段，A-B 各 2 段）。".format(
    0.6249 / 2 * (2 ** 0.5)))
print("  即：光\"段间\"噪声就已经是 0.5 pp 判据阈的 {:.2f} 倍。".format(
    (0.6249 / 2 * 2 ** 0.5) / 0.5))
print()
print("  用实测 60 s 段 rate 直接算段间散布（同一 cell 同一趟，段位置 0/30/60/90）：")
for t in ["trip_g_idle_r1", "trip_g_idle_r2"]:
    vals = [rate(slice_t(S[t], lo, lo + 60)) for lo in (0, 30, 60, 90)]
    vals = [v for v in vals if v is not None]
    print("    {:<18} 4 个 60 s 段: {}  极差 = {:.4f} pp".format(
        t, " / ".join("{:.3f}".format(v) for v in vals), max(vals) - min(vals)))

print()
print("=" * 108)
print("W102 §B-2 · 非单调趋势下的 ABBA 反例（用实测相位曲线构造）")
print("=" * 108)
print()
print("构造方式（不打乱任何实测数据）：")
print("  · 用 W98 g_far 的逐 30 s 实测 rate 作为\"被测场景\"的时间走势（这是本批里唯一的")
print("    全 Hunt 长曲线，ABBA 的 C6 场景与之同族）。")
print("  · 令 A 段与 B 段的**期望**完全相同（真实 d = 0）：即 B 段 = A 段同位置的值。")
print("  · ABBA 的四个段若落在不同的相位位置，则 mean(A) ≠ mean(B)，差值就是**虚假 d**。")
print()
far = S["trip_g_far_r2"]
print("  g_far_r2 逐 15 s 实测 rate（作为趋势函数 f(t)）：")
curve = []
for lo in range(0, 150, 15):
    v = rate(slice_t(far, lo, lo + 15))
    curve.append(v)
    print("    {:>3}-{:>3} s : {:>8.3f} %".format(lo, lo + 15, v))

# 用真实记录做 A/B 交错，比较"ABBA"与"ABBA 反转(BAAB)"和"真 ABAB"
def curve_at(t, table, step=20.0):
    idx = min(len(table) - 1, int(t // step))
    return table[idx]

near = S["trip_g_near_r1"]
print("  用 g_near_r1 的 30 s 分辨率实测曲线做数值实验（W102 勘误：该曲线**不是单调的**，")
print("    它是\"相位驱动\"的衰减，靠前的段远高于靠后的段，且 120-150 s 有回弹）。")
print("    真实 d = 0（A、B 是同一场景），只有段的位置不同：")
for order_name, order in [("ABBA", "ABBA"), ("BAAB", "BAAB"), ("ABAB", "ABAB")]:
    ds = []
    for blk in range(3):
        t0 = blk * 4 * 30.0
        A, B = [], []
        for k, tag in enumerate(order):
            lo = t0 + k * 30.0
            v = rate(slice_t(near, lo, lo + 30.0))
            if v is None:
                continue
            (A if tag == "A" else B).append(v)
        if A and B:
            ds.append(sum(A) / len(A) - sum(B) / len(B))
    print("      {:<6} d_block = {}   均值 = {:>+8.3f} pp  （真实 d = 0）".format(
        order_name, " / ".join("{:+.3f}".format(x) for x in ds),
        sum(ds) / len(ds) if ds else float("nan")))

print()
print("  ⇒ 关键事实：**实测曲线的衰减速度远快于\"每区组 240 s\"这个尺度**，")
print("     所以区组 1 与区组 2 的 A/B 内差是**数量级不同**的量。ABBA 只能抵消")
print("     \"全小区组内 A 与 B 位置的平均效应相同\"那一类趋势，抵消不了\"同区内 B 段")
print("     整体落在 A 段后面\"这一阶。区组内顺序 ABBA 的 A 位置是 1、4，B 是 2、3。")
print()
print("  把\"位置效应\"隔离出来的对照实验（同一实测曲线，只改顺序）：")
seg4 = []
for lo in (0, 30, 60, 90):
    v = rate(slice_t(near, lo, lo + 30.0))
    seg4.append(v)
print("    实测四段（0/30/60/90 s 起，各 30 s）= " + " / ".join("{:.3f}".format(x) for x in seg4))
for order in ("ABBA", "BAAB", "ABAB", "BBAA", "AABB"):
    A = [seg4[k] for k, t in enumerate(order) if t == "A"]
    B = [seg4[k] for k, t in enumerate(order) if t == "B"]
    print("      {:<6} mean(A)={:>8.3f} mean(B)={:>8.3f} d={:>+8.3f} pp".format(
        order, sum(A) / len(A), sum(B) / len(B),
        sum(A) / len(A) - sum(B) / len(B)))
print()
print("  ⇒ 同一组真实数据、真实 d=0，仅**改段序**，d 就在这个范围里跑：")
allv = []
for order in ("ABBA", "BAAB", "ABAB", "BBAA", "AABB"):
    A = [seg4[k] for k, t in enumerate(order) if t == "A"]
    B = [seg4[k] for k, t in enumerate(order) if t == "B"]
    allv.append(sum(A) / len(A) - sum(B) / len(B))
print("      d ∈ [{:+.3f}, {:+.3f}] pp，跨度 {:.3f} pp —— 这是\"段序选择\"带来的虚假 d。".format(
    min(allv), max(allv), max(allv) - min(allv)))
print("      注意 ABBA 落在 {:+.3f}，AABB 落在 {:+.3f}：ABBA 并不是天然\"最优\"，".format(
    allv[0], allv[4]))
print("      它只是在**趋势为线性**时最小化位置偏差；本曲线在 0-120 s 内近似指数衰减，")
print("      线性性不成立。")

print()
print("  非单调趋势的最小反例（= 本卡要的\"具体反例构造\"）：")
print("    假设真实观测器效应 d = 0，唯一的时间结构是战局的\"升-降-升\"：")
print("      决策前的行军段低，接触初期冲高，单位死亡后回落，残余战斗再小抬。")
print("    用实测 g_far_r2 的数据可以读出这个形状（见上面逐 15 s 表：65.99 → 17.92，")
print("    且 120-135 s 相对 105-120 s 有 +0.42 pp 的回升）。")
print("    取段值表 [低, 高, 中, 低]，A/B 只由段位置决定：")
for name, seg in [("升-降-平(20/60/35/20)", [20.0, 60.0, 35.0, 20.0]),
                  ("驼峰落在段2(20/20/60/20)", [20.0, 20.0, 60.0, 20.0]),
                  ("谷-峰-谷-峰(20/60/20/60)", [20.0, 60.0, 20.0, 60.0]),
                  ("实测仿形(65/45/35/25)", [65.0, 45.0, 35.0, 25.0])]:
    A = [seg[k] for k, t in enumerate("ABBA") if t == "A"]
    B = [seg[k] for k, t in enumerate("ABBA") if t == "B"]
    A2 = [seg[k] for k, t in enumerate("BAAB") if t == "A"]
    B2 = [seg[k] for k, t in enumerate("BAAB") if t == "B"]
    print("      形状 {:<24} ABBA d={:>+7.2f}  BAAB d={:>+7.2f}  ABAB d={:>+7.2f}".format(
        name, sum(A) / 2 - sum(B) / 2, sum(A2) / 2 - sum(B2) / 2,
        (seg[0] + seg[2]) / 2 - (seg[1] + seg[3]) / 2))
print()
print("    **结论（反例）**：形状 20/20/60/20（单驼峰恰好落在 B 段位置）时，")
print("      ABBA 给出 d = -20.00 pp，BAAB 给出 +20.00 pp，而真实 d = 0。")
print("      ABBA 与 BAAB 符号相反这一事实本身就是\"无法分辨\"的证据 ——")
print("      但**协议只跑一次 ABBA**，它看不到这个对照。")


def _unused_old_block():
    pass

# 非单调构造：取 g_far_r2 实测曲线（0-150 单调降），把它镜像拼成"先升后降"
mono = []
for lo in range(0, 120, 30):
    mono.append(rate(slice_t(S["trip_g_far_r2"], lo, lo + 30)))
print("    基曲线 g_far_r2 30 s 段: " + " / ".join("{:.2f}".format(x) for x in mono))
# 驼峰曲线：A 段在谷，B 段在峰
tent = [mono[0], mono[1], mono[0] + 25.0, mono[0]]   # 人为驼峰
print("    非单调曲线（人为驼峰，仅用于反例）: " + " / ".join("{:.2f}".format(x) for x in tent))
for order in ["ABBA", "BAAB"]:
    A = [tent[k] for k, tag in enumerate(order) if tag == "A"]
    B = [tent[k] for k, tag in enumerate(order) if tag == "B"]
    print("      {:<6} mean(A)={:>8.3f}  mean(B)={:>8.3f}  d_block={:>+8.3f} pp".format(
        order, sum(A) / len(A), sum(B) / len(B),
        sum(A) / len(A) - sum(B) / len(B)))

print()
print("  ⇒ 具体反例（ABBA 给出虚假 d 而真实 d=0）：")
print("     设趋势为\"升-降-升\"三段，段值 20 / 60 / 20 / ...，真实观测器效应恒为 0。")
for name, seg in [("升-降-升", [20.0, 60.0, 20.0, 20.0]),
                  ("驼峰正中对齐", [20.0, 20.0, 60.0, 20.0]),
                  ("谷-峰-谷-峰", [20.0, 60.0, 20.0, 60.0])]:
    A = [seg[k] for k, t in enumerate("ABBA") if t == "A"]
    B = [seg[k] for k, t in enumerate("ABBA") if t == "B"]
    d = sum(A) / len(A) - sum(B) / len(B)
    A2 = [seg[k] for k, t in enumerate("BAAB") if t == "A"]
    B2 = [seg[k] for k, t in enumerate("BAAB") if t == "B"]
    d2 = sum(A2) / len(A2) - sum(B2) / len(B2)
    print("      形状 {:<12} 段值 {:<22} ABBA d={:>+7.2f}  BAAB d={:>+7.2f}".format(
        name, str(seg), d, d2))
print()
print("      其中「升-降-升」= 20/60/20/20 时 ABBA 给出 d = {:+.2f} pp，真实 d = 0。".format(
    (sum([20.0, 20.0]) / 2) - (sum([60.0, 20.0]) / 2)))

print()
print("=" * 108)
print("W102 §B-4 · 预热 10 s 够不够：用最陡的实测斜率算")
print("=" * 108)
near1 = S["trip_g_near_r1"]
print("  g_near_r1 前 30 s 的逐 2 s rate（这是工程上最陡的边界）：")
prev = None
for lo in range(0, 32, 2):
    v = rate(slice_t(near1, lo, lo + 2))
    if v is None:
        continue
    print("    {:>3}-{:>3} s : {:>8.3f} %  {}".format(
        lo, lo + 2, v, "" if prev is None else "  斜率 {:+.2f} pp/2s".format(v - prev)))
    prev = v
print()
print("  ⇒ 用 0-10 s 与 10-20 s 算\"丢 10 s 预热\"后残留的偏差：")
v0 = rate(slice_t(near1, 0, 10))
v10 = rate(slice_t(near1, 10, 20))
print("     0-10 s = {:.3f} %   10-20 s = {:.3f} %   差 = {:+.3f} pp".format(v0, v10, v0 - v10))
print("     若段长 60 s 且丢前 10 s，则该段残留的边界偏差 ≈ (v0-v10) × (10/50) = {:.3f} pp".format(
    (v0 - v10) * (10.0 / 50.0)))
print()
print("  另：本批实测 max_gap_ms（样本最大间隔，即 python 侧卡顿）见 A_recompute.txt §A-2，")
print("      为 106.95–372.94 ms。也就是说观测器自己每段最多会打 ~0.37 s 的洞。")
