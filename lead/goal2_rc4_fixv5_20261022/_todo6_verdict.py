#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""待办 6 判据（v2）：用**崩溃瞬间**的单例读数归因，不用关窗前的读数。

★★ v1 的方向性错误（§379 推翻 §374 §二 后暴露）：
   v1 依据「WM_CLOSE 本身既不创建也不销毁单例」来设计判据，把
   `singleton_before_close` 当作"单例是否存活"的判据。
   §379 已证：WM_CLOSE 走默认分支 = DefWindowProcA = DestroyWindow
   = 同步发 WM_DESTROY = 0x777803 **清零单例**。
   ⇒ 关窗前读到的非 0 值，在崩溃瞬间**必然**已经是 0。
   ⇒ 用 before_close 做归因，等于用"关窗前的状态"去解释"关窗后的崩溃"，
     两种退出方式都会被读成同一个答案 —— v1 想避免的错误，它自己犯了。

v2 的正确判据（两个时点分开，各答各的问题）：
  ① `singleton_before_close` 只回答「单例**是否创建过**」
     —— 用于判定 WM_CREATE 是否到达（待办 7 的结论）。
  ② `singleton_at_hit`（崩溃瞬间读数）才是**归因**依据
     —— 崩溃链要求 ecx = [0x887368] = 0；只有崩溃瞬间的读数能验证这一点。

判定三档（逐趟，基于 at_hit）：
  HIT_SINGLETON_ZERO  : singleton_at_hit == 0   ⇒ 与 RC-4 因果链一致
  HIT_SINGLETON_NONZERO: singleton_at_hit != 0  ⇒ **与因果链矛盾**，须复核
  UNVERIFIABLE        : 字段缺失 / 读失败 / 趟次 abort / 未命中

本脚本只读 AB_*.json，不启动任何进程。无数据时 exit 2（fail-closed）。
"""
import json
import sys
from pathlib import Path

CARD = Path(__file__).resolve().parent


def load_trips():
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


def created_state(rec):
    """① 单例是否**创建过** —— 用关窗前读数（这是它唯一能回答的问题）。"""
    if "singleton_before_close" not in rec:
        return "UNVERIFIABLE", "字段缺失"
    v = rec.get("singleton_before_close")
    if v is None:
        return "UNVERIFIABLE", "读取失败"
    return ("CREATED" if v != 0 else "NEVER_CREATED"), "0x%08X" % v


def hit_state(rec):
    """② 崩溃瞬间的单例读数 —— 这是归因依据。"""
    hit = rec.get("rc4_hit")
    if not hit:
        return "NO_HIT", "-"
    if "singleton_at_hit" not in hit:
        return "UNVERIFIABLE", "命中但缺 singleton_at_hit"
    v = hit.get("singleton_at_hit")
    if v is None:
        return "UNVERIFIABLE", "崩溃瞬间读取失败"
    return ("HIT_SINGLETON_ZERO" if v == 0 else "HIT_SINGLETON_NONZERO"), \
        "0x%08X" % v


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
        cs, cw = created_state(rec)
        hs, hw = hit_state(rec)
        rows.append({"file": fname, "arm": arm, "trip": idx,
                     "created": cs, "created_why": cw,
                     "hit_state": hs, "hit_why": hw,
                     "abort": rec.get("abort")})

    print("=" * 104)
    print("待办 6 逐趟明细（v2：创建态与崩溃瞬间态分开记）")
    print("=" * 104)
    print("%-30s %-4s %-3s %-14s %-12s %-22s %-12s"
          % ("文件", "arm", "趟", "创建态(关窗前)", "值", "崩溃瞬间态", "值"))
    for r in rows:
        print("%-30s %-4s %-3d %-14s %-12s %-22s %-12s"
              % (r["file"][:30], r["arm"], r["trip"], r["created"],
                 r["created_why"], r["hit_state"], r["hit_why"]))

    # ---- 表 A：创建态（回答「WM_CREATE 到没到」）----
    print()
    print("=" * 104)
    print("表 A：单例是否创建过（回答待办 7：WM_CREATE 到没到）")
    print("=" * 104)
    arms = sorted({r["arm"] for r in rows})
    print("%-16s %s" % ("创建态 \\ arm", "".join("%-20s" % a for a in arms)))
    for st in ("CREATED", "NEVER_CREATED", "UNVERIFIABLE"):
        cells = []
        for a in arms:
            n = sum(1 for r in rows if r["arm"] == a and r["created"] == st)
            cells.append("%-20s" % (str(n) if n else "-"))
        if any(c.strip() != "-" for c in cells):
            print("%-16s %s" % (st, "".join(cells)))

    # ---- 表 B：崩溃瞬间态（归因）----
    print()
    print("=" * 104)
    print("表 B：崩溃瞬间 [0x887368] 的值（★ 这才是 RC-4 归因依据）")
    print("=" * 104)
    print("%-24s %s" % ("瞬间态 \\ arm", "".join("%-20s" % a for a in arms)))
    for st in ("HIT_SINGLETON_ZERO", "HIT_SINGLETON_NONZERO",
               "NO_HIT", "UNVERIFIABLE"):
        cells = []
        for a in arms:
            n = sum(1 for r in rows if r["arm"] == a and r["hit_state"] == st)
            cells.append("%-20s" % (str(n) if n else "-"))
        if any(c.strip() != "-" for c in cells):
            print("%-24s %s" % (st, "".join(cells)))

    # ---- 判据 ----
    print()
    print("=" * 104)
    print("判据")
    print("=" * 104)
    zero = [r for r in rows if r["hit_state"] == "HIT_SINGLETON_ZERO"]
    nonzero = [r for r in rows if r["hit_state"] == "HIT_SINGLETON_NONZERO"]
    unv = [r for r in rows if r["hit_state"] == "UNVERIFIABLE"]
    nohit = [r for r in rows if r["hit_state"] == "NO_HIT"]

    if zero:
        print("  ✓ %d 趟命中且崩溃瞬间单例为 0 ⇒ 与 RC-4 因果链（ecx=0）一致"
              % len(zero))
    if nonzero:
        print("  ✗ %d 趟命中但崩溃瞬间单例**非 0** ⇒ 与因果链矛盾！"
              % len(nonzero))
        print("     ⇒ 链上 ecx 的 0 不来自 [0x887368]，须重新定位取 0 的来源")
    if unv:
        print("  ⚠ %d 趟 UNVERIFIABLE：%s"
              % (len(unv), ", ".join(sorted({r["hit_why"] for r in unv}))[:110]))
    if nohit:
        print("  · %d 趟未命中（不参与归因）" % len(nohit))

    # 关键警示：不得用创建态做归因
    created_nz = [r for r in rows if r["created"] == "CREATED" and r["hit_state"] != "NO_HIT"]
    if created_nz:
        print()
        print("  ★ 注意：%d 趟「关窗前单例非 0」且命中。" % len(created_nz))
        print("    §379 已证 WM_CLOSE 经 DefWindowProcA 必然清零单例，")
        print("    所以「关窗前非 0」与「崩溃瞬间为 0」**并不矛盾**。")
        print("    归因只能用崩溃瞬间读数（表 B），不能用表 A。")

    if not zero and not nonzero:
        print("  NO_VERDICT: 无任何可归因的命中趟。")
        return 2
    if nonzero and not zero:
        return 4          # 与因果链矛盾，单独退出码
    return 0


if __name__ == "__main__":
    sys.exit(main())
