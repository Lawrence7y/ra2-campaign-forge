# -*- coding: utf-8 -*-
"""stall_judge.py - measure 窗停滞判读标准实现（离线只读，§515–§526 结论固化）

本文件把 §526 的判据流程落成**可执行件**，供后续任何轮次直接调用，
避免每次重写导致口径漂移（本程已因重写踩过两次坑：枚举遗漏、分母假相关）。

★ 口径来源（引用时须注明）：
  - 停滞时长 = **口径 B**（D-12② 裁「B 为准」）：卡住帧值首末拍跨度，
    t(段内末拍) − t(段内首拍)，≥ T 计入，占比 ÷ 窗跨度。
  - 口径 C（算到下一推进拍）是**已登记陷阱**，本文件不提供，若需对照须显式注明。
  - occ_a 是 **C 型 interior + C 型 head + B 型 tail** 的混合口径（§515 勘误），
    与口径 B **不同源**，跨线比数值前须先统一。

★ 判读流程（§526 §6 固化为代码）：
  1. 有推进？       f 从未变化 ⇒ 全窗冻结窗（另类，不计停滞）
  2. f[0] == 0？    是 ⇒ **加载段型**：主导段是帧钟未启动的空白，不计入引擎停摆
  3. 最长段占 > 80%？
       是 ⇒ **单段主导（引擎停摆型）**：报 freezeStart；B% ≡ (span−freezeStart)/span
       否 ⇒ **多次型（整窗低帧率）**：帧号严格递增（簇内），报段数与最长段
  4. 必附采样缺口（帧沿处 >10ms 占比）；> 5% 标「含采样成分」，不得直接作机制论证
  5. 单段窗比较严重程度时报 freezeStart，不只报 B%

★ 用法（作为脚本）：
    python -I -X utf8 stall_judge.py <measure_wN.json 路径> [...]
  或作为模块：
    from stall_judge import judge_window, judge_file

本文件**只读**，不写任何数据；不做机制定谳。
"""

import json
import os
import sys

T_DEFAULT = 0.100        # 停滞阈值（秒），D-12② 口径 B 钉死
GAP_THRESH = 0.010       # 帧沿缺口阈值（秒）
SINGLE_SHARE = 0.80      # 单段主导判据：最长段占 > 此值
STALL_MIN = 25.0         # 滞态门槛（STALL_AUDIT §1 的 R4 细分）
GAP_WARN_PCT = 5.0       # 帧沿缺口占 span 超过此值须加警告


def _platforms(ts, fs, thr):
    """B 口径平台列表：[(i_start, i_end, dur, frame_value)]，只含 dur > thr。"""
    n = len(ts)
    out = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    d = ts[j] - ts[0]
    if d > thr:
        out.append((0, j, d, fs[0]))
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        dd = ts[k] - ts[i]
        if dd > thr:
            out.append((i, k, dd, fs[i]))
        i = k + 1
    return out


