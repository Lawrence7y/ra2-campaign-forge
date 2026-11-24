# -*- coding: utf-8 -*-
r"""_r9sd_extra.py — 两处补证：(a) R10 对 3 条剩余非要素问题的豁免；(b) 角色消融负样本。
只读；输出落 _r9sd_extra_stdout.txt。
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(WDIR))
import _r9s_predicates as R9S

g7 = R9S.R9

print("=== (a) R10 对 RULING_MATRIX_AB.md 三条越权断言 ===")
t = (ROOT / "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md").read_text(encoding="utf-8")
probs, warns, hits = g7.r10_scan(t, ["已改矩阵", "已收紧", "已施行", "已改设计"])
print("  problems =", json.dumps(probs, ensure_ascii=False))
for h in hits:
    print("  hit", json.dumps(h, ensure_ascii=False))
print("  all_negation_or_quote =", all(h["kind"] in ("negation", "quote_mention") for h in hits))

print("\n=== (b) 角色消融负样本（删任一必选角色，期望 present=False） ===")
# 每条从对应正例出发，只删掉/替换一个角色；文本逐字写在下面。
ABL = [
    ("A1_S1_drop_agent", "需谁批准",
     "## 5 裁决与可执行改动清单\n"
     "### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **待指定**，pf2:200）\n"),
    ("A2_S1_drop_assign", "需谁批准",
     "## 5 裁决与可执行改动清单\n"
     "### 5.2 可执行改动清单（★ 处方，未实施；批准人须经治理链确认，乙设计责任人参与讨论）\n"),
    ("A3_S2_drop_payload", "实跑输出",
     "## 3 实证\n"
     "- **构造输入 → 实跑返回**：classify 直调，16/16 格实跑：\n"
     "```\n（本轮已实跑并记录，输出见 _out.txt:159-174）\n```\n"),
    ("A4_S3_drop_after", "改前改后",
     "## 4 订正草案（改前/改后逐处对照）\n"
     "- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n"),
    ("A5_S3_drop_compare", "改前改后",
     "## 4 订正草案\n"
     "- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n"
     "- 【改后】本件按 13 项分写，与裁决列名逐项对应，无缺漏、无新增。\n"),
    ("A6_S4_drop_polarity", "脚本存在性",
     "## 3 脚本搜索全结果与存在性判定（四路逐路）\n"
     "全树 .py 共 11790 个，逐路结论：已查生成脚本，命中若干复核件。\n"),
    ("A7_S5_drop_evidence", "可重建",
     "## 4 重建可行性与单向压缩候选筛选\n"
     "**判定：正确算法【可唯一重建】。**\n"),
]
rows = []
for aid, tok, txt in ABL:
    ok, layer, detail = R9S.r9s_element_present(txt, tok)
    rows.append({"id": aid, "token": tok, "present": ok, "layer": layer})
    print("  %-22s %-8s present=%-5s layer=%s" % (aid, tok, ok, layer or "(none)"))
n_fail = sum(1 for x in rows if not x["present"])
print("  角色消融判缺失 = %d/%d  all_fail=%s" % (n_fail, len(rows), n_fail == len(rows)))
