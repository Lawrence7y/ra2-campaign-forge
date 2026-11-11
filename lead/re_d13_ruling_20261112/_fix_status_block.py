#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 D-13 历史状态块（D-31 Q4 同步块）逐字迁移进「已裁决记录」的 D-13 条目内。

原因：首轮脚本只迁移了「D-13 原始正文」块，状态块被替换成指针，
      自检 "D-13 状态块原文零丢失" FAIL。本脚本补迁，保证原文零丢失。
"""
import hashlib
import os
import sys

PD = r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md"
BAK = r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\PENDING_DECISIONS_before.md"

STATUS_BLOCK = [
    "- **D-13 已同步状态（2026-11-08，依据 D-31 裁决 Q4）：维持 PAUSE，实施保持 BLOCKED。**\n",
    "  **裁决要点**：不批准以「只编写候选件+离线单测」放行采样代码；仅保留**无采样实现的规格评审**与纯模型/合成验证资格。\n",
    "  实际代价、帧数、重复性、阈值仍不足；采样候选须**用户明确改变零采样代码禁令并指定有效写域**；真机/活进程须**当轮明示**，均不能由裁决代授。\n",
    "  **另登记待裁**：N10-C04 / 上游 Q3「静态检索任务的顺序与新写域」**仍待裁**——不能以「更新缺口状态」冒充已裁任务顺序或写域。\n",
    "  裁决书：`lead/direction_ruling_20261108/RULING_DIRECTION.md`（16,514 B / `0ebd68dd11a2a54a`）。\n",
    "  **★ 本条状态已同步，但条目本身仍需用户在 D-13 三选一（A/C/暂停）上明示后方可归档。**\n",
    "  证据：`lead/d13d14_cards_20261108/DECISION_QUESTIONS.md` + `lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md`（规格补正件）。\n",
    "\n",
]

ANCHOR = "  ### D-13 原始正文（保留供追溯，不改）"


def main():
    c = open(PD, encoding="utf-8").read().splitlines(True)
    idx = None
    for i, l in enumerate(c):
        if l.startswith(ANCHOR):
            idx = i
            break
    if idx is None:
        print("!! 锚点未找到")
        return 2
    print("anchor at L%d" % (idx + 1))

    insert = [
        "  **历史状态块（逐字保留，供追溯；自待裁段迁移，未改一字）**：\n",
        "\n",
    ] + ["  " + s if s.strip() else s for s in STATUS_BLOCK]

    out = c[:idx] + insert + c[idx:]
    txt = "".join(out)
    open(PD, "wb").write(txt.encode("utf-8"))

    raw = open(PD, "rb").read()
    f = raw.decode("utf-8")
    print("after bytes = %d" % len(raw))
    print("after sha   = %s" % hashlib.sha256(raw).hexdigest())

    checks = [
        ("状态块首行在案", "- **D-13 已同步状态（2026-11-08，依据 D-31 裁决 Q4）：维持 PAUSE，实施保持 BLOCKED。**"),
        ("裁决要点行在案", "不批准以「只编写候选件+离线单测」放行采样代码"),
        ("须当轮明示在案", "真机/活进程须**当轮明示**"),
        ("N10-C04 在案", "N10-C04"),
        ("D-13 已裁决在案", "D-13 已裁决（2026-11-12）"),
        ("D-14 在案", "D-14 已同步状态"),
        ("原始正文锚在案", "D-13 原始正文（保留供追溯，不改）"),
        ("真机未授权声明在案", "真机发射 / 活进程采集**仍未授权"),
    ]
    ok = True
    print()
    for t, s in checks:
        r = s in f
        ok = ok and r
        print("[%s] %s" % ("PASS" if r else "FAIL", t))

    # 与备份比对：状态块 8 行是否逐字都在
    bak = open(BAK, encoding="utf-8").read()
    lost = []
    for s in STATUS_BLOCK:
        t = s.strip()
        if t and t not in f:
            lost.append(t[:50])
    print("[%s] 状态块逐行零丢失 (lost=%d)" % ("PASS" if not lost else "FAIL", len(lost)))
    for x in lost:
        print("   LOST:", x)
    ok = ok and not lost

    fffd = f.count("\ufffd")
    print("[%s] UTF-8 无替换字符 (fffd=%d)" % ("PASS" if fffd == 0 else "FAIL", fffd))
    ok = ok and fffd == 0
    print("lines = %d" % len(f.splitlines()))
    print("\n==== RESULT: %s ====" % ("ALL PASS" if ok else "HAS FAILURE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
