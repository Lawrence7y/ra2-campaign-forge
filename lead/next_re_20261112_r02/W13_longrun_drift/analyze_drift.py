#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W13 —— RE-N04b 长时漂移离线重算（只从 NDJSON 重算，可重复）。

红线（与 longrun_probe.py predeclared_analysis_plan 完全一致，不得事后改）：
  * 速率单位 = 计数/s（Δframe/真实 Δt，t_mono_ns 差），不是帧率/FPS；
  * 30 ms 轮询非逐帧采样 ⇒ 无逐帧 P95/P99 / 帧时间 / 1% low；
  * 无经校验的单位计数 ⇒ 不宣称负载；A8ED50/B0CE88/87E8E0 语义未定，只描述；
  * 单臂 ⇒ 无「原版对比」「优化收益」；
  * 10 s 固定网格窗（锚=段内首个 ok 拍），窗边界参考拍=边界时刻前最后 ok 拍，
    窗与窗共享边界无缝拼合；真实 Δt≥8.0s 才算有效窗；残窗列出标注 partial；
  * 漂移判据（预设）：n3=N//3，drop_pct=(median(首1/3)-median(末1/3))/median(首1/3)
    *100；>0.5 ⇒ 候选下行漂移；≤0.5（含上升）⇒ 未观测到漂移；
  * 斜率 = 全有效窗 rate~窗序号最小二乘（计数/s per 10 s 窗）；
  * 拐点（判漂移时）= 首个 rate < 0.995*median(首1/3) 的有效窗；只给相关不归因；
  * 停推段 = 连续 ok 拍 frame 相同且真实跨度 ≥1.0s；逐段标 win_foreground/输入证据；
    无输入 ⇒ 「未知原因的停推」；
  * read_status=fail 拍保留、不填补；
  * 分档：有效局内段 <300s ⇒ [数据不足]；否则按 drop_pct 分档。

用法：
  python -X utf8 analyze_drift.py --ndjson out/run.ndjson
输出：out/windows.csv + out/analysis.json + 控制台摘要。
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import statistics
import sys
from pathlib import Path

WIN_S = 10.0          # 固定窗宽（秒）
MIN_DT_S = 8.0        # 有效窗真实 Δt 下限
DRIFT_PCT = 0.5       # 预设阈值（不得改）
KNEE_FACTOR = 0.995   # 拐点阈值因子（不得改）
STALL_S = 1.0         # 停推段判定阈（秒）
W12_CARD = 31.25      # W12 卡面参考值（计数/s）
W12_R1R3_MED = 31.2484  # W12 R1-R3 实测中位（计数/s）
FIELD_KEYS = ("mode_A8B238", "A8E9A0", "ABCD58", "B0CE88", "87E8E0")


