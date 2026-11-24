# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W1 —— 离线重算（P2）。

**只读 ndjson**，不连真机、不启动游戏、不读进程内存。
所有结论只从 `out/*.ndjson` 中的 `kind=="sample"` 行重算。

质量红线：
  * read_status != "ok" 的拍**保留但不参与**任何门控/推进统计；
    不当作「未推进」，也不填补。
  * 不把 50 ms 轮询称为逐帧 P95/P99 或 FPS。
  * 「没观测到长停」绝不写成「长停不存在」。
  * 门控判据只用 frame_advanced 与门控字节；不用「帧在变」定义战斗状态。

用法：
  python -X utf8 analyze_probe.py --ndjson out/gate_probe_xxx.ndjson \
      --md ANALYSIS.md --uncovered UNCOVERED.md --json out/analysis.json
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe")
OUT = BASE / "out"
GATES = ("g1", "g2", "g3", "g4")


def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load(path):
    samples, events, metas = [], [], []
    with open(path, "r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception as e:
                events.append({"kind": "parse_error", "line": ln, "err": str(e)})
                continue
            k = rec.get("kind")
            if k == "sample":
                samples.append(rec)
            elif k == "event":
                events.append(rec)
            else:
                metas.append(rec)
    return samples, events, metas


def pct(n, d):
    return (100.0 * n / d) if d else None


def fmt_pct(v):
    return "n/a" if v is None else "%.3f%%" % v


def hist_counter(counter, top=None):
    items = counter.most_common(top)
    if not items:
        return "（无）"
    return "、".join("`%s`×%d" % (k, v) for k, v in items)


def longest_zero_gate_stall(samples):
    """连续「read ok & frame_advanced is False & any_gate_nonzero is False」段。

    段长用**真实 t_mono_ns 差**，不用名义间隔。
    返回 (最长段字典, 全部段列表)。
    """
    def cond(r):
        # 帧号回退属边界（新局/读档），不计入「停推连续段」
        return (r.get("read_status") == "ok"
                and r.get("frame_advanced") is False
                and r.get("any_gate_nonzero") is False
                and r.get("frame_regression") is not True)

    runs = []
    cur = None
    for idx, r in enumerate(samples):
        if cond(r):
            if cur is None:
                cur = {"start_idx": idx, "end_idx": idx, "n": 1,
                       "t_first_ns": int(r["t_mono_ns"]),
                       "t_last_ns": int(r["t_mono_ns"])}
            else:
                cur["end_idx"] = idx
                cur["n"] += 1
                cur["t_last_ns"] = int(r["t_mono_ns"])
        else:
            if cur is not None:
                runs.append(cur)
                cur = None
    if cur is not None:
        runs.append(cur)

    for c in runs:
        c["span_ms"] = (c["t_last_ns"] - c["t_first_ns"]) / 1e6
        b = samples[c["start_idx"] - 1]["t_mono_ns"] if c["start_idx"] > 0 else c["t_first_ns"]
        a = (samples[c["end_idx"] + 1]["t_mono_ns"]
             if c["end_idx"] + 1 < len(samples) else c["t_last_ns"])
        c["enclosed_ms"] = (int(a) - int(b)) / 1e6
        c["first_seq"] = samples[c["start_idx"]].get("seq")
        c["last_seq"] = samples[c["end_idx"]].get("seq")
        c["remark_first"] = samples[c["start_idx"]].get("remark")
    if not runs:
        return None, []
    best = max(runs, key=lambda c: (c["span_ms"], c["n"]))
    return best, runs


def window_rates(samples, window_s=10.0):
    """每 window_s 秒窗口内的「帧计数净推进 / 真实时间」区间估计。"""
    ok = [r for r in samples if r.get("read_status") == "ok"]
    if len(ok) < 2:
        return {"overall": None, "windows": [], "min": None,
                "median": None, "max": None,
                "total_delta": 0, "elapsed_s": 0.0}
    t0 = int(ok[0]["t_mono_ns"])
    t_end = int(ok[-1]["t_mono_ns"])
    elapsed = (t_end - t0) / 1e9
    total = 0
    buckets = defaultdict(float)
    for r in ok:
        d = r.get("frame_delta")
        if isinstance(d, int) and d > 0:
            total += d
            b = int((int(r["t_mono_ns"]) - t0) / 1e9 // window_s)
            buckets[b] += d
    n_win = max(buckets.keys(), default=0) + 1
    rates = []
    for b in range(n_win):
        w_start = b * window_s
        w_end = min((b + 1) * window_s, elapsed)
        dur = max(0.0, w_end - w_start)
        if dur <= 0:
            continue
        rates.append({"window": b, "start_s": w_start, "end_s": w_end,
                      "duration_s": dur, "delta": buckets.get(b, 0),
                      "rate_per_s": buckets.get(b, 0) / dur})
    vals = [x["rate_per_s"] for x in rates]
    return {"overall": total / elapsed if elapsed > 0 else None,
            "windows": rates,
            "min": min(vals) if vals else None,
            "median": statistics.median(vals) if vals else None,
            "max": max(vals) if vals else None,
            "total_delta": total, "elapsed_s": elapsed}


def analyze(path):
    samples, events, metas = load(path)
    n_samples = len(samples)
    rs_hist = Counter(str(r.get("read_status")) for r in samples)
    ok = [r for r in samples if r.get("read_status") == "ok"]
    n_ok = len(ok)
    n_fail = n_samples - n_ok

    # ---- frame_advanced=false ----
    adv_false = [r for r in ok if r.get("frame_advanced") is False]
    adv_true = [r for r in ok if r.get("frame_advanced") is True]
    adv_null = [r for r in ok if r.get("frame_advanced") is None]
    false_gate_nz = [r for r in adv_false if r.get("any_gate_nonzero") is True]
    false_gate_zero = [r for r in adv_false if r.get("any_gate_nonzero") is False]
    false_gate_null = [r for r in adv_false if r.get("any_gate_nonzero") is None]
    n_any_gate_nz = sum(1 for r in ok if r.get("any_gate_nonzero") is True)
    n_frame_regression = sum(1 for r in ok if r.get("frame_regression") is True)

    # ---- 各门控非零占比 + 对应 remark ----
    gate_stats = {}
    for g in GATES:
        nz = [r for r in ok if isinstance(r.get(g), int) and r[g] != 0]
        gate_stats[g] = {
            "n_nonzero": len(nz),
            "pct_nonzero": pct(len(nz), n_ok),
            "remark_hist": dict(Counter(str(r.get("remark")) for r in nz)),
            "in_adv_false": sum(1 for r in adv_false
                                if isinstance(r.get(g), int) and r[g] != 0),
        }

    best, runs = longest_zero_gate_stall(samples)
    rates = window_rates(samples)

    remark_hist = Counter(str(r.get("remark")) for r in samples)
    per_remark = {}
    for rem, cnt in remark_hist.items():
        sub = [r for r in samples if str(r.get("remark")) == rem]
        sub_ok = [r for r in sub if r.get("read_status") == "ok"]
        per_remark[rem] = {
            "n": cnt, "n_ok": len(sub_ok),
            "n_adv_false": sum(1 for r in sub_ok if r.get("frame_advanced") is False),
            "n_all_zero_no_adv": sum(1 for r in sub_ok
                                     if r.get("frame_advanced") is False
                                     and r.get("any_gate_nonzero") is False),
            "n_gate_nz": sum(1 for r in sub_ok
                             if r.get("any_gate_nonzero") is True),
            "n_fail": cnt - len(sub_ok),
        }

    fg_hist = Counter(str(r.get("win_foreground")) for r in samples)
    exit_hist = Counter(str(r.get("exitstate")) for r in ok).most_common(12)
    b07784_hist = Counter(str(r.get("b07784")) for r in ok).most_common(12)
    ev_hist = Counter(str(r.get("event")) for r in events if r.get("event"))
    val_hist = Counter()
    for g in GATES:
        for r in ok:
            if isinstance(r.get(g), int) and r[g] != 0:
                val_hist["%s=%d" % (g, r[g])] += 1

    t_first = min((int(r["t_mono_ns"]) for r in samples), default=0)
    t_last = max((int(r["t_mono_ns"]) for r in samples), default=0)
    return {
        "ndjson": str(path), "generated_utc": utc_iso(),
        "n_samples": n_samples, "n_ok": n_ok, "n_fail": n_fail,
        "read_status_hist": dict(rs_hist),
        "observed_span_s": (t_last - t_first) / 1e9,
        "first_utc": next((r.get("t_utc_iso") for r in samples), None),
        "last_utc": next((r.get("t_utc_iso") for r in reversed(samples)), None),
        "n_adv_false": len(adv_false), "n_adv_true": len(adv_true),
        "n_adv_null": len(adv_null),
        "n_any_gate_nonzero_ok": n_any_gate_nz,
        "n_frame_regression": n_frame_regression,
        "false_gate_nz": len(false_gate_nz),
        "false_gate_nz_pct": pct(len(false_gate_nz), len(adv_false)),
        "false_gate_zero": len(false_gate_zero),
        "false_gate_zero_pct": pct(len(false_gate_zero), len(adv_false)),
        "false_gate_null": len(false_gate_null),
        "gate_stats": gate_stats,
        "all_zero_no_adv_total": len(false_gate_zero),
        "all_zero_no_adv_longest": best,
        "all_zero_no_adv_n_runs": len(runs),
        "all_zero_no_adv_top_runs": sorted(
            runs, key=lambda c: c["span_ms"], reverse=True)[:10],
        "rates": rates,
        "remark_hist": dict(remark_hist), "per_remark": per_remark,
        "win_foreground_hist": dict(fg_hist),
        "exitstate_top": exit_hist, "b07784_top": b07784_hist,
        "event_hist": dict(ev_hist), "gate_nonzero_values": dict(val_hist),
        "n_events": len(events), "n_meta": len(metas),
        "events": [{"event": e.get("event"), "remark": e.get("remark"),
                    "elapsed_s": e.get("elapsed_s"),
                    "detail": e.get("detail")} for e in events
                   if e.get("event")],
    }


def render_md(s):
    t = []
    A = t.append
    A("# ANALYSIS.md —— 门控跳过 vs 真卡顿（离线重算，只从 NDJSON）")
    A("")
    A("- run_id: `NEXT_RE_20261112_R02`")
    A("- 生成时刻(UTC): `%s`" % s["generated_utc"])
    A("- 数据源: `%s`（**只读**，无真机连接）" % s["ndjson"])
    A("- 采样拍数 **%d**：`read_status=ok` %d，读失败 **%d**（保留但不参与统计，"
      "不当作「未推进」，也不填补）" %
      (s["n_samples"], s["n_ok"], s["n_fail"]))
    A("- 真实单调时钟跨度: **%.3f s**（%s → %s）" %
      (s["observed_span_s"], s["first_utc"], s["last_utc"]))
    A("- `read_status` 分布: %s" % s["read_status_hist"])
    A("")
    A("## 1. 核心判据")
    A("")
    A("| 指标 | 值 |")
    A("| --- | --- |")
    A("| `frame_advanced=false` 拍数 | **%d** |" % s["n_adv_false"])
    A("| 其中 `any_gate_nonzero=true` | **%d**（%s） |" %
      (s["false_gate_nz"], fmt_pct(s["false_gate_nz_pct"])))
    A("| 其中 `any_gate_nonzero=false`（四门控全 0 但未推进） | **%d**（%s） |" %
      (s["false_gate_zero"], fmt_pct(s["false_gate_zero_pct"])))
    A("| 其中 `any_gate_nonzero=null` | %d |" % s["false_gate_null"])
    A("| `frame_advanced=true` 拍数 | %d |" % s["n_adv_true"])
    A("| `frame_advanced=null`（首拍 / 读失败后一拍） | %d |" % s["n_adv_null"])
    A("")
    b = s["all_zero_no_adv_longest"]
    A("**「四门控全 0 但帧未推进」**：共 %d 拍，位于 %d 个连续段。" %
      (s["all_zero_no_adv_total"], s["all_zero_no_adv_n_runs"]))
    if b:
        A("最长连续段：**%.3f ms**（真实 `t_mono_ns` 差，%d 拍，seq %s→%s，"
          "段首 remark=`%s`）；相邻前后拍夹出的区间上界 %.3f ms。" %
          (b["span_ms"], b["n"], b["first_seq"], b["last_seq"],
           b["remark_first"], b["enclosed_ms"]))
    else:
        A("最长连续段：**未观测到**（0 段）。")
    A("")
    A("最长 10 段（按真实 t_mono_ns 跨度降序）：")
    A("")
    A(md_table4(["#", "拍数", "span(ms)", "enclosed(ms)", "seq", "remark"],
                [[i + 1, c["n"], "%.3f" % c["span_ms"],
                  "%.3f" % c["enclosed_ms"],
                  "%s→%s" % (c["first_seq"], c["last_seq"]),
                  c["remark_first"]]
                 for i, c in enumerate(s["all_zero_no_adv_top_runs"])]))
    A("")
    A("> **解释边界**：50 ms 轮询只在采样瞬间看门控字节。两次采样之间某个游戏 tick"
      "可能短暂出现门控非零而两次采样都读到 0。因此「四门控全 0 但未推进」"
      "**不能证明**该停推不是门控造成的；它只能说明 *在采样瞬间* 四门控为 0。"
      "反之，若 `frame_advanced=false` 的拍全部伴随门控非零，则与「门控跳过」一致，"
      "但同样不是排它性证明（本批不抓栈，无法定位调用点）。")
    A("")
    A("> **另一层模糊性**：50 ms 轮询窗口内 `frame_advanced=false` 只表示这 50 ms 里"
      "帧计数器净增量为 0。若游戏内部逻辑 tick 本身慢于 20 Hz、或采样恰好落在两个"
      "tick 之间，也会出现单拍全 0 未推进，并**不构成**「卡顿」。因此单拍计数只能作线索，"
      "真正有意义的是**连续段长度**（上表用真实 `t_mono_ns` 差给出）；"
      "孤立单拍不应解读为停推。")
    A("")
    A("## 2. 四门控非零占比及对应状态")
    A("")
    rows = []
    for g in GATES:
        st = s["gate_stats"][g]
        rows.append([g, st["n_nonzero"], fmt_pct(st["pct_nonzero"]),
                     st["in_adv_false"],
                     hist_counter(Counter(st["remark_hist"]), 8)])
    A(md_table4(["门控", "非零拍数", "占 ok 拍比例", "落在 frame_advanced=false 内",
                 "非零时 remark 状态"], rows))
    A("")
    A("- 门控非零的具体取值: %s" %
      (hist_counter(Counter(s["gate_nonzero_values"]), 20)))
    A("- `any_gate_nonzero=true` 在全部 ok 拍中: %d（%s）；"
      "帧号回退（新局边界）拍数: %d。" %
      (s["n_any_gate_nonzero_ok"],
       fmt_pct(pct(s["n_any_gate_nonzero_ok"], s["n_ok"])),
       s["n_frame_regression"]))
    A("")
    A("按 `remark`（脚本排程标注的**外部状态**，不是从帧变化推出来的战斗状态）分段：")
    A("")
    pr = []
    for rem, v in sorted(s["per_remark"].items(), key=lambda kv: -kv[1]["n"]):
        pr.append([rem, v["n"], v["n_ok"], v["n_fail"], v["n_adv_false"],
                   v["n_all_zero_no_adv"], v["n_gate_nz"]])
    A(md_table4(["remark", "总拍", "ok", "fail", "adv=false",
                 "全0未推进", "门控非零"], pr))
    A("")
    A("## 3. 帧推进速率的区间估计（**不是逐帧 FPS**）")
    A("")
    r = s["rates"]
    if r["overall"] is not None:
        A("- 全程净帧计数推进 Δframe = **%d**，真实耗时 %.3f s ⇒ 平均 "
          "**%.3f 计数/s**" % (r["total_delta"], r["elapsed_s"], r["overall"]))
        A("- 10 s 窗口（按真实 `t_mono_ns` 切分）净推进率区间："
          "**min %.3f / 中位 %.3f / max %.3f 计数/s**（共 %d 个窗口）" %
          (r["min"], r["median"], r["max"], len(r["windows"])))
        A("")
        A(md_table4(["窗口", "起(s)", "止(s)", "真实时长(s)", "Δframe", "计数/s"],
                    [[x["window"], "%.1f" % x["start_s"], "%.1f" % x["end_s"],
                      "%.2f" % x["duration_s"], x["delta"],
                      "%.3f" % x["rate_per_s"]] for x in r["windows"]]))
    else:
        A("- 有效连续 ok 拍不足，无法估计。")
    A("")
    A("> **明确声明**：以上数字是 *50 ms 轮询窗口内帧计数器的净增量 / 真实墙钟时间*，"
      "**不是逐帧 FPS**，也不是每帧耗时。一次 50 ms 轮询之间游戏可能推进 0~多个"
      "内部 tick，我们只看净值；因此**不提供**逐帧 P95/P99、帧时间分布或 FPS 分位数。"
      "该计数器的语义是游戏内部逻辑帧计数（`0x00A8ED84` 在 `0x55DE81` 处 +1），"
      "不等同于渲染帧数。")
    A("")
    A("## 4. 辅助字段 / 前台 / 事件（仅登记，不作语义断言）")
    A("")
    A("- `win_foreground` 分布: %s" % s["win_foreground_hist"])
    A("- `exitstate` (0x00A8EDD8) 前 12 值: %s" % s["exitstate_top"])
    A("- `b07784` (0x00B07784) 前 12 值: %s" % s["b07784_top"])
    A("- 事件行 %d 条，分布: %s" % (s["n_events"], s["event_hist"]))
    A("")
    A("事件明细：")
    A("")
    for e in s["events"]:
        A("- `%s` @ %s s, remark=`%s`, detail=`%s`" %
          (e["event"], e["elapsed_s"], e["remark"],
           json.dumps(e["detail"], ensure_ascii=False, default=str)
           if e["detail"] is not None else ""))
    A("")
    A("## 5. 结论口径")
    A("")
    A("1. 判据只用 `frame_advanced` 与四个门控字节；**没有**用「帧在变」定义战斗状态。")
    A("2. 本次是 50 ms 间隔的单趟只读轮询。**没观测到长停 ≠ 长停不存在**；"
      "未被本次观测覆盖的时长、地图、负载与随机相位都可能出现长停。")
    A("3. 「四门控全 0 但帧未推进」若存在，只能作为「*可能是*真的卡顿/非门控原因」"
      "的**线索**，不能作为排它结论：门控可在采样间非零、也可能存在本批未登记的"
      "其它跳过路径；本批禁止抓栈，无法给出调用点级归因。")
    return "\n".join(t) + "\n"


def md_table4(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |")
    return "\n".join(out)


def render_comparison(s):
    runs = s.get("comparison_runs") or []
    t = []
    A = t.append
    A("")
    A("## 附录 —— 多趟运行对比（均只从各自 NDJSON 离线重算）")
    A("")
    A("主表为本次最后一路样本；下表为同一批次内其它路原始记录，"
      "**原始 NDJSON 一律不删改**。")
    A("")
    rows = [[str(s["ndjson"]), s["n_samples"], s["n_adv_false"],
             s["false_gate_nz"], s["false_gate_zero"],
             s["n_any_gate_nonzero_ok"],
             ("%.3f" % s["all_zero_no_adv_longest"]["span_ms"])
             if s["all_zero_no_adv_longest"] else "none",
             "%.1f" % s["observed_span_s"]]]
    for r in runs:
        rows.append([r["ndjson"], r["n_samples"], r["n_adv_false"],
                     r["false_gate_nz"], r["false_gate_zero"],
                     r["n_gate_nz_ok"],
                     ("%.3f" % r["longest_ms"]) if r["longest_ms"] is not None
                     else "none", "%.1f" % r["observed_span_s"]])
    A(md_table4(["NDJSON", "采样", "adv=false", "其中门控非零",
                 "四门控全0未推进", "全程门控非零拍", "最长段(ms)", "时长(s)"],
                rows))
    A("")
    A("> 第一趟（run1）的 Esc 返回动作失效，导致约 240 s 处于**局内菜单暂停**；"
      "该段虽为「四门控全 0 但帧未推进」，但属于 **观测自身引入的扰动**，"
      "**不得**解读为自然卡顿，也不得据此宣称「长停已被复现」。"
      "第二趟修正了返回动作并加了恢复校验，以第二趟为主判据。")
    return "\n".join(t) + "\n"


def render_uncovered(s):
    t = []
    A = t.append
    A("# UNCOVERED.md —— 本次观测的未覆盖项与扰动")
    A("")
    A("- run_id: `NEXT_RE_20261112_R02` / W1 真机只读观测（批次 A）")
    A("- 生成时刻(UTC): `%s`" % s["generated_utc"])
    A("")
    A("## 1. 方法学未覆盖（最重要）")
    A("")
    A("1. **采样相位盲区**：轮询间隔 50 ms，而门控字节是*每个游戏 tick* 判定的。"
      "两次采样之间门控可能短暂非零，两次采样都读到 0。因此"
      "「采样瞬间四门控全 0」**不等于**「整段区间门控全 0」。"
      "本批无法逐 tick 观测门控，不能把「全 0 未推进」直接判定为真卡顿。")
    A("2. **不抓栈**：本批禁止 `SuspendThread` / `StackWalk64` / MiniDump / 断点 / 注入，"
      "因此即使出现真实卡顿，也无法定位到具体调用点、锁或等待对象。")
    A("3. **单一场次**：只跑了 1 张图（按名称子串选 `Proving Grounds`）、"
      "1 个进程、1 次加载、1 档游戏速度、1 个渲染配置。"
      "未覆盖其它地图、高负载局、多人/网络局、不同游戏速度、存档/读档、"
      "不同显卡/ddraw 后端、长时间（>5 min）对局、后台挂机。")
    A("4. **「没观测到长停」≠「长停不存在」**：本趟观测 %.1f s，"
      "对低频、长尾、相位相关的停推没有统计把握。" % s["observed_span_s"])
    A("5. **门控地址未做运行时二次验证**：只做了 `0x0055DE4F` 处 5 字节代码签名"
      "比对（确认镜像基址符合预期），未枚举模块基址、未做运行时反汇编。"
      "若镜像被重定位（签名比对会失败），所有绝对地址读数将失去意义。")
    A("6. **辅助字段未解码**：`exitstate`(0x00A8EDD8)、`b07784`(0x00B07784)"
      " 只登记数值分布，未解释其语义，也未验证它们与停推的因果关系。")
    A("")
    A("## 2. 状态标注的局限")
    A("")
    A("- `remark` 来自**脚本排程**（开局瞬间 / 稳定局内 / Esc / 失焦 / 切回），"
      "不是从帧变化反推的战斗状态。")
    A("- Esc「打开菜单 / 返回」与「窗口失焦 / 切回」都是**尽力而为**的 UI 尝试"
      "（`keybd_event` / `SetForegroundWindow` + ALT 技巧），"
      "本批**没有**独立验证菜单是否真的弹出、游戏是否真的暂停、"
      "DirectInput 焦点是否真的丢失；只登记动作、前台窗口 pid 与随后的读数。"
      "若动作未生效，该段标注仍成立为「尝试」，不能当「已发生」。")
    A("- `win_foreground` 仅比较前台窗口所属 pid，不反映全屏 DirectDraw 状态、"
      "Alt-Tab 中间态或输入焦点细节。")
    A("- 若游戏自然崩溃/退出：只记录时刻与最后读数，**不重启补测**；"
      "本趟退出事件数见 `ANALYSIS.md` 事件明细。")
    A("- 游戏若在对局中自然结束（胜利/失败），本批只靠帧计数回退 / 进程退出 /"
      "排程事件间接记录，未枚举结算界面的控件做独立确认。")
    A("")
    A("## 3. 本次观测自身引入的扰动")
    A("")
    A("1. **ReadProcessMemory 轮询**：每拍 7 次跨进程读（约 140 次/s），"
      "会产生轻微的系统调用与缓存扰动，但不挂起线程、不改目标内存。")
    A("2. **UI 输入注入**：Esc 键事件与前台窗口切换本身就是对局状态的干预，"
      "可能主动触发暂停/门控，属于**观测引入的停推**，与「自然卡顿」不可混同。")
    A("3. **NDJSON 每行 flush**：磁盘 I/O 在采样线程内同步完成，"
      "可能使个别采样间隔略大于名义 50 ms；分析一律用真实 `t_mono_ns`，"
      "不用名义间隔。")
    A("4. **启动/加载期**：开局后固定等待 15 s 才开始轮询，"
      "加载期与开局瞬间的早期行为只覆盖了 15 s 之后的部分。")
    A("5. **配置还原**：收尾时从基线副本逐字节回写 `RA2MD.INI` / `ddraw.ini`，"
      "会抹掉游戏本趟写回的设置；游戏写回内容已在 `CONFIG_RESTORE.md` 中比对登记。")
    A("")
    A("## 4. 明确未做的事（授权边界）")
    A("")
    A("- 未 `SuspendThread` / `ResumeThread` / `StackWalk64` / MiniDump / 下断点 /"
      "注入 / 写目标进程内存 / 修改 exe 或 dll。")
    A("- 未 `taskkill` 任何非本趟自启动的进程；只关闭自己记录的 pid。")
    A("- 未对全仓做 `Get-ChildItem -Recurse`；文件清单只在 `ra2youli\\` 内"
      "做有上限（%d 文件）的比对扫描。" % 6000)
    A("- 未做任何 git 写操作；写域仅限 "
      "`lead/next_re_20261112_r02/W1_realtime_probe/`（含 `out/`）。")
    return "\n".join(t) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ndjson", action="append", default=[],
                    help="可重复；最后一个为主样本，其余作为附录对比")
    ap.add_argument("--md", default=str(BASE / "ANALYSIS.md"))
    ap.add_argument("--uncovered", default=str(BASE / "UNCOVERED.md"))
    ap.add_argument("--json", default=str(OUT / "analysis.json"))
    a = ap.parse_args()

    paths = []
    for x in a.ndjson:
        pth = Path(x)
        if not pth.is_absolute():
            pth = BASE / pth
        paths.append(pth)
    if not paths:
        cands = sorted(OUT.glob("gate_probe_*.ndjson"),
                       key=lambda x: x.stat().st_mtime, reverse=True)
        if not cands:
            raise SystemExit("没有 ndjson 可分析")
        paths = [cands[0]]
    s = analyze(paths[-1])
    others = []
    for extra in paths[:-1]:
        try:
            others.append((extra, analyze(extra)))
        except Exception as e:
            print("warn: 跳过 %s (%r)" % (extra, e))
    s["comparison_runs"] = [
        {"ndjson": str(p), "n_samples": o["n_samples"],
         "n_adv_false": o["n_adv_false"],
         "false_gate_nz": o["false_gate_nz"],
         "false_gate_zero": o["false_gate_zero"],
         "n_gate_nz_ok": o["n_any_gate_nonzero_ok"],
         "longest_ms": (o["all_zero_no_adv_longest"]["span_ms"]
                        if o["all_zero_no_adv_longest"] else None),
         "observed_span_s": o["observed_span_s"]}
        for p, o in others]
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(s, ensure_ascii=False, indent=1,
                                       sort_keys=True, default=str),
                            encoding="utf-8")
    Path(a.md).write_text(render_md(s) + render_comparison(s), encoding="utf-8")
    Path(a.uncovered).write_text(render_uncovered(s), encoding="utf-8")
    print("analyze_probe OK: ndjson=%s samples=%d ok=%d fail=%d "
          "adv_false=%d all_zero_no_adv=%d longest_ms=%s comparison=%d" %
          (paths[-1], s["n_samples"], s["n_ok"], s["n_fail"], s["n_adv_false"],
           s["all_zero_no_adv_total"],
           ("%.3f" % s["all_zero_no_adv_longest"]["span_ms"])
           if s["all_zero_no_adv_longest"] else "none",
           len(s["comparison_runs"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
