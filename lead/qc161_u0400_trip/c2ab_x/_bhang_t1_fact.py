# -*- coding: utf-8 -*-
"""_bhang_t1_fact.py — B 线重派机制分析员事实提取（离线只读，零真机，零改动）。

轴：三趟 P3e 早窗（T204123 latched-hang / T204921 / T205108 自然退）+ 对照
（P3_G1B1 战斗关窗、P3m_MENU 就绪关窗）+ 旧 MAIN d09b×2（无 bail）。
产出：latch 时点、hwnd/singleton 归零时点、latch 前后逐字段序列、口径核对
（101.7 vs 104.6）、闩后全程形态。stdout 输出，不写报告文件。
"""
import json
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip")
TRIPS = {
    "HANG":  "c2ab_x/20261028T204123_9001_P3e_EARLY_MENU",
    "NAT1":  "c2ab_x/20261028T204921_9001_P3e_EARLY_MENU",
    "NAT2":  "c2ab_x/20261028T205108_9001_P3e_EARLY_MENU",
    "P3BTL": "c2ab_x/20261028T091330_0001_P3_G1B1",
    "P3M":   "c2ab_x/20261028T092052_0001_P3m_MENU",
    "D09BA": "d09b/20261025T110445_MAIN_OnNoDbg",
    "D09BB": "d09b/20261025T112422_MAIN_OnNoDbg",
}
KEYS = ("exitstate", "frame", "hwnd", "singleton", "tick")


def sc(v):
    return v.get("state", "?") if isinstance(v, dict) else v


def load(rel):
    j = json.load(open(BASE / rel / "timeline.json", encoding="utf-8", errors="replace"))
    r = json.load(open(BASE / rel / "_rec.json", encoding="utf-8", errors="replace"))
    return j, r


def rels(rows, t_close):
    return [(round(row["t"] - t_close, 3), row) for row in rows]


def transitions(rr, key):
    out = []
    prev = None
    for rel, row in rr:
        v = sc(row.get(key))
        if prev is not None and v != prev:
            out.append((rel, prev, v))
        prev = v
    return out


