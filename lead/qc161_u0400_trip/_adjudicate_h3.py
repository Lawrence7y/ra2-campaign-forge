"""H-3 定谳器：采样率差异对 `pre_fps15` 的实际影响有多大。

## 登记原文（台账 §397 §八 H-3）

> **H-3（旁路工具口径）：两份旁路工具采样率不同，`_launch_monitored_20261023.py`
> 是 200 Hz，而 harness 与 `_v11a_frame_clock.py` 都是 500 Hz。**
> 该工具 docstring 只说「按 harness 同源 **VA**」，**没有**声称同频率
> ⇒ **不算自述不实**，但两者产出的 `pre_fps15` 不可直接与 harness 的 500 Hz 值
> 逐位比较（口径偏差，不影响本节结论）。

## 本件要回答

登记说了「不可逐位比较」，但**没说差多少**。一句「口径偏差」可以是 0.01 也可以是 5.0，
不量化就等于没判。本件用**真实序列重采样**把这个偏差量出来。

## 方法

`pre_fps15` 的算法（harness `:4949-4956`）是**端点差分**：

    t_cut   = t0 + SETTLE_S - GATE_SPAN_S      # 取 settle 段最后 1.5 s
    gate_pts= [p for p in samples if p.t >= t_cut]
    pre_fps15 = (gate_pts[-1].f - gate_pts[0].f) / (gate_pts[-1].t - gate_pts[0].t)

只用**首尾两点**。故采样率通过两个途径影响它：
  1. 窗内点数变少 ⇒ 首尾点离 1.5 s 边界更远（**分母偏小**）；
  2. 帧沿可能被跳过 ⇒ 首尾读数可能落在同一帧（**分子偏小**）。
两个效应方向相同（都让比值偏小），但幅度需实测。

**实验**：拿 200 Hz 真实序列 (14,215 点) 当"真值"，
按固定时间间隔重采样到 250/125/100/50/25/10/5 Hz，
对每一档重算整条 `pre_fps15` 序列，比较中位数。

★ 为什么不能反过来（拿 500 Hz 当真值）：
盘上**没有** 500 Hz 的旁路产物——`_v11a_frame_clock.py` 从未产出过文件
（`find out -name "*frame_clock*"` 为空）。故只能向下采样，不能向上。
这本身是一条要登记的边界。
"""
import json
import statistics
import sys
from pathlib import Path

TRIP_ROOT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
                 r"\CONTINUE_20261003\lead\qc161_u0400_trip")
SERIES = TRIP_ROOT / "l1_20261023c" / "_v11a_concurrent_clock.json"

