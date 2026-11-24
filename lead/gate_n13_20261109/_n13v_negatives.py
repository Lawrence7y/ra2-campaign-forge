# -*- coding: utf-8 -*-
r"""_n13v_negatives.py — 第四步复核：撰写人样本集之外的新负样本（真断言，D 类）

构造原则：
  - 每条都是「主语=被登记的那一笔/件/台账 + 完成词谓语」或编排方点名的真断言形；
  - 逐字不在 _n13_regression.py 的 18 条 NEGATIVES 与 _n13_new_fp_probe.py 的 13 条 CASES 内；
  - 不依赖撰写人守卫词（可应用/可改/照此/无需…）来触发 D；
  - 黑盒调用 r13_assertions，不读撰写人正则。
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_n13_20261109"
N13 = WD / "_n13_predicates.py"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"


def _load(p, n):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


n13 = _load(N13, "_n13v_neg_n13")
g7 = _load(G7, "_n13v_neg_g7")
reg = _load(WD / "_n13_regression.py", "_n13v_neg_reg")
probe = _load(WD / "_n13_new_fp_probe.py", "_n13v_neg_probe")
T = list(n13.DEFAULT_TOKENS)
EXISTING = {t for _, t, _, _ in reg.NEGATIVES} | {t for _, t, _, _ in probe.CASES}

# 5 条正式新负样本（编排方要求的 5 条）
NEW5 = [
    ("V1", "未验：本笔已入账",
     "前置「未验」标签污染 R10 回看窗；主体「本笔已入账」是编排方点名的 D 形"),
    ("V2", "清点结果：本笔已入账",
     "A 检索动作「清点」+ 结果标签 + 主语完成断言，无「可应用」类守卫词"),
    ("V3", "核查结论：该笔已追加至台账尾部",
     "A 核查标签 + 该笔 + 已追加，无动作词"),
    ("V4", "§2 已入账 grep 结果 / §3 结论：本笔已入账",
     "B 目录 + A grep 标记 + 尾部主语断言"),
    ("V5", "### 2.2 待入账清点 + 已入账 grep 结果；本笔已入账",
     "B 标题 + 分号后另起主语断言"),
]

# 补充侦察样本（不放进正式 5 条，单独列差异）
EXTRA = [
    ("X1", "未核：本件已生效", "前置「未」+ 主语断言"),
    ("X2", "grep 结果：已入账", "A 结果标签 + 裸完成词（语境有歧义，仅登记）"),
    ("X3", "核对：本笔已生效", "A 核对标签 + 主语断言"),
    ("X4", "检索已入账条目：本笔已入账", "A 检索 + 主语断言"),
    ("X5", "本节不代签；本笔已入账", "前置否定分句 + 分号 + 主语断言"),
    ("X6", "本笔已入账，但尚待复核", "主语断言 + 转折后无完成词"),
    ("X7", "已入账核查实跑命令：该笔已追加至台账尾部", "A 实跑命令标签 + 该笔已追加"),
    ("X8", "不清点：本笔已入账", "前置「不」+ 主语断言"),
    ("X9", "| 笔 | 状态 |\n|:--|:--|\n| 1 | 本笔已入账 |", "表格数据行主语断言（无可应用）"),
    ("X10", "本笔已入账（未验项另计）", "主语断言 + 后置括注含「未」"),
]


def judge(t):
    p, det = n13.r13_assertions(t, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    return len(p) > 0, p, det


def main():
    print("=" * 78)
    print("第四步复核：撰写人样本集之外的 5 条新负样本（真断言）")
    print("=" * 78)
    for cid, t, note in NEW5:
        print("  %-3s 已在撰写人样本集内 = %s | %s" % (cid, t in EXISTING, note))
    print()
    misses5 = []
    for cid, t, note in NEW5:
        failed, probs, det = judge(t)
        status = "抓住" if failed else "★漏网"
        if not failed:
            misses5.append((cid, t, note, det))
        print("%-4s %-4s | %s" % (cid, status, repr(t)))
        print("     ", [(d["kind"], d["rule"][:58]) for d in det])
    print()
    print("正式 5 条：抓住 %d / 漏网 %d" % (len(NEW5) - len(misses5), len(misses5)))
    print("漏网 =", [m[0] for m in misses5])

    print()
    print("=" * 78)
    print("补充侦察样本（同族写法，看漏网是否成族）")
    print("=" * 78)
    missesX = []
    for cid, t, note in EXTRA:
        failed, probs, det = judge(t)
        status = "抓住" if failed else "★漏网"
        if not failed:
            missesX.append((cid, t, note, det))
        print("%-4s %-4s | %-42s | %s" % (cid, status, note, repr(t)))
        if not failed:
            print("      漏网明细:", [(d["kind"], d["rule"][:58]) for d in det])
    print()
    print("补充侦察漏网 =", [m[0] for m in missesX], "(%d/%d)" % (len(missesX), len(EXTRA)))
    print("全部漏网 =", [m[0] for m in misses5 + missesX])
    print("N13V_NEW_NEG_ALL_CAUGHT =", (len(misses5) + len(missesX)) == 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