def load_ndjson(path):
    samples, events = [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            k = rec.get("kind")
            if k == "sample":
                samples.append(rec)
            elif k in ("event", "ui_watch", "meta", "meta_end"):
                events.append(rec)
    return samples, events


def make_windows(t0, samples, win_s=WIN_S, min_dt=MIN_DT_S):
    """固定网格窗；窗边界参考拍=边界时刻前最后一个 ok 拍（共享边界，无缝拼合）。"""
    ts = [s["t_mono_ns"] for s in samples]
    fs = [s["frame"] for s in samples]
    if len(ts) < 2:
        return []
    span = ts[-1] - ts[0]
    win_ns = int(win_s * 1e9)
    n_win = int(span // win_ns) + (1 if span % win_ns else 0)
    out = []
    for k in range(n_win):
        b_start = ts[0] + k * win_ns
        b_end = ts[0] + (k + 1) * win_ns
        if k == 0:
            i0 = 0
        else:
            i0 = bisect.bisect_right(ts, b_start) - 1
            if i0 < 0:
                i0 = 0
        i1 = bisect.bisect_right(ts, b_end) - 1
        note = ""
        if i1 <= i0:
            note = "窗内无新增 ok 拍"
        dt = (ts[i1] - ts[i0]) / 1e9
        df = fs[i1] - fs[i0]
        valid = (i1 > i0) and dt >= min_dt
        if i1 > i0 and dt < min_dt:
            note = (note + " " if note else "") + "partial(Δt<%.0fs)" % min_dt
        if not note:
            note = "ok" if valid else "invalid"
        out.append({
            "window": k,
            "start_rel_s": round((b_start - t0) / 1e9, 3),
            "end_rel_s": round((b_end - t0) / 1e9, 3),
            "ref_start_rel_s": round((ts[i0] - t0) / 1e9, 3),
            "ref_end_rel_s": round((ts[i1] - t0) / 1e9, 3),
            "dt_real_s": round(dt, 3),
            "frame_start": fs[i0], "frame_end": fs[i1],
            "dframe": df,
            "rate_counts_per_s": round(df / dt, 4) if (i1 > i0 and dt > 0) else None,
            "valid": bool(valid),
            "note": note.strip(),
        })
    return out


def drift_stats(windows):
    vals = [w for w in windows if w["valid"] and w["rate_counts_per_s"] is not None]
    rates = [w["rate_counts_per_s"] for w in vals]
    res = {"n_windows_total": len(windows), "n_windows_valid": len(rates)}
    if not rates:
        res["insufficient"] = True
        return res
    n3 = len(rates) // 3
    res["n3"] = n3
    med_first = med_last = None
    drop_pct = None
    if n3 >= 1:
        med_first = round(statistics.median(rates[:n3]), 4)
        med_last = round(statistics.median(rates[-n3:]), 4)
        drop_pct = round((med_first - med_last) / med_first * 100.0, 4) \
            if med_first else None
    res["median_first_third"] = med_first
    res["median_last_third"] = med_last
    res["drop_pct"] = drop_pct
    # 斜率：全有效窗 rate~窗序号 最小二乘
    xs = [w["window"] for w in vals]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(rates) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, rates))
    res["slope_per_window"] = round(sxy / sxx, 6) if sxx else None
    res["rate_min"] = round(min(rates), 4)
    res["rate_max"] = round(max(rates), 4)
    res["rate_mean"] = round(my, 4)
    res["rates_first_n3"] = rates[:n3]
    res["rates_last_n3"] = rates[-n3:]
    # 拐点（判漂移时才有意义；这里按定义先算出首个跌破点供报告引用）
    if med_first:
        thr = KNEE_FACTOR * med_first
        for w in vals:
            if w["rate_counts_per_s"] < thr:
                res["knee"] = {"window": w["window"],
                               "start_rel_s": w["start_rel_s"],
                               "rate": w["rate_counts_per_s"],
                               "threshold": round(thr, 4)}
                break
    res["insufficient"] = False
    return res


def find_stalls(samples, t0):
    stalls = []
    run_start = 0
    for i in range(1, len(samples) + 1):
        if i == len(samples) or samples[i]["frame"] != samples[run_start]["frame"]:
            seg = samples[run_start:i]
            if len(seg) >= 2:
                sd = (seg[-1]["t_mono_ns"] - seg[0]["t_mono_ns"]) / 1e9
                if sd >= STALL_S:
                    fg = [bool(s.get("win_foreground")) for s in seg]
                    stalls.append({
                        "start_rel_s": round((seg[0]["t_mono_ns"] - t0) / 1e9, 3),
                        "end_rel_s": round((seg[-1]["t_mono_ns"] - t0) / 1e9, 3),
                        "duration_s": round(sd, 3),
                        "frame": seg[0]["frame"],
                        "n_ok_ticks": len(seg),
                        "win_foreground_all_true": all(fg),
                        "win_foreground_false_ratio": round(
                            sum(1 for x in fg if not x) / len(fg), 3),
                    })
            run_start = i
    return stalls


