# -*- coding: utf-8 -*-
r"""_r9s_step1_verify.py — 第一步独立复核 5 处（a/b/c）。

(a) 自跑 r9_element_present：印 literal_present / r9_present / r9_layer / 所在行原文；
(b) 逐处读原句上下文（邻近行窗口），判断语义是否真的在场；
(c) 判定是否有「看起来像但语义也不在场」的真缺失。

只读；写仅落本写域 _r9s_step1_out.json。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(WDIR))
import _r9s_predicates as R  # noqa: E402

CASES = [
    ("lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md", "需谁批准", 108,
     (106, 112)),
    ("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", "实跑输出", 65,
     (62, 75)),
    ("lead/n11_wording_fix_20261108/N11_WORDING_FIX.md", "改前改后", 76,
     (76, 90)),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", "脚本存在性", 32,
     (30, 45)),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", "可重建", 87,
     (73, 88)),
]

# 逐处 (b)/(c) 的形式化结论；依据写到「文件:行」。
VERDICTS = {
    "需谁批准": {
        "semantic_present": True,
        "kind": "语义在场（措辞变体）",
        "basis": "RULING_MATRIX_AB.md:108「批准人一律 = **乙设计责任人**，pf2:200」。"
                 "「需谁批准」是 wh-问句，指称其真答案集合；赋值句把 wh-变量约束成具体施事且断言一律/唯一，"
                 "是该集合的一员且更强。:138「若批准人不采随批」进一步佐证批准人角色在治理链上真实生效。",
        "why_not_fake": "不是「只提到批准」——「一律 = 乙设计责任人」给出了可指认的施事值，回答了『谁』。",
    },
    "实跑输出": {
        "semantic_present": True,
        "kind": "语义在场（措辞变体 + 载荷在场）",
        "basis": "MATRIX_DEFECT_REACHABILITY.md:65「构造输入 → 实跑返回……16/16 格实跑：」命名事件；"
                 ":67-72 围栏块给出 `verdict='post_read_error' conf='none' is_new=None pre_state='unknown'` 等"
                 "**带具体值的返回数据行**，:69-71 三行逐一列不同 pre 变体的实际返回值；:74「16/16，out:159-174」"
                 "复核输出索引；:26 逐条列出实跑命令与 239 行 PROBE_DONE 输出。Run(e) ∧ Output(e,o) ∧ Present(o) 三半齐备。",
        "why_not_fake": "★ 单独「实跑返回」不够（只是命名事件），单独 `out:159-174` 也不够（只是索引）；"
                        "本件的等价性来自 :69-71 的**输出对象本身**逐字在盘，且 :80-87 §3.2 复现同一形态。"
                        "若只有「16/16 格实跑」而无带值数据行，本设计判 FAIL（负样本 N06/N07/N10）。",
    },
    "改前改后": {
        "semantic_present": True,
        "kind": "语义在场（斜杠/标签分隔变体）",
        "basis": "N11_WORDING_FIX.md:76「改前/改后逐处对照」；:81【改前】完整原句、:82【改后】完整改句；"
                 ":88/:89 方案 B 再给一对；:97「三案均只处理 _ps:54 一句」。"
                 "Before(t) ∧ After(t) ∧ Compare(t) 在同一 `## 4` 小节齐备。",
        "why_not_fake": "两半都带实值文本，且标题明写「逐处对照」；不是只提一个术语。",
    },
    "脚本存在性": {
        "semantic_present": True,
        "kind": "语义在场（判定已交付；极性为负）",
        "basis": "S604_SCRIPT_GAP.md:10「生成脚本是否在盘、能否重建」提出问题；:32 §3 标题「脚本搜索全结果与"
                 "存在性判定」；:34-67 四路逐路结论（:44「均无 §604 生成器」/:51「无一生成器」/:59「明载脚本未落盘」"
                 "/:67「脚本从未写入台账」）；:69-71 §3.5「存在性判定」下判「【不存在且从未落盘】」。",
        "why_not_fake": "要素问的是**判定**而非「存在」；判不存在也是已交付的判定。四路独立证据 + 明确极性闭环。",
    },
    "可重建": {
        "semantic_present": True,
        "kind": "语义在场（程度副词插入变体）",
        "basis": "S604_SCRIPT_GAP.md:73 §4「重建可行性」；:77-83 五项口径唯一性表（口径 1/4「唯一性」列）；"
                 ":87「判定：正确算法【可唯一重建】。已有四重独立实现逐位一致……max|Δ|=0.000000」。"
                 "「可」= ◇ 情态头、「重建」= 动作头均保留，「唯一」只强化确定性不换头；且有确定性证据。",
        "why_not_fake": "不是只写「已分析」；同小节同时给出肯定的 ◇Reconstruct 结论与五重独立实现逐位一致的证据。",
    },
}

out = {"pred_sha256": hashlib.sha256(R.R9_PATH.read_bytes()).hexdigest(),
       "pred_bytes": R.R9_PATH.stat().st_size, "cases": []}
for rel, tok, line, (lo, hi) in CASES:
    p = ROOT / rel
    raw = p.read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines()
    lit = tok in text
    ok_r9, layer_r9 = R.R9.r9_element_present(text, tok)
    ok_r9s, layer_r9s, detail = R.r9s_element_present(text, tok)
    rec = {
        "rel": rel, "token": tok, "line": line,
        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
        "literal_present": lit, "r9_present": ok_r9, "r9_layer": layer_r9,
        "r9s_present": ok_r9s, "r9s_layer": layer_r9s,
        "r9s_spec": detail.get("spec"),
        "r9s_evidence": detail.get("evidence", [])[:2],
        "lineText": lines[line - 1] if line <= len(lines) else "",
        "context_lines": [{"n": n, "text": lines[n - 1]}
                          for n in range(lo, min(hi, len(lines)) + 1)],
        "verdict": VERDICTS[tok],
    }
    out["cases"].append(rec)
    print("=== %s / %s (L%d) ===" % (rel, tok, line))
    print("  literal_present=%s r9_present=%s r9_layer=%r" % (lit, ok_r9, layer_r9))
    print("  r9s_present=%s r9s_layer=%r spec=%s" % (ok_r9s, layer_r9s, rec["r9s_spec"]))
    print("  lineText: %s" % rec["lineText"])
    print("  语义在场=%s 类别=%s" % (rec["verdict"]["semantic_present"], rec["verdict"]["kind"]))
    print("  依据: %s" % rec["verdict"]["basis"])
    print("  非假象: %s" % rec["verdict"]["why_not_fake"])
    print()

out["any_true_missing"] = [c["token"] for c in out["cases"]
                           if not c["verdict"]["semantic_present"]]
out["n_semantic_present"] = sum(1 for c in out["cases"]
                                if c["verdict"]["semantic_present"])
print("结论：5 处中语义也不在场的真缺失 = %s；语义在场 = %d/5"
      % (json.dumps(out["any_true_missing"], ensure_ascii=False),
         out["n_semantic_present"]))
(WDIR / "_r9s_step1_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
