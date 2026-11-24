# -*- coding: utf-8 -*-
r"""_n13_new_fp_probe.py — 第四步(b)：N13 会不会引入新的误报族？自己举反例试

这里的「新误报族」= 真断言被 A 检索标记 / B 标题结构洗成放过。
判据：每行给期望（应抓住=D / 应放过=A/B/C），实跑 r13_assertions 比对。
"""

import importlib.util
import pathlib

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
N13 = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"


def _load(p, n):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


n13 = _load(N13, "_n13_fp")
g7 = _load(G7, "_g7_fp")
T = list(n13.DEFAULT_TOKENS)


def judge(t):
    p, d = n13.r13_assertions(t, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    return (len(p) > 0), p, d


# 反例族：把 A/B 的表面标记粘到真断言上
CASES = [
    # id, 文本, 期望(D=应抓住 / X=应放过), 说明
    ("F01", "### 2.2 已入账 grep 结果：本笔已于 §605 入账", "D",
     "B 标题 + A 检索标记，但尾部带真断言"),
    ("F02", "## 已入账，可应用母本", "D",
     "标题行内直接写完成断言 + 可应用"),
    ("F03", "grep 结果：已生效，可应用母本", "D",
     "A 检索标记 + 可应用型真断言"),
    ("F04", "| 笔 | 状态 | 已入账? |\n|:--|:--|:--|\n| 1 | 本笔已入账 | 是 |", "D",
     "表头合法，但数据行内真断言"),
    ("F05", "有没有已入账的？有，本笔已于 §605 入账", "D",
     "A 问句伪装 + 肯定回答"),
    ("F06", "已入账核查实跑命令：确认本笔已入账", "D",
     "A 核查标签 + 真断言"),
    ("F07", "§2 已入账 grep / §3 本笔已生效，可应用母本", "D",
     "B 目录枚举 + 真断言"),
    ("F08", "不宣告 X 已生效，但 Y 已入账", "D",
     "同句混用（R10 CLAUSE_BREAK 不含逗号的裂缝）"),
    ("F09", "本笔已入账 0 命中不得写成未入账", "D",
     "A 结果标记「0 命中」劫持真断言"),
    ("F10", "### 2.2 待入账清点 + 已入账 grep 结果", "X",
     "真件 B/A 小节标题（对照：应放过）"),
    ("F11", "一、一页纸总览  1(a) 笔数=5 / 1(c) 已入账 grep=0 / 依赖速览", "X",
     "真件 A 总览（对照：应放过）"),
    ("F12", "| 笔 | 暂编 | 标题 | 已入账? |\n|:--:|:--:|:--|:--|", "X",
     "真件 B 表头（对照：应放过）"),
    ("F13", "- **附两条引用限定**（…本节登记不宣告 N-4 正式绑定已生效）。", "X",
     "真件 C 否定式（对照：应放过）"),
]


def main():
    print("=" * 78)
    print("N13 新误报族反例探针（A/B 豁免会不会洗掉真断言）")
    print("=" * 78)
    bad = 0
    for cid, t, expect, note in CASES:
        failed, probs, det = judge(t)
        got = "D" if failed else "X"
        ok = (got == expect)
        if not ok:
            bad += 1
        print(("PASS" if ok else "FAIL"), cid, "expect=%s got=%s" % (expect, got), "|", note)
        print("      ", [(d["kind"], d["rule"][:52]) for d in det])
        if probs:
            print("       problems:", probs)
    print()
    print("反例探针：%d/%d 符合期望；不符 %d" % (len(CASES) - bad, len(CASES), bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
