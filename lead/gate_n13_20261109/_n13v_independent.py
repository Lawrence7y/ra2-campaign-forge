# -*- coding: utf-8 -*-
r"""_n13v_independent.py — 复核员独立实现（不看 _n13_predicates.py 源码/正则）

三件事：
  PART A 独立 A/B/C/D 判别器（本人自拟规则，仅依据任务描述的四类 + 真件 10 行原文）
  PART B 在撰写人 16 正 / 18 负样本集上与撰写人谓词对跑，逐条列差异
  PART C 构造 5 条撰写人样本集里没有的新负样本（真断言），黑盒测撰写人谓词

撰写人谓词只作为黑盒调用（r13_assertions），不读取其源码。
零真机、零采样；只做静态文本。
"""
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_n13_20261109"
N13 = WD / "_n13_predicates.py"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
REG = WD / "_n13_regression.py"

TOKENS = ("已入账", "已追加", "已生效")

# ---------------- 本人自拟规则（与撰写人实现无关） ----------------
# 子句界：我自选的字符集（特意包含逗号/冒号/顿号，用于隔离检索标记与断言）
SEP = "。！？；\n，,：:、"
# 主语词表（被登记的那一笔 / 承载完成动作的主体）
SUBJ = ("本笔", "本件", "该笔", "该件", "本节", "本回件", "本交付件", "本候选",
        "母本", "台账", "第", "此笔", "该条", "本条", "该草案")
# 肯定/可执行的后续动作词（出现即视为既成事实被应用）
ACTION = ("可应用", "可改", "照此", "无需", "放行", "具备", "即可", "按此", "据此", "可据此", "准许")
# 转折/并列后接肯定段
CONTRAST = ("但", "然而", "不过", "而且", "并且", "且", "同时", "另外", "反之")
# 检索/问询/结果标记
SEARCH = ("grep", "检索", "搜索", "查找", "清点", "核查", "核对", "实跑命令",
          "有没有", "是否", "结果", "命中", "=0", "0 逐字", "结果：", "确认")
# 否定标记（只在 token 之前回看，避免后置否定污染）
NEG = ("不宣告", "不得", "不", "未", "非", "无", "禁", "勿")
# 目录/结构枚举标记
TOC = ("§", "总览", "目录", "大纲", "结构", "五节", "五章", "章节", "1(", "一页纸")
# 拆分裂缝：主语 + 完成副词 + 可选定位 + 完成动词（本人另写，非撰写人正则）
SPLIT = re.compile(
    r"(?:本笔|本件|该笔|第\s*\d+\s*笔|本节|母本|台账|本交付件|本候选)"
    r"\s*(?:已|现|正式|业已)[^，。；！？\n]{0,24}?(?:入账|追加|生效)")
# 表格分隔行
TBL_SEP = re.compile(r"^\s*\|[\s:|\-]+\|\s*$")


def _clause(line, pos, end):
    """取 token 所在子句（我自己的边界定义）。"""
    left = max((line.rfind(c, 0, pos) for c in SEP), default=-1)
    rights = [p for p in (line.find(c, end) for c in SEP) if p != -1]
    right = min(rights) if rights else len(line)
    return line[left + 1:right], line[left + 1:pos]


