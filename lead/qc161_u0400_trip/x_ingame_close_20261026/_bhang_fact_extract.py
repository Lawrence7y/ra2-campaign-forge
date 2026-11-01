# -*- coding: utf-8 -*-
"""_bhang_fact_extract.py — B 线机制分析员事实提取（离线只读，零真机）。

对 P3e×3（早窗三趟）+ 对照（P3_G1B1/P3m_MENU）+ 旧 MAIN 两趟做 timeline.json
逐行对齐 diff：latch 时点（exitstate 0→1）、latch 前后每秒各轴读数、
latched-hang 趟 vs 自然退趟逐字段差异。只读不写（除本件与 stdout）。
"""
import json
import sys
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip")
EARLY = [
    "c2ab_x/20261028T204123_9001_P3e_EARLY_MENU",   # latched-hang
    "c2ab_x/20261028T204921_9001_P3e_EARLY_MENU",   # 自然退
    "c2ab_x/20261028T205108_9001_P3e_EARLY_MENU",   # 自然退
]
OTHERS = [
    "c2ab_x/20261028T091330_0001_P3_G1B1",          # 战斗关窗对照
    "c2ab_x/20261028T092052_0001_P3m_MENU",         # 菜单就绪 44.8s 关对照
    "d09b/20261025T110445_MAIN_OnNoDbg",            # 旧 MAIN
    "d09b/20261025T112422_MAIN_OnNoDbg",            # 旧 MAIN
]


