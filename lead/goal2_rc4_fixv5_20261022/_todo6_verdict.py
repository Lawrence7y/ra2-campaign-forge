#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""待办 6 判据改造：把 A/B 探针的 AB_*.json 汇成「单例态 × 退出方式」二维表。

依据 §374 §二：WM_CLOSE 本身既不创建也不销毁单例（走默认分支），
所以「三种退出方式各跑 1 趟看是否命中」这个原设计会给出同一个答案。
命中与否实际取决于**主窗此前是否收到过 WM_CREATE 且分配成功**，
也就是关窗前的 [0x887368] 是不是非 0。

本脚本只读 AB_*.json，不启动任何进程。无数据时输出 NO_DATA 并以 exit 2 退出
（fail-closed：不许把"没跑过"读成"没命中"）。

判定三档（逐趟）：
  SINGLETON_DEAD   : singleton_before_close == 0   ⇒ 单例从未创建（或创建失败写 0）
  SINGLETON_ALIVE  : singleton_before_close != 0   ⇒ 单例已创建
  UNVERIFIABLE     : 字段缺失 / 读失败 / 趟次 abort ⇒ 不许猜

二维表按 (arm, 单例态) 聚合，列给出 rc4_hit 计数与 clean_exit 计数。
"""
import json
import sys
from pathlib import Path

CARD = Path(__file__).resolve().parent
ARM_LABEL = {
    "A": "A（原版直启，无守卫）",
    "B0": "B0（副本 + 守卫 dry-run）",
    "B1": "B1（副本 + 守卫生效）",
    "B": "B（副本 + 守卫）",
}


def load_trips():
    """返回 [(文件名, arm, trip_dict)]；坏文件单列不静默跳过。"""
    out, bad = [], []
    for p in sorted(CARD.glob("AB_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                      # noqa: BLE001
            bad.append((p.name, repr(e)))
            continue
        arm = d.get("arm") or p.stem.split("_")[1]
        for i, r in enumerate(d.get("trips") or [], 1):
            out.append((p.name, arm, i, r))
    return out, bad


def singleton_state(rec):
    """三档判定；字段缺失一律 UNVERIFIABLE，不拿 clean_exit 之类代偿。"""
    if rec.get("abort"):
        return "UNVERIFIABLE", "abort=%s" % rec["abort"]
    if "singleton_before_close" not in rec:
        return "UNVERIFIABLE", "字段缺失 singleton_before_close"
    v = rec.get("singleton_before_close")
    if v is None:
        return "UNVERIFIABLE", "读取失败（OpenProcess/ReadProcessMemory 未成功）"
    if not isinstance(v, int):
        return "UNVERIFIABLE", "非整数 %r" % (v,)
    return ("SINGLETON_DEAD" if v == 0 else "SINGLETON_ALIVE"), "0x%08X" % v


def main():
    trips, bad = load_trips()
    if not trips:
        print("NO_DATA: %s 下没有可用的 AB_*.json" % CARD)
        print("  ⇒ 待办 6 判据未取得任何数据，不得判 PASS。")
        for name, err in bad:
            print("  坏文件 %s: %s" % (name, err))
        return 2

    rows = []
    for fname, arm, idx, rec in trips:
        st, why = singleton_state(rec)
        hit = rec.get("rc4_hit")
        rows.append({
            "file": fname, "arm": arm, "trip": idx, "state": st, "why": why,
            "hit": bool(hit),
            "hit_eip": (hit or {}).get("address"),
            "hit_access": ((hit or {}).get("info") or [None, None])[1]
            if hit else None,
            "clean_exit": rec.get("clean_exit"),
            "closed_at_s": rec.get("closed_at_s"),
            "guard_hits": (rec.get("guard") or {}).get("hits_total"),
        })

    # ---- 逐趟明细 ----
    print("=" * 96)
    print("待办 6 逐趟明细（单例态在 WM_CLOSE 之前读取）")
    print("=" * 96)
    print("%-34s %-4s %-3s %-16s %-12s %-6s %-6s %-8s"
          % ("文件", "arm", "趟", "单例态", "值", "命中", "净退", "守卫"))
    for r in rows:
        print("%-34s %-4s %-3d %-16s %-12s %-6s %-6s %-8s"
              % (r["file"][:34], r["arm"], r["trip"], r["state"], r["why"],
                 "Y" if r["hit"] else "n",
                 "-" if r["clean_exit"] is None else ("Y" if r["clean_exit"] else "n"),
                 "-" if r["guard_hits"] is None else r["guard_hits"]))

    # ---- 二维表：单例态 × arm ----
    print()
    print("=" * 96)
    print("二维表：单例态 × 退出方式（arm）")
    print("=" * 96)
    states = ["SINGLETON_ALIVE", "SINGLETON_DEAD", "UNVERIFIABLE"]
    arms = sorted({r["arm"] for r in rows})
    print("%-18s %s" % ("单例态 \\ arm", "".join("%-26s" % a for a in arms)))
    print("%-18s %s" % ("", "".join("%-26s" % "趟/命中/净退" for _ in arms)))
    for st in states:
        cells = []
        for a in arms:
            sub = [r for r in rows if r["arm"] == a and r["state"] == st]
            if not sub:
                cells.append("%-26s" % "-")
                continue
            nh = sum(1 for r in sub if r["hit"])
            nc = sum(1 for r in sub if r["clean_exit"])
            cells.append("%-26s" % ("%d / %d / %d" % (len(sub), nh, nc)))
        if any(c.strip() != "-" for c in cells):
            print("%-18s %s" % (st, "".join(cells)))

    # ---- 判据 ----
    print()
    print("=" * 96)
    print("判据（§374 §二）")
    print("=" * 96)
    alive = [r for r in rows if r["state"] == "SINGLETON_ALIVE"]
    dead = [r for r in rows if r["state"] == "SINGLETON_DEAD"]
    unv = [r for r in rows if r["state"] == "UNVERIFIABLE"]

    verdict = []
    if unv:
        verdict.append("⚠ %d/%d 趟 UNVERIFIABLE（%s）——这些趟不参与结论"
                       % (len(unv), len(rows),
                          ", ".join(sorted({r["why"] for r in unv}))[:120]))
    if alive:
        n = sum(1 for r in alive if r["hit"])
        verdict.append("单例存活趟：%d 趟，命中 RC-4 %d 趟（%.0f%%）"
                       % (len(alive), n, 100.0 * n / len(alive)))
    if dead:
        n = sum(1 for r in dead if r["hit"])
        verdict.append("单例为零趟：%d 趟，命中 RC-4 %d 趟（%.0f%%）"
                       % (len(dead), n, 100.0 * n / len(dead)))

    if alive and dead:
        ra = sum(1 for r in alive if r["hit"]) / len(alive)
        rd = sum(1 for r in dead if r["hit"]) / len(dead)
        if ra > rd:
            verdict.append("⇒ 命中率在「单例存活」侧更高：与 RC-4 因果链"
                           "（ecx=[0x887368]=0 才崩）**方向相反**，须复核链上取的是哪次读")
        elif rd > ra:
            verdict.append("⇒ 命中率在「单例为零」侧更高：**支持** RC-4 因果链"
                           "（ecx=[0x887368]=0 ⇒ 崩溃）")
        else:
            verdict.append("⇒ 两侧命中率相同：单例态不是区分变量，"
                           "须另找触发者（或样本量不足）")
    elif alive or dead:
        verdict.append("⇒ 只有单侧样本，无法做对照；须补另一侧")

    # 铁律：except.txt 零新增不得单独作为未崩溃判据 —— 本表不引用它
    for v in verdict:
        print(" ", v)

    if not alive and not dead:
        print("  NO_VERDICT: 无任何可判定的单例态样本。")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