def my_classify(text):
    """返回 (should_fail, details)。details: (line_no, token, kind, why)
    kind: A 检索 / B 标题表头目录 / C 否定 / D 真断言；只有 D 计 FAIL。"""
    lines = text.splitlines()
    details = []
    for li, line in enumerate(lines, 1):
        # 行级守卫 1：转折/并列之后的肯定段（含完成词或拆分形态）
        contrast_pos = False
        for c in CONTRAST:
            for m in re.finditer(re.escape(c), line):
                tail = line[m.end():]
                if (any(t in tail for t in TOKENS) or SPLIT.search(tail)) \
                        and not any(n in tail[:12] for n in ("不", "未", "非", "无")):
                    contrast_pos = True
        # 行级守卫 2：可执行动作词
        actionable = any(a in line for a in ACTION)
        # 行级守卫 3：表格数据行（首格数字/§N，且非分隔行）
        is_data_row = bool(re.match(r"^\s*\|\s*(?:\d+|§)", line)) and not TBL_SEP.match(line)
        # 行级守卫 4：拆分形态
        has_split = bool(SPLIT.search(line)) and not any(
            n in line[:SPLIT.search(line).start()] for n in ("不宣告", "不得写成"))

        for tok in TOKENS:
            for m in re.finditer(re.escape(tok), line):
                clause, pre = _clause(line, m.start(), m.end())
                neg_pre = any(n in pre for n in NEG)
                subj_pre = any(s in pre for s in SUBJ)
                if contrast_pos or actionable or has_split or is_data_row or subj_pre:
                    kind, why = "D", "行级守卫(转折/动作/拆分/数据行/主语前置)"
                elif neg_pre:
                    kind, why = "C", "token 前置否定语（交 R10）"
                else:
                    # A：子句内检索/问询/结果标记
                    if any(s in clause for s in SEARCH) or line.rstrip().endswith(("？", "?")) \
                            or "？" in clause or "?" in clause:
                        kind, why = "A", "检索动作/问句/检索结果"
                    # B1：Markdown 标题
                    elif re.match(r"^\s*#{1,6}\s", line):
                        kind, why = "B", "小节标题"
                    # B2：表头 = | 行 + 下一行分隔行 或 含问询列名
                    elif line.lstrip().startswith("|") and (
                            (li < len(lines) and TBL_SEP.match(lines[li]))
                            or "?" in line or "？" in line or "是否" in line):
                        kind, why = "B", "表格表头列名"
                    # B3：目录/结构枚举（§ 串 + 章节名，无句末标点）
                    elif any(t in line for t in TOC) and "/" in line and "。" not in line:
                        kind, why = "B", "目录/结构枚举"
                    else:
                        kind, why = "D", "无 A/B/C 语境，默认真断言"
                details.append((li, tok, kind, why))
        # 只有拆分形态、没有字面三词的行也要判 D
        if not any(tok in line for tok in TOKENS) and has_split:
            details.append((li, "(拆分)", "D", "词表拆分裂缝：主语+完成动词"))
    should_fail = any(k == "D" for _, _, k, _ in details)
    return should_fail, details


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    n13 = _load(N13, "_n13v_blackbox")
    g7 = _load(G7, "_g7_blackbox")
    reg = _load(REG, "_n13v_reg_samples")
    T = list(n13.DEFAULT_TOKENS)

    def theirs(text):
        probs = n13.r13_assertions(text, T, r10_scan=g7.r10_scan,
                                   r12_scan=g7.r12_scan)[0]
        return len(probs) > 0, probs

    print("=" * 78)
    print("PART B 独立实现 vs 撰写人谓词，在撰写人 16 正 / 18 负样本上对跑")
    print("=" * 78)
    diff = []
    allrows = [("P", sid, txt, False) for sid, txt, _e, _n in reg.POSITIVES] + \
              [("N", sid, txt, True) for sid, txt, _e, _n in reg.NEGATIVES]
    for grp, sid, txt, expect_fail in allrows:
        m_fail, m_det = my_classify(txt)
        t_fail, t_probs = theirs(txt)
        ok_m = (m_fail == expect_fail)
        ok_t = (t_fail == expect_fail)
        agree = (m_fail == t_fail)
        flag = "" if agree else "  <<< 判定差异"
        print("%s %-4s expect=%-4s 我=%-4s(%s) 撰写人=%-4s(%s)%s" %
              (grp, sid, "FAIL" if expect_fail else "PASS",
               "FAIL" if m_fail else "PASS", "对" if ok_m else "错",
               "FAIL" if t_fail else "PASS", "对" if ok_t else "错", flag))
        if not agree:
            diff.append((sid, txt, expect_fail, m_fail, t_fail, m_det, t_probs))
    print()
    print("判定差异条数 =", len(diff))
    for sid, txt, expect, m, t, m_det, t_probs in diff:
        print("-" * 70)
        print("样本", sid, "期望", "FAIL" if expect else "PASS",
              "| 我判", "FAIL" if m else "PASS", "| 撰写人判", "FAIL" if t else "PASS")
        print("  文本:", repr(txt))
        print("  我的明细:", [(k, w) for _, _, k, w in m_det])
        print("  撰写人 problems:", t_probs)

    print()
    print("=" * 78)
    print("PART C 新负样本（撰写人样本集里没有的真断言），黑盒测撰写人谓词")
    print("=" * 78)
    # V1..V5 = 正式指定的 5 条新负样本；X* = 附加侦察样本
    NEW = [
        ("V1", "§2 已入账 grep 结果 / §3 结论：本笔已入账",
         "B 目录 + A 检索标记 + 无「可应用」尾部的主语断言"),
        ("V2", "不宣告 X 已生效，且本笔已入账",
         "C 否定 + 非「但」的并列转折（且）后接肯定断言"),
        ("V3", "已入账核查实跑命令：该笔已追加至台账尾部",
         "A 核查标签 + 已追加真断言，无可执行动作词"),
        ("V4", "有没有已入账的？有，第 5 笔已入账",
         "A 问句 + 肯定回答（主语=第 5 笔）"),
        ("V5", "### 2.2 待入账清点 + 已入账 grep 结果；本笔已入账",
         "B 标题 + 分号后另起真断言"),
        ("X1", "未验：本笔已入账", "前置「未」污染 R10 回看窗"),
        ("X2", "grep 结果：已入账", "A 检索结果 + 裸完成词"),
        ("X3", "§1 总览 / §2 已入账清单：第 5 笔已入账 / §3 依赖",
         "B 目录 + 清单 + 主语断言"),
        ("X4", "| 笔 | 已入账? |\n|:--|:--|\n| 1 | 本笔已入账 |",
         "表头合法 + 数据行主语断言（无「可应用」）"),
        ("X5", "已生效核查结果：本件已生效，照此执行", "A 标记 + 照此执行"),
        ("X6", "不宣告 N-4 正式绑定已生效，然而本笔已入账", "然而转折"),
        ("X7", "清点已追加 grep 结果；台账已追加第五节", "A 清点 + 分号 + 主语断言"),
        ("X8", "本笔已入账（未验项另计）", "主语断言 + 后置括号否定词"),
    ]
    misses = []
    for cid, txt, note in NEW:
        t_fail, t_probs = theirs(txt)
        m_fail, _ = my_classify(txt)
        status = "抓住" if t_fail else "★漏网"
        if not t_fail:
            misses.append((cid, txt, note))
        print("%-4s %-4s 撰写人=%-4s 我=%-4s | %s" %
              (cid, status, "FAIL" if t_fail else "PASS",
               "FAIL" if m_fail else "PASS", note))
        print("      文本:", repr(txt))
        if not t_fail:
            det = n13.r13_scan(txt, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)[1]
            print("      漏网明细:", [(d["kind"], d["rule"][:60]) for d in det])
    print()
    print("PART C 正式 5 条新负样本漏网 =",
          [c[0] for c in misses if c[0] in ("V1", "V2", "V3", "V4", "V5")])
    print("PART C 全部漏网 =", [c[0] for c in misses], "（共 %d 条）" % len(misses))
    return 0


if __name__ == "__main__":
    sys.exit(main())