def load(rel):
    p = BASE / rel / "timeline.json"
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def rec(rel):
    with open(BASE / rel / "_rec.json", "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def scalar(v):
    """tri_read 可能返回 {"state": kind}；归一为可打印串。"""
    if isinstance(v, dict):
        return v.get("state", "?")
    return v


def latch_analysis(rel):
    j = load(rel)
    r = rec(rel)
    rows = j["close_rows"]
    out = {"rel": rel, "n_rows": len(rows)}
    t_close = None
    # 关窗时刻：close_delivery.t（驱动 rec）；close_rows[0].t 是关窗后首个样本
    t_close = r["close_delivery"]["t"]
    out["t_close"] = t_close
    out["closed_at_s"] = r["closed_at_s"]
    # 逐行找 exitstate 变迁
    trans = []
    prev = None
    for i, row in enumerate(rows):
        es = scalar(row.get("exitstate"))
        if prev is not None and es != prev:
            trans.append((i, row["t"], round(row["t"] - t_close, 3), prev, es))
        prev = es
    out["exitstate_transitions"] = trans
    # hwnd/singleton 首个归零行
    for key in ("hwnd", "singleton"):
        first0 = None
        for row in rows:
            if scalar(row.get(key)) == 0:
                first0 = (row["t"], round(row["t"] - t_close, 3))
                break
        out["%s_first_zero" % key] = first0
        # 是否有非零→非零变化
        vals = [scalar(row.get(key)) for row in rows]
        nz = [(row["t"], round(row["t"] - t_close, 3), v) for row, v in zip(rows, vals) if v != 0]
        out["%s_nonzero_rows" % key] = len(nz)
        if nz:
            out["%s_nonzero_first" % key] = (nz[0][1], nz[0][2])
            out["%s_nonzero_last" % key] = (nz[-1][1], nz[-1][2])
    # frame 轴：非零帧的范围与最后变化
    fr = [(row["t"], scalar(row.get("frame"))) for row in rows]
    fr_nz = [(t, v) for t, v in fr if v != 0]
    out["frame_nonzero_rows"] = len(fr_nz)
    if fr_nz:
        out["frame_nonzero_first"] = (round(fr_nz[0][0] - t_close, 3), fr_nz[0][1])
        out["frame_nonzero_last"] = (round(fr_nz[-1][0] - t_close, 3), fr_nz[-1][1])
    # frame 是否有推进（相邻行变化）
    moves = []
    lastv = None
    for t, v in fr:
        if lastv is not None and v != lastv and v != 0:
            moves.append((round(t - t_close, 3), v))
        lastv = v
    out["frame_changes_n"] = len(moves)
    if moves:
        out["frame_first_change"] = moves[0]
        out["frame_last_change"] = moves[-1]
    # tick 轴
    ticks = sorted(set(str(scalar(row.get("tick"))) for row in rows))
    out["tick_values"] = ticks[:8]
    # wait 轴
    waits = sorted(set(row.get("wait") for row in rows))
    out["wait_values"] = waits
    # code 出现行
    codes = [(round(row["t"] - t_close, 3), row.get("code")) for row in rows if row.get("code") is not None]
    out["code_rows"] = codes[:5]
    out["exited"] = r["exited"]
    out["exit_kind"] = r["exit_kind"]
    out["exit_after_close_s"] = r["exit_after_close_s"]
    out["final_exitcode"] = r["final_exitcode"]
    # latch 时点（exitstate 0→1）
    latches = [tr for tr in trans if str(tr[3]) == "0" and str(tr[4]) == "1"]
    out["latch"] = latches
    # hold_tl（关窗前）窗口枚举
    hold = j.get("hold_tl", [])
    out["hold_n"] = len(hold)
    out["hold_exitstate"] = [scalar(h.get("exitstate")) for h in hold]
    out["hold_frame"] = [scalar(h.get("frame")) for h in hold]
    out["hold_hwnd"] = [scalar(h.get("hwnd")) for h in hold]
    out["hold_visible_n"] = [len(h.get("visible_windows", [])) for h in hold]
    out["hold_ws_kb"] = [h.get("ws_kb") for h in hold]
    out["window_at_s"] = r.get("window_at_s")
    out["watch_s"] = r.get("watch_s")
    # latch 后样本数/时长
    if latches:
        lt = latches[0][1]
        after = [row for row in rows if row["t"] >= lt]
        out["rows_after_latch"] = len(after)
        out["latch_to_last_row_s"] = round(rows[-1]["t"] - lt, 3)
        # latch 后 exitstate 是否恒 1
        out["exitstate_after_latch_set"] = sorted(set(str(scalar(row.get("exitstate"))) for row in after))
        # latch 后 hwnd/singleton 是否恒 0
        out["hwnd_after_latch_set"] = sorted(set(str(scalar(row.get("hwnd"))) for row in after))
        out["singleton_after_latch_set"] = sorted(set(str(scalar(row.get("singleton"))) for row in after))
        out["frame_after_latch_set"] = sorted(set(str(scalar(row.get("frame"))) for row in after))[:8]
        # latch 前 3 行明细
        li = latches[0][0]
        out["rows_before_latch"] = [
            {k: scalar(row.get(k)) for k in ("t", "wait", "exitstate", "frame", "hwnd", "singleton", "tick")}
            for row in rows[max(0, li - 3):li]
        ]
        out["latch_row_detail"] = rows[li]
        out["rows_after_latch_detail_3"] = [
            {k: scalar(row.get(k)) for k in ("t", "wait", "exitstate", "frame", "hwnd", "singleton", "tick")}
            for row in rows[li + 1:li + 4]
        ]
    return out


def sample_per_second(rel, t_anchor, span=(0, 20)):
    """以关窗为 0 点，每 ~1 s 抽一行（最近样本），显示各轴。"""
    j = load(rel)
    rows = j["close_rows"]
    sel = []
    target = t_anchor + span[0]
    while target <= t_anchor + span[1]:
        best = None
        for row in rows:
            if best is None or abs(row["t"] - target) < abs(best["t"] - target):
                best = row
        if best and abs(best["t"] - target) <= 0.55:
            sel.append((round(best["t"] - t_anchor, 2), best))
        target += 1.0
    return sel


def show_row(row, keys):
    parts = []
    for k in keys:
        v = scalar(row.get(k))
        if k == "t":
            continue
        parts.append("%s=%s" % (k, v))
    return " ".join(parts)


def main():
    print("=" * 100)
    print("A. 三趟早窗 latch 分析")
    print("=" * 100)
    results = {}
    for rel in EARLY:
        res = latch_analysis(rel)
        results[rel] = res
        print("\n### %s" % rel)
        for k in ("closed_at_s", "window_at_s", "hold_exitstate", "hold_frame", "hold_hwnd",
                  "hold_visible_n", "hold_ws_kb", "exitstate_transitions", "latch",
                  "hwnd_first_zero", "singleton_first_zero", "hwnd_nonzero_first", "hwnd_nonzero_last",
                  "singleton_nonzero_first", "singleton_nonzero_last",
                  "frame_nonzero_rows", "frame_nonzero_first", "frame_nonzero_last",
                  "frame_changes_n", "frame_first_change", "frame_last_change",
                  "tick_values", "wait_values", "code_rows",
                  "exited", "exit_kind", "exit_after_close_s", "final_exitcode",
                  "rows_after_latch", "latch_to_last_row_s",
                  "exitstate_after_latch_set", "hwnd_after_latch_set",
                  "singleton_after_latch_set", "frame_after_latch_set"):
            print("  %s = %s" % (k, results[rel].get(k)))
        if results[rel].get("rows_before_latch"):
            print("  latch 前 3 行:")
            for row in results[rel]["rows_before_latch"]:
                print("    %s" % show_row(row, ("t", "wait", "exitstate", "frame", "hwnd", "singleton", "tick")))
            print("  latch 行:")
            print("    %s" % show_row(results[rel]["latch_row_detail"], ("t", "wait", "exitstate", "frame", "hwnd", "singleton", "tick")))
            print("  latch 后 3 行:")
            for row in results[rel]["rows_after_latch_detail_3"]:
                print("    %s" % show_row(row, ("t", "wait", "exitstate", "frame", "hwnd", "singleton", "tick")))

    print("\n" + "=" * 100)
    print("B. latch 对齐（以各趟 latch 时刻为 0 点，±3 s 全样本逐字段）")
    print("=" * 100)
    for rel in EARLY:
        res = results[rel]
        if not res["latch"]:
            print("\n### %s —— 无 latch（不适用）" % rel)
            continue
        lt = res["latch"][0][1]
        j = load(rel)
        rows = j["close_rows"]
        lo = [row for row in rows if lt - 3.0 <= row["t"] < lt]
        hi = [row for row in rows if lt <= row["t"] <= lt + 3.0]
        print("\n### %s  latch_t=%.3f（相对关窗 +%.3f s）" % (rel, lt, res["latch"][0][2]))
        print("  latch 前（每 0.1s 一行，共 %d 行；仅列与上一行有差异的）" % len(lo))
        prev = None
        for row in lo:
            cur = tuple(scalar(row.get(k)) for k in ("exitstate", "frame", "hwnd", "singleton", "tick", "wait"))
            if prev is None or cur != prev:
                print("    +%.3f %s" % (row["t"] - res["t_close"], show_row(row, ("exitstate", "frame", "hwnd", "singleton", "tick", "wait"))))
            prev = cur
        print("  latch 后（共 %d 行；仅列与上一行有差异的）" % len(hi))
        prev = None
        for row in hi:
            cur = tuple(scalar(row.get(k)) for k in ("exitstate", "frame", "hwnd", "singleton", "tick", "wait"))
            if prev is None or cur != prev:
                print("    +%.3f %s" % (row["t"] - res["t_close"], show_row(row, ("exitstate", "frame", "hwnd", "singleton", "tick", "wait"))))
            prev = cur

    print("\n" + "=" * 100)
    print("C. 对照趟（战斗关窗 P3 / 菜单就绪 P3m）exitstate 轴")
    print("=" * 100)
    for rel in OTHERS[:2]:
        res = latch_analysis(rel)
        print("\n### %s" % rel)
        for k in ("closed_at_s", "exitstate_transitions", "exited", "exit_kind",
                  "exit_after_close_s", "final_exitcode", "tick_values", "wait_values",
                  "hold_exitstate", "hold_visible_n"):
            print("  %s = %s" % (k, res.get(k)))
        # frame 变化范围
        print("  frame_changes_n = %s" % res.get("frame_changes_n"))
        print("  frame_last_change = %r" % (res.get("frame_last_change"),))
        print("  hwnd_first_zero = %r" % (res.get("hwnd_first_zero"),))

    print("\n" + "=" * 100)
    print("D. 旧 MAIN 两趟对照")
    print("=" * 100)
    for rel in OTHERS[2:]:
        try:
            j = load(rel)
            r = rec(rel)
        except FileNotFoundError as e:
            print("\n### %s —— 文件缺失：%s" % (rel, e))
            continue
        rows = j["close_rows"]
        print("\n### %s" % rel)
        print("  keys = %s" % list(j.keys()))
        print("  rec: closed=%s exited=%s exit_kind=%s exit_after=%s code=%s window_at=%s" % (
            r.get("closed_at_s"), r.get("exited"), r.get("exit_kind"),
            r.get("exit_after_close_s"), r.get("final_exitcode"), r.get("window_at_s")))
        t_close = r["close_delivery"]["t"]
        prev = None
        print("  close_rows（%d 行）关键变迁（列与上一行有差异的）:" % len(rows))
        shown = 0
        for row in rows:
            cur = tuple(str(scalar(row.get(k))) for k in ("exitstate", "frame", "hwnd", "singleton", "tick"))
            if prev is None or cur != prev:
                print("    +%.3f %s" % (row["t"] - t_close, show_row(row, ("exitstate", "frame", "hwnd", "singleton", "tick", "wait"))))
                shown += 1
                if shown > 40:
                    print("    ...（截断）")
                    break
            prev = cur
        hold = j.get("hold_tl", [])
        if hold:
            print("  hold 期 exitstate=%s" % [scalar(h.get("exitstate")) for h in hold])

    print("\n" + "=" * 100)
    print("E. latched-hang 趟 latch 后每 10 s 抽样（全程 101.7 s 形态）")
    print("=" * 100)
    rel = EARLY[0]
    res = results[rel]
    lt = res["latch"][0][1]
    sel = sample_per_second(rel, lt, span=(0, 101))
    for off, row in sel:
        if round(off) % 10 == 0 or off < 1:
            print("  latch%+8.2f s  %s" % (off, show_row(row, ("exitstate", "frame", "hwnd", "singleton", "tick", "wait", "code"))))


if __name__ == "__main__":
    main()