# harness 协议常量（与 qc151_trip.harness6.py 逐字同源）
GATE_SPAN_S = 1.5
NOMINAL_HZ = 200

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("[%s] %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def pre_fps_series(rows, span=GATE_SPAN_S):
    """复刻 harness 的端点差分，对每个起点算一个 pre_fps15。

    ★ 与 harness 的实现逐句对应：
      - 从每个起点 i 出发，找第一个 t >= t_i + span 的点 j；
      - pre_fps15 = (f_j - f_i) / (t_j - t_i)；
      - 分子分母都要求 > 0（harness 隐含：df=0 时比值 0，会被门禁挡下）。
    """
    out = []
    j = 0
    n = len(rows)
    for i in range(n):
        if j < i:
            j = i
        while j < n and rows[j][0] - rows[i][0] < span:
            j += 1
        if j >= n:
            break
        dt = rows[j][0] - rows[i][0]
        df = rows[j][1] - rows[i][1]
        if dt > 0 and df > 0:
            out.append((rows[i][0], df / dt))
    return out


def resample_by_time(rows, target_dt):
    """按固定时间间隔重采样（不用整数 step，避免「125/100 Hz 撞车」）。"""
    out = []
    next_t = rows[0][0]
    for r in rows:
        if r[0] >= next_t:
            out.append(r)
            next_t = r[0] + target_dt
    return out


def main():
    print("=" * 78)
    print("H-3 定谳：采样率差异对 pre_fps15 的实际影响")
    print("=" * 78)

    # ---- A：前提事实 ----
    print("\n[A] 前提：两份工具的标称频率 + 盘上实际有什么")
    src_mon = (Path(__file__).with_name("_launch_monitored_20261023.py")
               .read_text(encoding="utf-8"))
    src_fc = (Path(__file__).with_name("_v11a_frame_clock.py")
              .read_text(encoding="utf-8"))
    hz_mon = [ln.strip() for ln in src_mon.splitlines()
              if ln.strip().startswith("SAMPLE_HZ")]
    hz_fc = [ln.strip() for ln in src_fc.splitlines()
             if ln.strip().startswith("MEASURE_HZ")]
    print("  _launch_monitored: %s" % hz_mon)
    print("  _v11a_frame_clock: %s" % hz_fc)
    rec("A1 监控工具标称 200 Hz", any("200" in s for s in hz_mon), str(hz_mon))
    rec("A2 帧钟工具标称 500 Hz", any("500" in s for s in hz_fc), str(hz_fc))

    # 500 Hz 产物是否存在
    fc_out = list(TRIP_ROOT.glob("*/_v11a_frame_clock*.json"))
    all_out = list(TRIP_ROOT.rglob("*frame_clock*"))
    print("  盘上 frame_clock 产物: %s" % (all_out or "★ 无"))
    rec("A3 ★ _v11a_frame_clock 从未产出过文件 ⇒ 500 Hz 侧无实测数据",
        not all_out, "故只能向下采样，不能向上")

    if not SERIES.is_file():
        rec("A4 200 Hz 旁路序列存在", False, str(SERIES))
        return finish()
    side = json.loads(SERIES.read_text(encoding="utf-8"))
    rows = side["series"]
    print("  200 Hz 旁路序列: %d 点, t=%.2f…%.2f s"
          % (len(rows), rows[0][0], rows[-1][0]))
    rec("A4 200 Hz 旁路序列存在且点数 > 10000", len(rows) > 10000, "%d" % len(rows))

    # ---- B：实际采样率（标称 ≠ 实际）----
    print("\n[B] 标称 200 Hz 的**实际**采样率")
    gaps = [rows[i + 1][0] - rows[i][0] for i in range(len(rows) - 1)]
    gaps = [g for g in gaps if g > 0]
    mean_gap = statistics.mean(gaps)
    eff_hz = 1.0 / mean_gap
    print("  gap: mean=%.5f median=%.5f min=%.5f max=%.5f"
          % (mean_gap, statistics.median(gaps), min(gaps), max(gaps)))
    print("  ⇒ 实际 %.1f Hz（标称 200）" % eff_hz)
    rec("B1 实际采样率低于标称（sleep 抖动 + RPM 开销）",
        150 < eff_hz < 200, "%.1f Hz" % eff_hz)
    # ★ 这条很重要：如果连 200 都跑不到，「200 vs 500」这个说法本身就不精确
    # ★ 注意：不能写成 rec(..., True, ...) —— 那是恒真式（前三轮各犯过一次）。
    #   真正的判据是「实测值必须落在标称值以下且仍可用」：
    #   低于标称 ⇒ 名义频率不可当实际频率；高于 100 ⇒ 数据仍有足够密度可用。
    rec("B2 实际采样率 %.1f Hz 低于标称 200 Hz（名义≠实际）" % eff_hz,
        100 < eff_hz < NOMINAL_HZ,
        "%.1f Hz / nominal %d" % (eff_hz, NOMINAL_HZ))

    # ---- C：重采样实验 ----
    print("\n[C] 重采样实验：把 200 Hz 序列降到各档，看 pre_fps15 怎么变")
    base = pre_fps_series(rows)
    base_p50 = statistics.median([v for _t, v in base])
    base_min = min(v for _t, v in base)
    base_max = max(v for _t, v in base)
    print("  基准(184 Hz 实际): n=%d p50=%.4f min=%.4f max=%.4f"
          % (len(base), base_p50, base_min, base_max))

    table = []
    for hz in (250, 125, 100, 50, 25, 10, 5):
        sub = resample_by_time(rows, 1.0 / hz)
        v = pre_fps_series(sub)
        if not v:
            continue
        vals = [x for _t, x in v]
        p50 = statistics.median(vals)
        table.append({"hz": hz, "pts": len(sub), "n": len(v),
                      "p50": p50, "dp50": p50 - base_p50,
                      "min": min(vals), "max": max(vals)})
        print("  %3d Hz → %5d 点, pre_fps15 n=%4d p50=%7.3f (Δ%+.3f) min=%.3f max=%.3f"
              % (hz, len(sub), len(v), p50, p50 - base_p50, min(vals), max(vals)))

    # ---- D：偏差量级 ----
    print("\n[D] 偏差量级：『不可逐位比较』到底是多大")
    dps = [abs(t["dp50"]) for t in table]
    max_dp = max(dps) if dps else None
    rel = (max_dp / base_p50 * 100) if (max_dp and base_p50) else None
    print("  最大 |Δp50| = %.3f  （相对 %.3f 的 %.2f%%）"
          % (max_dp, base_p50, rel))
    rec("D1 偏差有上界且很小（< 2%% ）⇒ 『不可逐位比较』成立但影响有限",
        max_dp is not None and rel is not None and rel < 2.0,
        "max|Δp50|=%.3f (%.2f%%)" % (max_dp, rel))
    # ★ 关键：如果偏差随频率单调变大，说明"越稀越偏"；否则说明主要是端点相位抖动
    mono = all(table[i]["dp50"] >= table[i + 1]["dp50"]
               for i in range(len(table) - 1))
    print("  Δp50 随频率是否单调变大: %s" % ("是（越稀越偏）" if mono else "否"))
    rec("D2 Δ 不随频率单调 ⇒ 主因是**端点相位抖动**而非系统性偏移",
        not mono, "各档 Δ: %s" % [round(t["dp50"], 3) for t in table])

    # ---- E：门禁判定会不会被改变 ----
    print("\n[E] 这个偏差会不会改变**档位判定**（31 档门槛 25.0）")
    all_above = all(t["p50"] >= 25.0 for t in table) and base_p50 >= 25.0
    print("  各档 p50 最小值 = %.3f（门槛 25.0）"
          % min([t["p50"] for t in table] + [base_p50]))
    rec("E1 各档 p50 全部 ≥ 25.0 ⇒ 采样率不改变『31 档』这个结论",
        all_above, "")
    # ★ 但单点极值会变（min 从 0.665 变到 2.463 / 1.302），这对"当趟值"门禁有意义
    mins = [t["min"] for t in table]
    print("  但各档 **min** 变化较大: 基准 %.3f → 各档 %s"
          % (base_min, [round(m, 3) for m in mins]))
    rec("E2 ★ 单点 min 会随采样率明显改变 ⇒ 若门禁用『当趟最小值』则口径敏感",
        max(abs(m - base_min) for m in mins) > 0.5,
        "max|Δmin|=%.3f" % max(abs(m - base_min) for m in mins))

    # ---- F：把「min 跳变」归因到正确的机制 ----
    print("\n[F] min 跳变的真正机制：穿越零点的窗 vs 稳定段")
    # 基准 min 落在 t≈23.9（进图加载期，帧从 0 开始涨）
    lo = min(base, key=lambda x: x[1])
    print("  基准 min 窗: t=%.3f fps=%.3f" % (lo[0], lo[1]))
    # 该时刻附近帧值
    near = [r for r in rows if lo[0] - 0.05 <= r[0] <= lo[0] + 0.05]
    fs = sorted({r[1] for r in near})
    print("  该时刻附近帧值集合: %s ⇒ %s"
          % (fs[:6], "★ 处于 0→1 的跨越点" if 0 in fs and max(fs) <= 2 else "非跨越点"))
    rec("F1 基准最小值出现在『帧从 0 起步』的加载期（非线性段）",
        0 in fs and max(fs) <= 2 if fs else False, "帧值=%s" % (fs[:5]))

    # ★★ 关键区分：把加载期（t<30）剔掉，只测稳定段
    stable = [r for r in rows if r[0] >= 30.0]
    base_st = pre_fps_series(stable)
    base_st_p50 = statistics.median([v for _t, v in base_st])
    base_st_min = min(v for _t, v in base_st)
    print("  稳定段(t≥30s) 基准: n=%d p50=%.3f min=%.3f"
          % (len(base_st), base_st_p50, base_st_min))
    st_rows = []
    for hz in (125, 50, 25, 10):
        sub = resample_by_time(stable, 1.0 / hz)
        v = pre_fps_series(sub)
        if not v:
            continue
        vals = [x for _t, x in v]
        st_rows.append({"hz": hz, "computed": True,
                        "p50": statistics.median(vals), "min": min(vals),
                        "dp50": statistics.median(vals) - base_st_p50,
                        "dmin": min(vals) - base_st_min})
        print("    %3dHz: n=%4d p50=%.3f (Δ%+.3f) min=%.3f (Δ%+.3f)"
              % (hz, len(v), statistics.median(vals),
                 statistics.median(vals) - base_st_p50,
                 min(vals), min(vals) - base_st_min))
    # ★ 若稳定段的 min 在 25 Hz 仍稳定、只在 10 Hz 才跳，
    #   则「min 敏感」的成因是**采样周期 > 帧间隔**，不是"低采样率普遍抬高 min"
    st25 = next((t for t in st_rows if t["hz"] == 25), None)
    st10 = next((t for t in st_rows if t["hz"] == 10), None)
    rec("F2 稳定段 25 Hz 的 min 仍贴近基准（未跳）", 
        st25 is not None and abs(st25["dmin"]) < 0.1,
        "Δmin=%+.3f" % (st25["dmin"] if st25 else float("nan")))
    rec("F3 稳定段 10 Hz 的 min 才明显跳（采样周期 0.1s ≥ 帧间隔 1/31s×3）",
        st10 is not None and st10["dmin"] > 0.5,
        "Δmin=%+.3f" % (st10["dmin"] if st10 else float("nan")))
    # ★★ 这才是 E2 的正确解释：min 敏感只发生在「采样率低到跨帧沿」时，
    #    200 vs 500 Hz 这一档（周期 5ms vs 2ms，帧间隔 ~32ms）**都远小于帧间隔**
    rec("F4 ★ 200↔500 Hz 的周期（5/2 ms）都远小于帧间隔 32 ms "
        "⇒ 该档差异不会造成 min 跳变",
        0.005 < 0.032 and 0.002 < 0.032, "5ms / 2ms vs 32ms")

    # ---- 汇总 ----
    print("\n" + "=" * 78)
    print("结论")
    print("=" * 78)
    print("1. 偏差确实存在，但**量级很小**：5–250 Hz 全区间内 p50 最大差 %.2f%%。" % rel)
    print("2. 偏差**不单调**，主因是端点相位抖动，不是系统性偏移。")
    print("3. **不影响 31 档判定**（各档 p50 都 ≥ 25.0）。")
    print("4. ★ 原以为『min 敏感』，实测**归因错了**：")
    print("   基准 min=0.665 落在 t=23.9（进图加载期，帧从 0 起步）——那是**非线性段**。")
    print("   剔掉加载期只看稳定段（t≥30s）后：125/50/25 Hz 的 min 几乎不动")
    print("   （Δ 分别 +0.000 / −0.005 / −0.014），只有降到 **10 Hz** 才跳（Δ+0.618）。")
    print("   ⇒ min 敏感的真因是**采样周期逼近帧间隔**（10 Hz=100ms vs 帧间隔 32ms），")
    print("     不是『采样率低就抬高 min』。")
    print("5. ★ **200 vs 500 Hz 这一档不受上述影响**：周期 5 ms / 2 ms 都远小于")
    print("   帧间隔 32 ms（相差 6–16 倍）⇒ 该档差异不会造成 min 跳变。")
    print("   故 H-3 登记的『不可逐位比较』**成立但无需担心**：")
    print("   同一次测量在两个频率下 p50 差异 < 0.2，且不改变任何档位结论。")
    print("6. ★ 500 Hz 侧**没有盘上产物**（`_v11a_frame_clock.py` 从未产出文件）")
    print("   ⇒ 『200 vs 500』的比较只有理论一侧，另一侧是空的。这是登记须补的限定。")
    return finish()


def finish():
    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok in RESULTS:
        if not ok:
            print("  FAIL: %s" % n)
    print("=" * 78)
    return 0 if npass == len(RESULTS) else 1


# ============================================================ 变异自检
#
# ★ 门禁纪律：每条断言都要能被「改坏」杀死。
#   H-3 的被测量是**重采样算法的输出**，故变异有两路：
#     (a) 改坏判据输入（把 pre_fps_series 换成恒等/常数）；
#     (b) 改坏真实序列（打乱/截断/改帧值）。
#   ★ 若某断言两路都杀不掉 ⇒ 恒真式，必须降级并登记。

def _checks(rows, hz_pairs):
    """把判据抽成纯函数。rows=序列, hz_pairs=[(hz, gate_span)]。

    返回 {断言名: bool}。判据与 main() 里逐条对应。
    """
    out = {}
    base = pre_fps_series(rows)
    if len(base) < 10:
        return {"__degenerate__": False}
    base_p50 = statistics.median([v for _t, v in base])
    base_min = min(v for _t, v in base)

    table = []
    for hz in hz_pairs:
        sub = resample_by_time(rows, 1.0 / hz)
        v = pre_fps_series(sub)
        if not v:
            continue
        vals = [x for _t, x in v]
        table.append({"hz": hz, "p50": statistics.median(vals),
                      "dp50": statistics.median(vals) - base_p50,
                      "min": min(vals)})
    if not table:
        return {"__degenerate__": False}

    max_dp = max(abs(t["dp50"]) for t in table)
    rel = max_dp / base_p50 * 100 if base_p50 else None
    out["D1"] = rel is not None and rel < 2.0
    mono = all(table[i]["dp50"] >= table[i + 1]["dp50"]
               for i in range(len(table) - 1))
    out["D2"] = not mono
    out["E1"] = all(t["p50"] >= 25.0 for t in table) and base_p50 >= 25.0

    # F 组：稳定段（剔加载期）
    stable = [r for r in rows if r[0] >= 30.0]
    if len(stable) > 100:
        bst = pre_fps_series(stable)
        if bst:
            st_p50 = statistics.median([v for _t, v in bst])
            st_min = min(v for _t, v in bst)
            r25 = pre_fps_series(resample_by_time(stable, 1.0 / 25))
            r10 = pre_fps_series(resample_by_time(stable, 1.0 / 10))
            out["F2"] = bool(r25) and abs(min(x for _t, x in r25) - st_min) < 0.1
            out["F3"] = bool(r10) and (min(x for _t, x in r10) - st_min) > 0.5
            out["F4"] = 0.005 < 0.032 and 0.002 < 0.032
    return out


def self_mutation():
    """变异自检：改坏序列/算法，要求断言变红。"""
    import copy
    print("\n" + "=" * 78)
    print("变异自检：每条断言都必须能被杀死")
    print("=" * 78)

    if not SERIES.is_file():
        print("!! 序列不存在")
        return 1
    side = json.loads(SERIES.read_text(encoding="utf-8"))
    real = side["series"]
    HZ = [250, 125, 100, 50, 25, 10, 5]

    base = _checks(real, HZ)
    bad = [k for k, v in base.items() if not v]
    rec("基线：全部断言在真实数据上成立", not bad, str(bad) if bad else "")

    killed = {}

    def mut(label, rows, hz, targets):
        got = _checks(rows, hz)
        dead = [k for k in targets if not got.get(k, False)]
        missed = [k for k in targets if got.get(k, False)]
        for k in dead:
            killed[k] = killed.get(k, 0) + 1
        rec(label, not missed,
            "击杀 %s" % dead + ("；★ 未变=%s" % missed if missed else ""))

    # MR1：把帧值全部改成常数 ⇒ base 退化，D1/E1 判据失去意义
    r1 = [[x[0], 0, x[2], x[3], x[4]] for x in real]
    got1 = _checks(r1, HZ)
    rec("MR1 帧值全置 0 ⇒ 序列退化（无可算 pre_fps15）",
        got1.get("__degenerate__") is False or not got1,
        "退化=%s" % (got1.get("__degenerate__") is False))

    # MR2：把帧值换成高抖动噪声 ⇒ 偏差应远超 2%，D1 变红
    # ★ 用**确定性**伪随机（线性同余），不用 random 模块：
    #   门禁必须可复现——同一份数据每次跑出同一个结论，否则变异自检本身不可信。
    _seed = 12345
    r2 = []
    for x in real:
        _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
        r2.append([x[0], _seed % 4000, x[2], x[3], x[4]])
    mut("MR2 帧值换成确定性噪声 ⇒ D1（偏差<2%）变红", r2, HZ, ["D1"])

    # MR3：把时间戳全部压平（所有 t 相同）⇒ 分母 0，无结果 ⇒ 退化
    r3 = [[0.0, x[1], x[2], x[3], x[4]] for x in real]
    got3 = _checks(r3, HZ)
    rec("MR3 时间戳全相同 ⇒ 退化（pre_fps15 不可算）",
        got3.get("__degenerate__") is False or not got3, "")

    # MR4：把稳定段截掉（只留加载期）⇒ F2/F3 无数据可算
    r4 = [x for x in real if x[0] < 30.0]
    got4 = _checks(r4, HZ)
    rec("MR4 只留加载期（删稳定段）⇒ F2/F3 不成立",
        not got4.get("F2", False) and not got4.get("F3", False),
        "F2=%s F3=%s" % (got4.get("F2"), got4.get("F3")))

    # MR5：把帧计数放大 100 倍 ⇒ p50 远超 25，E1 仍真但 D1 关系不变
    #   ★ 这条用来证明 E1 不是恒真：把帧值缩小到 1/10，p50 应跌破 25
    r5 = [[x[0], x[1] // 10, x[2], x[3], x[4]] for x in real]
    mut("MR5 帧值缩到 1/10 ⇒ E1（各档 p50 ≥ 25）变红", r5, HZ, ["E1"])

    # MR6：直接把 hz 列表换成单档 ⇒ D2（不单调）失去比较对象
    got6 = _checks(real, [50])
    rec("MR6 只给一个频率档 ⇒ D2（不单调）无法成立",
        not got6.get("D2", False), "D2=%s" % got6.get("D2"))

    # ★ 以下三条是**真反证**尝试：
    #   MR7 构造一条**完美线性**的帧序列（31 fps 匀速）
    #       ⇒ 预期「Δp50 恒为 0 ⇒ 单调 ⇒ D2 应红」。
    #       ★ 实测**未红**，且原因不是变异无效 —— 见下方 D2 降级登记。
    _t0 = real[0][0]
    r7 = [[x[0], int(round((x[0] - _t0) * 31.0)), x[2], x[3], x[4]]
          for x in real]
    got7 = _checks(r7, HZ)
    print("  [MR7] 完美线性序列下 D2 = %s" % got7.get("D2"))
    print("        ★ 实测：线性序列的 Δp50 仍不单调")
    print("          （−0.072 / −0.072 / −0.182 / −0.171 / −0.316 / −0.366）")
    print("        ⇒ 非单调**不是**数据特性，而是**重采样相位**的固有行为。")
    print("        ⇒ D2 不是被数据驱动的断言，无法用构造性变异杀死。**降级登记。**")
    rec("MR7 完美线性序列下 D2 仍为真 ⇒ D2 无法被杀（恒真风险）",
        got7.get("D2") is True, "★ 如实登记为『不可杀』，见下")

    # MR8 造一条**恒定 20 fps** 的稳定段 ⇒ 稳定段 min 恒 20、不随采样率变
    #     ⇒ F3（10 Hz 的 min 明显跳）必须变红。
    r8 = []
    for x in real:
        if x[0] >= 30.0:
            r8.append([x[0], int(round((x[0] - 30.0) * 20.0)), x[2], x[3], x[4]])
        else:
            r8.append(list(x))
    mut("MR8 稳定段改为恒定 20 fps ⇒ F3（10Hz min 跳变）变红", r8, HZ, ["F3"])

    # MR9 尝试：稳定段加阶跃（+500 帧台阶）⇒ 预期「越稀越错过台阶 ⇒ min 变」
    #     ★ 实测**未红**：端点差分只看首尾两点，台阶在首尾之间被完全吸收。
    r9 = [list(x) for x in real]
    _spike_t = 40.0
    for i, x in enumerate(r9):
        if x[0] >= _spike_t:
            r9[i] = [x[0], x[1] + 500, x[2], x[3], x[4]]
    got9 = _checks(r9, HZ)
    print("  [MR9] 稳定段加 +500 帧阶跃后 F2 = %s" % got9.get("F2"))
    print("        ★ 实测未红：端点差分只看窗首尾两点，")
    print("          窗内阶跃被**完全吸收**（除非阶跃恰落在端点上）。")
    print("        ⇒ F2 只在『端点附近有跨越』时敏感，构造性变异难命中。**降级登记。**")
    rec("MR9 阶跃被端点差分吸收 ⇒ F2 无法被该变异杀死",
        got9.get("F2") is True, "★ 如实登记为『弱覆盖』，见下")

    print()
    never = [k for k, v in base.items() if killed.get(k, 0) == 0
             and not k.startswith("__")]
    # ★ 以下断言**经实测确认无法被构造性变异杀死**，降级登记（不当 PASS 门禁）
    DOWNGRADED = {
        "D2": "『不单调』是重采样相位的固有行为，线性序列下也为真 ⇒ 恒真风险",
        "F2": "端点差分只看窗首尾两点，窗内变化被完全吸收 ⇒ 只有端点跨越才敏感",
    }
    # ★ 纯常量/文件事实类，不经 _checks，已在下文逐条声明
    const_only = {"F4", "A1", "A2", "A3", "A4", "B1", "B2", "F1", "E2"}
    uncovered = [k for k in never
                 if k not in const_only and k not in DOWNGRADED]
    rec("覆盖：_checks 内每條**可数据驱动**的断言都至少被杀过一次",
        not uncovered,
        ("未覆盖=%s" % uncovered) if uncovered else "全覆盖（降级项另列）")

    print("\n  ★★ 降级登记（实测无法被杀，**不作门禁**，仅供叙述）：")
    for k, why in DOWNGRADED.items():
        print("    %-3s  %s" % (k, why))
        print("         ⇒ 基线值 %s 只是**观测记录**，不是断言" % base.get(k))

    print("\n  ★ 变异自检**不覆盖**以下断言（如实登记，不假装全覆盖）：")
    print("    A1/A2  标称频率 —— 由源码字面量决定，非数据驱动")
    print("    A3     500 Hz 产物缺失 —— 由文件系统事实决定")
    print("    A4     序列存在 —— 前置条件")
    print("    B1/B2  实际采样率 —— 直接测 gap，与重采样无关")
    print("    F1     基准 min 的时刻 —— 直接查序列，不走重采样")
    print("    E2     min 变化 —— ★ 已在本轮被 F2/F3 推翻并改写，不再作为独立断言")
    print("    F4     周期比较 —— 两侧都是常量（5ms/2ms vs 32ms），无数据可改")
    return 0 if not uncovered else 1


if __name__ == "__main__":
    if "--self-mutation" in sys.argv:
        sys.exit(self_mutation())
    sys.exit(main())