def field_snapshot(samples, t_a, t_b):
    seg = [s for s in samples if t_a <= s["t_mono_ns"] <= t_b]
    out = {"n_samples": len(seg)}
    if seg:
        out["span_s"] = round((seg[-1]["t_mono_ns"] - seg[0]["t_mono_ns"]) / 1e9, 3)
        out["t_utc_first"] = seg[0]["t_utc_iso"]
        out["t_utc_last"] = seg[-1]["t_utc_iso"]
    for key in FIELD_KEYS:
        vals = [s.get(key) for s in seg if s.get(key) is not None]
        out[key] = {
            "n": len(vals),
            "top": dict(collections.Counter(vals).most_common(5)),
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
        }
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--ndjson", default=None,
                    help="NDJSON 路径（默认同目录 out/run.ndjson）")
    ap.add_argument("--meta", default=None, help="meta.json 路径（默认同目录）")
    ap.add_argument("--out-dir", default=None, help="输出目录（默认 NDJSON 同目录）")
    a = ap.parse_args()
    nd_path = Path(a.ndjson) if a.ndjson else \
        Path(__file__).parent / "out" / "run.ndjson"
    meta_path = Path(a.meta) if a.meta else nd_path.parent / "meta.json"
    out_dir = Path(a.out_dir) if a.out_dir else nd_path.parent
    samples, events = load_ndjson(nd_path)
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    ingame_ok = [s for s in samples
                 if s.get("phase") == "ingame" and s.get("read_status") == "ok"]
    ingame_all = [s for s in samples if s.get("phase") == "ingame"]
    post_end_ok = [s for s in samples
                   if s.get("phase") == "post_end" and s.get("read_status") == "ok"]
    post_end_all = [s for s in samples if s.get("phase") == "post_end"]

    res = {"ndjson": str(nd_path), "generated_note":
           "离线重算自 NDJSON；判据与 longrun_probe.py predeclared_analysis_plan 一致",
           "unit_note": "速率单位=计数/s（Δframe/真实Δt），非 FPS；30ms 轮询非逐帧"}

    # ---- 读失败（有效局内段；保留不填补） ----
    fails = [s for s in ingame_all if s.get("read_status") != "ok"]
    cur = longest_fail = 0
    for s in ingame_all:
        if s.get("read_status") != "ok":
            cur += 1
            longest_fail = max(longest_fail, cur)
        else:
            cur = 0
    res["read_fail"] = {
        "n_fail": len(fails),
        "longest_consecutive": longest_fail,
        "failed_fields_union": sorted({f2 for s in fails
                                       for f2 in (s.get("read_fail_detail") or [])}),
    }

    if len(ingame_ok) < 2:
        res["insufficient"] = True
        res["tier"] = "[数据不足]"
        res["insufficient_reason"] = "有效局内段 ok 拍 <2（err=%s）" % meta.get("error")
        (out_dir / "analysis.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True,
                       default=str), encoding="utf-8")
        print("有效局内段不足：", res["insufficient_reason"])
        return 1

    t0 = ingame_ok[0]["t_mono_ns"]
    t_last = ingame_ok[-1]["t_mono_ns"]
    dur = (t_last - t0) / 1e9
    f_first, f_last = ingame_ok[0]["frame"], ingame_ok[-1]["frame"]
    overall_rate = (f_last - f_first) / dur if dur > 0 else None

    # ---- 主判据段（有效局内段） ----
    windows = make_windows(t0, ingame_ok)
    ds = drift_stats(windows)
    res["primary"] = {
        "segment_def": "phase=ingame（首个 frame>0 起）至自然结束/目标；含加载尾（披露）",
        "duration_s": round(dur, 3),
        "n_samples_ok": len(ingame_ok),
        "frame_first": f_first, "frame_last": f_last,
        "frame_net_delta": f_last - f_first,
        "overall_rate_counts_per_s": round(overall_rate, 4) if overall_rate else None,
        "windows": windows,
        "drift": ds,
    }

    # ---- 敏感性段（W12 同口径门起点之后） ----
    gate_t = None
    for e in events:
        if e.get("event") == "gate_marker_w12_style":
            gate_t = e["t_mono_ns"]
            break
    if gate_t:
        sec_ok = [s for s in ingame_ok if s["t_mono_ns"] >= gate_t]
        if len(sec_ok) >= 2:
            t0s = sec_ok[0]["t_mono_ns"]
            swin = make_windows(t0s, sec_ok)
            sds = drift_stats(swin)
            res["secondary"] = {
                "segment_def": "W12 同口径门（gate_marker）之后至段末；同一预设阈值",
                "duration_s": round((sec_ok[-1]["t_mono_ns"] - t0s) / 1e9, 3),
                "n_samples_ok": len(sec_ok),
                "overall_rate_counts_per_s": round(
                    (sec_ok[-1]["frame"] - sec_ok[0]["frame"])
                    / ((sec_ok[-1]["t_mono_ns"] - t0s) / 1e9), 4),
                "windows": swin,
                "drift": sds,
            }
        else:
            res["secondary"] = {"note": "门后 ok 拍不足"}
    else:
        res["secondary"] = {"note": "gate_marker 未触发（elapsed<15s 即结束等）"}

    # ---- 分档（预设） ----
    if dur < 300.0:
        tier = "[数据不足]"
        reason = "有效局内段 %.1fs < 300s（phase_stop=%s，natural_end=%s）" % (
            dur, meta.get("phase_stop"),
            (meta.get("sampling") or {}).get("natural_end") is not None)
    elif ds.get("drop_pct") is not None and ds["drop_pct"] > DRIFT_PCT:
        tier = "[观测到下行漂移]"
        reason = "降幅 %.3f%% > 0.5%%（预设阈值）" % ds["drop_pct"]
    else:
        tier = "[未观测到漂移]"
        reason = "降幅 %s ≤ 0.5%%（预设阈值；负值=末 1/3 反而略升）" % ds.get("drop_pct")
    res["tier"] = tier
    res["tier_reason"] = reason

    # ---- 拐点相关字段（只给相关，不归因） ----
    if tier == "[观测到下行漂移]" and ds.get("knee"):
        kw = ds["knee"]
        k_ref = next(w for w in windows if w["window"] == kw["window"])
        ta = t0 + int((k_ref["start_rel_s"] - 30.0) * 1e9)
        tb_start = t0 + int(k_ref["start_rel_s"] * 1e9)
        tb_end = t0 + int(k_ref["end_rel_s"] * 1e9)
        tc = tb_end + int(30.0 * 1e9)
        res["knee_context"] = {
            "knee": kw,
            "window": k_ref,
            "before_30s": field_snapshot(ingame_ok, max(ta, t0), tb_start),
            "window_itself": field_snapshot(ingame_ok, tb_start, tb_end),
            "after_30s": field_snapshot(ingame_ok, tb_end, min(tc, t_last)),
            "note": "只给字段相关变化；不归因",
        }

    # ---- 停推段 ----
    stalls = find_stalls(ingame_ok, t0)
    for st in stalls:
        if not st["win_foreground_all_true"]:
            st["label"] = "伴随失焦（win_foreground=false）"
        else:
            st["label"] = "未知原因的停推（前台保持、采样段零输入）"
    ne_t = None
    for e in events:
        if e.get("event") == "natural_end":
            ne_t = e["t_mono_ns"]
            break
    if ne_t:
        for st in stalls:
            st_t0 = t0 + int(st["start_rel_s"] * 1e9)
            if abs(st_t0 - ne_t) <= 5e9:
                st["note_near_natural_end"] = \
                    "紧邻 natural_end 检测时刻 ±5s（时间相关，非因果）"
    post_stalls = find_stalls(post_end_ok, t0) if len(post_end_ok) >= 2 else []
    for st in post_stalls:
        st["label"] = "post_end（自然结束补采段；结算屏冻结属预期，不计入有效局内段）"
    res["stalls"] = {
        "ingame": stalls,
        "ingame_count": len(stalls),
        "ingame_max_s": round(max((s["duration_s"] for s in stalls), default=0.0), 3),
        "post_end": post_stalls,
        "post_end_count": len(post_stalls),
        "rule": "连续 ok 拍 frame 相同且真实跨度≥1.0s；fail 拍不中断 run（帧未变），"
                "跨度按真实时间计",
    }

    # ---- 零输入证据（GetLastInputInfo，1s 留痕） ----
    watches = [e for e in events if e.get("kind") == "ui_watch"]
    dwts = [w.get("last_input_dwtime") for w in watches
            if w.get("last_input_dwtime") is not None]
    li_changes = sum(1 for i in range(1, len(dwts)) if dwts[i] != dwts[i - 1])
    res["zero_input_evidence"] = {
        "n_ui_watch": len(watches),
        "last_input_dwtime_first": dwts[0] if dwts else None,
        "last_input_dwtime_last": dwts[-1] if dwts else None,
        "dwtime_change_count": li_changes,
        "interpretation": "dwtime 全程不变 ⇒ 采样段（含置前之后）系统级零输入；"
                          "有变化则如实记录（存在输入）",
        "fg_false_ratio_ingame": round(
            sum(1 for s in ingame_all if not s.get("win_foreground"))
            / max(len(ingame_all), 1), 4),
    }

    # ---- 与 W12 对照 ----
    if overall_rate:
        res["w12_comparison"] = {
            "this_overall_rate": round(overall_rate, 4),
            "w12_card_value": W12_CARD,
            "dev_vs_card_pct": round((overall_rate - W12_CARD) / W12_CARD * 100, 3),
            "w12_r1r3_median": W12_R1R3_MED,
            "dev_vs_r1r3_median_pct": round(
                (overall_rate - W12_R1R3_MED) / W12_R1R3_MED * 100, 3),
            "note": "W12=125s 短窗基线；本卡=600s 长窗；只描述偏差",
        }

    res["natural_end"] = {
        "detected": ne_t is not None,
        "t_utc": next((e["t_utc_iso"] for e in events
                       if e.get("event") == "natural_end"), None),
        "buttons": next((e.get("detail", {}).get("buttons") for e in events
                         if e.get("event") == "natural_end"), None),
        "meta_phase_stop": meta.get("phase_stop"),
    }
    res["meta_map"] = meta.get("map")
    res["meta_pid"] = meta.get("pid")
    res["meta_is32"] = meta.get("is32")
    res["meta_carrier"] = meta.get("carrier")
    res["meta_restore_ok"] = all(
        r.get("sha_match") and r.get("byte_identical_to_baseline")
        for r in (meta.get("restore_rows") or [])
        if r.get("file") in ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak"))
    res["meta_residual_after"] = meta.get("residual_after")

    # ---- windows.csv（有效局内段，每 10s 窗一行） ----
    csv_path = out_dir / "windows.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        f.write("window,start_rel_s,end_rel_s,ref_start_rel_s,ref_end_rel_s,"
                "dt_real_s,frame_start,frame_end,dframe,rate_counts_per_s,"
                "valid,note\n")
        for w in windows:
            f.write("%d,%.3f,%.3f,%.3f,%.3f,%.3f,%d,%d,%d,%s,%s,%s\n" % (
                w["window"], w["start_rel_s"], w["end_rel_s"],
                w["ref_start_rel_s"], w["ref_end_rel_s"], w["dt_real_s"],
                w["frame_start"], w["frame_end"], w["dframe"],
                ("%0.4f" % w["rate_counts_per_s"]) if w["rate_counts_per_s"]
                is not None else "",
                w["valid"], w["note"]))
    res["windows_csv"] = str(csv_path)

    (out_dir / "analysis.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True, default=str),
        encoding="utf-8")

    # ---- 控制台摘要 ----
    print("tier=%s  %s" % (tier, reason))
    print("有效局内段: dur=%.1fs ok=%d fail=%d frame %d→%d rate=%.4f/s" %
          (dur, len(ingame_ok), len(fails), f_first, f_last, overall_rate or 0))
    print("10s 窗: N=%d valid=%d n3=%d" %
          (ds["n_windows_total"], ds["n_windows_valid"], ds.get("n3")))
    print("  首 1/3 中位=%s  末 1/3 中位=%s  降幅=%s%%" %
          (ds.get("median_first_third"), ds.get("median_last_third"),
           ds.get("drop_pct")))
    print("  斜率=%s (计数/s per 10s)  范围=[%s, %s]" %
          (ds.get("slope_per_window"), ds.get("rate_min"), ds.get("rate_max")))
    if ds.get("knee"):
        print("  首个跌破 0.995×首1/3 中位的窗: %s" % ds["knee"])
    if "secondary" in res and res["secondary"].get("drift"):
        sd2 = res["secondary"]["drift"]
        print("敏感性段(门后): dur=%.1fs 首/末1/3中位=%s/%s 降幅=%s%% 斜率=%s" %
              (res["secondary"]["duration_s"], sd2.get("median_first_third"),
               sd2.get("median_last_third"), sd2.get("drop_pct"),
               sd2.get("slope_per_window")))
    print("停推: 局内=%d 段（最长 %.2fs） post_end=%d 段" %
          (res["stalls"]["ingame_count"], res["stalls"]["ingame_max_s"],
           res["post_end_count"] if False else res["stalls"]["post_end_count"]))
    for st in stalls:
        print("  stall @%.1fs..%.1fs (%.2fs) frame=%d fg_all=%s %s %s" %
              (st["start_rel_s"], st["end_rel_s"], st["duration_s"], st["frame"],
               st["win_foreground_all_true"], st["label"],
               st.get("note_near_natural_end", "")))
    print("零输入证据: ui_watch=%d dwtime变化=%d fg_false_ratio=%s" %
          (res["zero_input_evidence"]["n_ui_watch"],
           res["zero_input_evidence"]["dwtime_change_count"],
           res["zero_input_evidence"]["fg_false_ratio_ingame"]))
    print("W12 对照: %s" % json.dumps(res.get("w12_comparison", {}),
                                      ensure_ascii=False))
    print("已写出 %s 和 %s" % (csv_path, out_dir / "analysis.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