def judge_window(ts, fs, thr=T_DEFAULT):
    """对单个窗给出结构化判读。返回 dict；输入无效时返回 None。

    返回字段：
      kind          'no_advance_window' | 'loading_segment' | 'single_segment' | 'multi_segment'
      b_pct         口径 B 停滞占比（%）
      span          窗跨度（t[-1]-t[0]）
      n_segs        计入段数
      longest_share 最长段占
      freeze_start  帧号最后一次变化的相对时刻（无帧沿时为 None）
      identity_ok   单段型下 B% 是否等于 (span-freeze)/span（±0.01pp）；其它类型 None
      gap_pct       帧沿处 >10ms 缺口占 span（%）
      gap_warning   是否 > GAP_WARN_PCT
      f0 / f_last   窗首尾帧号
      notes         判读说明列表（人读）
    """
    n = len(ts)
    if not ts or not fs or n < 2:
        return None
    t0 = ts[0]
    span = ts[-1] - t0
    if span <= 0:
        return None

    f0, f_last = fs[0], fs[-1]
    has_edge = any(fs[i] != fs[i - 1] for i in range(1, n))

    plats = _platforms(ts, fs, thr)
    tot = sum(p[2] for p in plats)
    b_pct = 100.0 * tot / span
    n_segs = len(plats)
    longest_share = (max(p[2] for p in plats) / tot) if tot else 0.0

    freeze_start = None
    if has_edge:
        last = None
        for i in range(1, n):
            if fs[i] != fs[i - 1]:
                last = i
        freeze_start = ts[last] - t0

    edge_gap = sum(ts[i] - ts[i - 1] for i in range(1, n)
                   if fs[i] != fs[i - 1] and ts[i] - ts[i - 1] > GAP_THRESH)
    gap_pct = 100.0 * edge_gap / span if span else 0.0

    notes = []
    if not has_edge:
        kind = "no_advance_window"
        notes.append("窗内帧号从未变化 ⇒ 全窗冻结窗/拒采窗，不计入停滞统计")
    elif n_segs == 0 or b_pct < STALL_MIN / 10.0:
        # ★ 修正：零/近零停滞窗不应被归入「多次型」——那不是「多次短卡」，是「没有卡」
        kind = "fast"
        notes.append("快态窗：无 >%.0fms 的停滞段（或占比极低 %.4f%%）⇒ 无停滞" %
                     (thr * 1000, b_pct))
    elif f0 == 0:
        kind = "loading_segment"
        notes.append("f[0]==0 ⇒ 加载段型：帧钟尚未启动，主导段是加载空白，不计入引擎停摆")
    elif longest_share > SINGLE_SHARE and b_pct >= STALL_MIN:
        kind = "single_segment"
        notes.append("单段主导（引擎停摆型）：满速运行后突然冻结、一去不回")
        notes.append("比较严重程度时请报 freezeStart（%.3fs），不只报 B%%" % freeze_start)
    else:
        kind = "multi_segment"
        notes.append("多次型（整窗低帧率）：帧号连续慢爬，段数由阈值切分而来")
        notes.append("★ 不可表述为「大量独立短阻塞事件」——那是阈值产物")

    identity_ok = None
    counted_positions = []
    if kind == "single_segment" and freeze_start is not None:
        pred = 100.0 * (span - freeze_start) / span
        identity_ok = abs(b_pct - pred) < 0.01
        # ★ §528 订正：该「恒等式」是代数恒等，不是物理判别，不得当作证据。
        #   只有当【唯一计入段 == 末段】时，B% 才必然等于 (span−freeze)/span。
        #   所以本工具只把它作「一致性自检」，明确标注其非证据属性。
        counted_positions = []
        for (s_i, e_i, _d, _fv) in plats:
            if s_i == 0:
                counted_positions.append("FIRST")
            elif e_i == n - 1:
                counted_positions.append("LAST")
            else:
                counted_positions.append("MID")
        only_last = (len(plats) == 1 and counted_positions == ["LAST"])
        if identity_ok and only_last:
            notes.append("一致性自检通过：B% 与 (span−freezeStart)/span 相等 —— "
                         "★ 但这是**代数恒等**（唯一计入段就是末段），**不构成物理证据**（§528）")
        elif identity_ok:
            notes.append("一致性自检通过（B% 与末段占比相等），但计入段含非末段，需注意")
        else:
            notes.append("⚠ 一致性自检未通过（B%=%.4f vs 末段占比 %.4f）——须复核分类前提"
                         % (b_pct, pred))

    gap_warning = gap_pct > GAP_WARN_PCT
    if gap_warning:
        notes.append("⚠ 帧沿缺口占 span %.2f%%（> %.0f%%）⇒ 读数含采样成分，"
                     "不得直接用作机制论证" % (gap_pct, GAP_WARN_PCT))

    return dict(
        kind=kind, b_pct=b_pct, span=span, n_segs=n_segs,
        longest_share=longest_share, freeze_start=freeze_start,
        identity_ok=identity_ok, gap_pct=gap_pct, gap_warning=gap_warning,
        counted_positions=counted_positions,
        f0=f0, f_last=f_last, notes=notes)


def judge_file(path, thr=T_DEFAULT):
    """读一个 measure 窗 JSON 并判读。返回 (dict|None, meta)。"""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    s = d.get("samples") or {}
    ts, fs = s.get("t"), s.get("f")
    meta = dict(trip_id=d.get("trip_id"), verdict=d.get("verdict"),
                units0=(d.get("gate") or {}).get("units0"),
                window=d.get("window"))
    return judge_window(ts, fs, thr), meta


def format_report(path, r, meta):
    name = os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path)
    lines = ["=" * 78, name, "=" * 78]
    if r is None:
        lines.append("  !! 无效窗（samples 缺失或 len(t)<2）")
        return "\n".join(lines)
    lines.append("  类型      : %s" % r["kind"])
    lines.append("  B%%（口径B）: %.4f%%   span=%.3fs   计入段数=%d"
                 % (r["b_pct"], r["span"], r["n_segs"]))
    lines.append("  最长段占  : %.4f" % r["longest_share"])
    if r["freeze_start"] is not None:
        lines.append("  freezeStart: %.4fs" % r["freeze_start"])
    if r["identity_ok"] is not None:
        lines.append("  恒等式    : %s" % ("成立" if r["identity_ok"] else "**不成立**"))
    lines.append("  帧沿缺口  : %.4f%%" % r["gap_pct"])
    lines.append("  f[0]/f[-1]: %s / %s" % (r["f0"], r["f_last"]))
    lines.append("  units0    : %s   verdict=%s   window=%s"
                 % (meta.get("units0"), meta.get("verdict"), meta.get("window")))
    lines.append("  --- 判读 ---")
    for x in r["notes"]:
        lines.append("  · " + x)
    return "\n".join(lines)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        print("用法：python -I -X utf8 stall_judge.py <measure_wN.json> [...]")
        return 2
    rc = 0
    for p in argv[1:]:
        if not os.path.isfile(p):
            print("!! 文件不存在：%s" % p)
            rc = 1
            continue
        r, meta = judge_file(p)
        print(format_report(p, r, meta))
        print()
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