def fact(tag):
    rel = TRIPS[tag]
    j, r = load(rel)
    rows = j.get("close_rows", [])
    t_close = r["close_delivery"]["t"]
    rr = rels(rows, t_close)
    print("=" * 110)
    print("### [%s] %s" % (tag, rel))
    print("  closed_at_s=%s close_rows_n=%d watch_s=%s exited=%s exit_kind=%s exit_after_close_s=%s code=%s" % (
        r.get("closed_at_s"), len(rows), r.get("watch_s"), r.get("exited"),
        r.get("exit_kind"), r.get("exit_after_close_s"), r.get("final_exitcode")))
    # 逐轴变迁
    for k in KEYS + ("wait",):
        tr = transitions(rr, k)
        # 折叠连续重复
        folded = tr[:12]
        print("  %-10s 变迁 %d 处: %s%s" % (k, len(tr),
              [(a, b, c) for a, b, c in folded], " ..." if len(tr) > 12 else ""))
    # latch 时点
    latch = [x for x in transitions(rr, "exitstate") if str(x[1]) == "0" and str(x[2]) == "1"]
    if latch:
        lr = latch[0][0]
        print("  LATCH @ rel=%.3f s" % lr)
        # 口径核对
        last_rel = rr[-1][0]
        n_after = sum(1 for a, _ in rr if a >= lr) - 1
        print("  口径核对: 闩行->末行 = %.3f s（按时间戳）；闩后行数=%d ×0.1s 名义=%.2f s" % (
            last_rel - lr, n_after, n_after * 0.1))
    # hwnd/singleton 首归零
    for k in ("hwnd", "singleton"):
        z = [a for a, row in rr if sc(row.get(k)) == 0]
        if z:
            print("  %s 首归零 rel=%.3f s（末非零读数=%s）" % (
                k, z[0], sc(next(row.get(k) for a, row in rr if a < z[0]))))
    # latch 前后 ±1.5 s 全行明细（仅列变化行）
    if latch:
        lr = latch[0][0]
        print("  -- latch 前 1.5 s（变化行）--")
        prev = None
        for a, row in rr:
            if lr - 1.5 <= a < lr:
                cur = tuple(str(sc(row.get(k))) for k in KEYS) + (str(row.get("wait")),)
                if cur != prev:
                    print("    +%.3f %s wait=%s" % (a, " ".join("%s=%s" % (k, sc(row.get(k))) for k in KEYS), row.get("wait")))
                prev = cur
        li = next(i for i, (a, _) in enumerate(rr) if a >= lr)
        print("  -- latch 行及后 5 行（全值）--")
        for a, row in rr[li:li + 6]:
            print("    +%.3f %s wait=%s" % (a, " ".join("%s=%s" % (k, sc(row.get(k))) for k in KEYS), row.get("wait")))
        print("  -- 末 3 行 --")
        for a, row in rr[-3:]:
            print("    +%.3f %s wait=%s code=%s cok=%s" % (a, " ".join("%s=%s" % (k, sc(row.get(k))) for k in KEYS),
                                                           row.get("wait"), row.get("code"), row.get("code_read_ok")))
        # 闩后每 10 s 抽样
        print("  -- 闩后每 10 s 抽样 --")
        for a, row in rr[li:]:
            if a >= lr and (round(a - lr) % 10 == 0):
                print("    latch%+7.2f %s wait=%s" % (a - lr, " ".join("%s=%s" % (k, sc(row.get(k))) for k in KEYS), row.get("wait")))
    # hold_tl 概览
    hold = j.get("hold_tl", [])
    if hold:
        print("  hold_tl(%d): exitstate=%s frame=%s tick=%s ws_kb=%s" % (
            len(hold), [sc(h.get("exitstate")) for h in hold], [sc(h.get("frame")) for h in hold],
            [sc(h.get("tick")) for h in hold], [h.get("ws_kb") for h in hold]))
        print("  hold hook6=%s visible=%s" % (
            sorted(set(str(h.get("hook6")) for h in hold)),
            [len(h.get("visible_windows", [])) for h in hold]))
    return r


def d09b_fact(tag):
    """旧 MAIN 两趟（旧 timeline 格式，字段可能不同）。"""
    rel = TRIPS[tag]
    j, r = load(rel)
    print("=" * 110)
    print("### [%s] %s  keys=%s" % (tag, rel, sorted(j.keys())))
    for k in ("closed_at_s", "exited", "exit_kind", "exit_after_close_s", "final_exitcode",
              "close_rows_n", "window_at_s"):
        if k in r:
            print("  rec.%s = %s" % (k, r[k]))
    rows = j.get("close_rows", [])
    t_close = r["close_delivery"]["t"] if "close_delivery" in r else None
    if rows and t_close:
        rr = rels(rows, t_close)
        for k in KEYS + ("wait",):
            tr = transitions(rr, k)
            print("  %-10s 变迁 %d 处: %s" % (k, len(tr), tr[:10]))
        prev = None
        shown = 0
        print("  变化行（前 25）:")
        for a, row in rr:
            cur = tuple(str(sc(row.get(k))) for k in KEYS) + (str(row.get("wait")),)
            if cur != prev:
                print("    +%.3f %s wait=%s code=%s" % (a, " ".join("%s=%s" % (k, sc(row.get(k))) for k in KEYS),
                                                        row.get("wait"), row.get("code")))
                shown += 1
                if shown >= 25:
                    print("    ...截断")
                    break
            prev = cur
    else:
        # 其他键的兜底展示
        for k, v in j.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                print("  %s: %d 行, 首行=%s" % (k, len(v), json.dumps(v[0], ensure_ascii=False)[:220]))
                print("       末行=%s" % json.dumps(v[-1], ensure_ascii=False)[:220])
            else:
                print("  %s: %s" % (k, str(v)[:160]))


if __name__ == "__main__":
    for tag in ("HANG", "NAT1", "NAT2", "P3BTL", "P3M"):
        fact(tag)
    for tag in ("D09BA", "D09BB"):
        try:
            d09b_fact(tag)
        except Exception as e:
            print("### [%s] 读取失败: %r" % (tag, e))
