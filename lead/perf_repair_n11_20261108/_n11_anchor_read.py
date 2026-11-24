# -*- coding: utf-8 -*-
"""N-11 分流：上游锚点切片实读（只读打印，供分流卡逐条引用）。
零真机；零采样代码；不改任何既有件。行文超 TRUNC 截断并如实标注 len。"""
import os
import re

BASE = r"D:\Project\ra2-campaign-forge"
TRUNC = 400


def show(rel, lo, hi=None):
    p = os.path.join(BASE, rel.replace("/", os.sep))
    hi = hi or lo
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    print("===== %s : %d-%d =====" % (rel, lo, min(hi, len(lines))))
    for i in range(lo, min(hi, len(lines)) + 1):
        t = lines[i - 1]
        mark = " …[截断]" if len(t) > TRUNC else ""
        print("%d: %s%s (len=%d)" % (i, t[:TRUNC], mark, len(t)))


def grep_104():
    print("===== [104 检索] 字面「104 件/104件」 + 独立数字 104 =====")
    files = [
        "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
        "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
        "lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md",
        "lead/re_line_20261105/D24_RULING/RULING_D24.md",
        "lead/PENDING_DECISIONS.md",
        "lead/GOAL_THREE_TARGETS_20261018.md",
    ]
    pat_num = re.compile(r"(?<![0-9A-Za-z_])104(?![0-9])")
    for rel in files:
        p = os.path.join(BASE, rel.replace("/", os.sep))
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        lit_hits, num_hits = [], []
        for i, t in enumerate(lines, 1):
            if ("104 件" in t) or ("104件" in t):
                lit_hits.append(i)
            if pat_num.search(t):
                num_hits.append(i)
        print("-- %s" % rel)
        print("   字面「104 件」命中行: %s" % (lit_hits if lit_hits else "无"))
        print("   独立数字 104 命中行数 = %d" % len(num_hits))
        for i in num_hits[:15]:
            t = lines[i - 1]
            print("   %d: %s%s" % (i, t[:120], " …[截断]" if len(t) > 120 else ""))
        if len(num_hits) > 15:
            print("   …（仅示前 15 行，其余行号略）")


def main():
    PLAN = "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md"
    LEDGER = "lead/GOAL_THREE_TARGETS_20261018.md"
    PENDING = "lead/PENDING_DECISIONS.md"
    D24 = "lead/re_line_20261105/D24_RULING/RULING_D24.md"

    show(PLAN, 77, 84)          # N-8 任务定义（本会话未读段）
    show(LEDGER, 53)            # N-11 依据之一
    show(LEDGER, 5996)          # N-11 依据 §560 标题
    show(LEDGER, 6017, 6032)    # §560 数字锚 + 6030/6032 未采自认
    show(LEDGER, 6033, 6075)    # §560 四成本中心 + 6065/6066/6069（N-8 引用行本人直读）
    show(LEDGER, 5828)          # 1832 对象（F8 代价参照）
    show(LEDGER, 6642, 6646)    # D-19 口径 A 语义 + 不得换算禁令
    show(LEDGER, 7095, 7099)    # DLL 节流 1/8
    show(LEDGER, 8408, 8414)    # §589 收紧
    show(LEDGER, 9740, 9757)    # §604 尾部：9741/9745/9751/9756 等
    show(PENDING, 15, 75)       # D-13(:23)/D-14(:64) 上下文
    show(D24, 55, 90)           # :59/:63/:70/:71/:75/:78/:87
    grep_104()


if __name__ == "__main__":
    main()
