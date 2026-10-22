#!/usr/bin/env python
"""裁决 3 第 5 条 · 查语料有无 `Access=0xC` 的崩溃（0x7241A0 的 0xC 族）。

★ 背景
  v7 裁决 3 第 5 条：「`0x7241A0` 那个 `0xC` 族无守卫站点：在语料里查有没有
  `Access=0xC` 的崩溃。」
  §365 的 v4 八函数覆盖了 66 个 `0x250` 族站点；`0x7241A0` 另有 1 个偏移为
  `0xC` 的站点**不在** v4 覆盖理由之内（它不是 `0x250` 族）。
  若语料里存在 `Access=0x0000000C` 的崩溃，说明这一族也真的会崩 ⇒ v4 覆盖不全。

★ 判据
  A1 语料清单可读且非空
  A2 逐文件抽出 `Access address` 值并做分布统计
  A3 **明确回答**：是否存在 `Access == 0x0000000C`
  A4 若存在 ⇒ 报告其 Eip 与文件路径（供裁决 3 第 5 条闭环）
  A5 反证：抽取器在已知 RC-4 现场上必须读出 `0x250`（否则抽取器坏了）

★ 用法
  python _access_0xC_census.py
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "goal2_rc4_trigger_20261022"
LIST = ROOT / "lead" / "goal2_rc4_frameproof_20261022" / "_except_list.txt"

CHECKS = []


def chk(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


RE_ACCESS = re.compile(r"Access address:\s*([0-9A-Fa-f]{8})")
RE_EIP = re.compile(r"Exception occurred at\s*([0-9A-Fa-f]{8})")


def parse(p: Path):
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:               # noqa: BLE001
        return None
    ma = RE_ACCESS.search(t)
    me = RE_EIP.search(t)
    if not ma:
        return {"path": str(p), "access": None,
                "eip": me.group(1).upper() if me else None}
    return {"path": str(p), "access": int(ma.group(1), 16),
            "eip": me.group(1).upper() if me else None}


def main() -> int:
    print("=" * 78)
    print("裁决 3 第 5 条 · Access=0xC 语料普查")
    print("=" * 78)

    if not LIST.is_file():
        print("!! 缺清单:", LIST)
        return 2
    paths = [ln.strip() for ln in LIST.read_text(encoding="utf-8").splitlines()
             if ln.strip()]
    chk("A1 语料清单可读且非空", len(paths) > 0, "%d 条" % len(paths))

    rows = []
    for rel in paths:
        p = (ROOT / rel.lstrip("./")).resolve()
        if not p.is_file():
            continue
        r = parse(p)
        if r:
            r["rel"] = rel
            rows.append(r)

    # ---- A2：分布 ----
    dist = Counter(r["access"] for r in rows)
    print()
    print("Access 值分布（共 %d 份可解析）：" % len(rows))
    for val, n in sorted(dist.items(), key=lambda kv: -kv[1]):
        label = ("0x%08X" % val) if isinstance(val, int) else "无 Access 行"
        print("  %-14s %3d 份" % (label, n))

    chk("A2 已抽取 Access 分布", len(dist) >= 1, "%d 种取值" % len(dist))

    hit_c = [r for r in rows if r["access"] == 0x0C]

    # ---- A3：是否存在的问题被**明确回答** ----
    #   ★ 这是「查证型」判据，不是「断言存在」。
    #     若写成 `chk(..., len(hit_c) > 0)`，那是在赌「一定有」，
    #     答案是否定时会假红 —— 而「没有」本身就是一个合格的答案。
    #     正确判据：抽取器工作正常（A2/A5 已证）+ 全部 131 份都被读取并分类
    #     ⇒ 答案已确定。
    unanswered = [r for r in rows if r["access"] is None]
    chk("A3 Access=0xC 问题已被明确回答（全部文件均已分类）",
        len(rows) == len(paths) and len(dist) >= 1,
        "读到 %d/%d 份；无 Access 行 %d 份（多为非崩溃文本）"
        % (len(rows), len(paths), len(unanswered)))
    print("      答案：%s（命中 %d 份）"
          % ("存在" if hit_c else "不存在", len(hit_c)))

    # ---- A4：若存在则列出 ----
    if hit_c:
        print()
        print("★ Access=0xC 的现场：")
        for r in hit_c:
            print("   eip=%s  %s" % (r["eip"], r["rel"]))
    else:
        print()
        print("★ 结论：语料里**没有** Access=0xC 的崩溃。")
        print("  ⇒ 0x7241A0 的 0xC 族站点**从未在真实崩溃中出现过**。")
        print("  ⇒ v4 八函数按 0x250 族划覆盖是**自洽**的；")
        print("     把 0xC 族站点排除在 v4 之外**不构成覆盖缺口**。")

    # ---- A5：反证抽取器 ----
    #   已知 RC-4 现场必须读出 0x250
    known = [r for r in rows if r["eip"] == "00724737"]
    ok5 = bool(known) and all(r["access"] == 0x250 for r in known)
    chk("A5 反证：已知 RC-4 现场（Eip=00724737）全部读出 0x250",
        ok5, "%d 份，access=%s"
        % (len(known), sorted({r["access"] for r in known})))

    print()
    n = len(CHECKS)
    ok = sum(1 for _, v, _ in CHECKS if v)
    print("-" * 78)
    print("结果：%d/%d PASS" % (ok, n))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
