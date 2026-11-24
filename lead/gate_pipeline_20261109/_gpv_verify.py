# -*- coding: utf-8 -*-
r"""_gpv_verify.py — 独立复核员：③ 消解规则可执行性 / ④ 跨层混合样本 / ⑦ 门槛。
本件只用 _gpv_ 前缀，落在唯一写域；只读加载既有谓词与 _gp_pipeline 骨架。
零真机、零采样；Python: python -I -X utf8 <绝对路径>。
"""
import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"
sys.path.insert(0, str(WD))
import _gp_pipeline as P  # noqa: E402

G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13 = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
g7, n13, T = P.load_predicates()
DOC_DIR = WD
OUT = {}


def layers_of(text, tokens):
    return P.run_layers(g7, n13, T, text, tokens, DOC_DIR, root=ROOT)


def chain_of(text, tokens):
    return P.gate_check(text, tokens, DOC_DIR, g7, n13, T, root=ROOT)


def brief(text, tokens):
    L = layers_of(text, tokens)
    p10, w10, h10 = g7.r10_scan(text, tokens)
    p12, h12 = g7.r12_scan(text, tokens)
    p13, d13 = n13.r13_assertions(text, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    r = chain_of(text, tokens)
    return {"R10_kinds": [(h["token"], h["pos"], h["kind"]) for h in h10],
            "R10_problems": p10,
            "R12_problems": p12,
            "N13_details": [(d["token"], d["pos"], d["line"], d["kind"])
                            for d in d13],
            "N13_problems": p13,
            "chain_verdict": r["verdict"],
            "chain_assertion_face": ("CATCH" if any(
                p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")
                for p in r["problems"]) else "PASS"),
            "R9_R11_problems": [p for p in r["problems"]
                                if p["rule_id"] in ("R9", "R11")],
            "chain_summary": r["summary"],
            "rows": [{"token": x["token"], "pos": x["pos"], "line": x["line"],
                      "r10": x["r10"], "r12": x["r12"], "n13": x["n13"],
                      "verdict": x["verdict"], "rules": x["rules"],
                      "n13_veto": x.get("n13_veto"), "quote": x.get("quote", "")}
                     for x in r["_rows"]],
            "conflicts": r["conflicts"],
            "ADJ": [p["msg"] for p in r["problems"] if p["rule_id"] == "ADJUDICATED"],
            "NEEDS_HUMAN": [p["msg"] for p in r["problems"]
                            if p["rule_id"] == "NEEDS_HUMAN"]}


# ===========================================================================
# ③ 消解规则可执行性：逐条打靶 + 构造样本给确定答案
# ===========================================================================
SEC3 = []
CASES = [
    # (id, text, tokens, human_truth, 预期触发的规则/说明)
    ("K1_dbl", "并非不宣告已生效", T, "CATCH", "R12 double_neg ⇒ K1"),
    ("K2_mixed", "不宣告 X 已生效，但 Y 已入账", T, "CATCH", "N13=D 且 R10=negation ⇒ K2"),
    ("K2_unverified", "未验：本笔已入账", T, "CATCH", "N13=D / R10=negation ⇒ K2"),
    ("K9_A", "grep 结果：已生效 0 命中", T, "PASS", "N13=A 精筛 ⇒ K3+K9"),
    ("K9_B", "### 1(c) 有没有已入账的？", T, "PASS", "N13=A ⇒ K9"),
    ("K4_F03", "grep 结果：已生效，可应用母本", T, "CATCH", "行级肯定守卫作废 A ⇒ K4"),
    ("K4_F03_neg", "未核 grep 结果：已生效，可应用母本", T, "CATCH", "R10 negation / N13 D ⇒ K2"),
    ("K6_outofvocab", "本件已填，须按格式填写", ["已填"], "CATCH", "token 不在 N13 三词 ⇒ K6 采 R10"),
    ("K8_unresolved", "已入账核查清单：本笔已生效", T, "CATCH", "同行 D + A/B ⇒ K4 提升"),
    ("K5_crossline", "## 2 已入账 grep 结果\n本笔已入账。", T, "CATCH", "跨行不传播，下行 D"),
]
for cid, text, toks, truth, note in CASES:
    b = brief(text, toks)
    SEC3.append({"id": cid, "text": text, "tokens": toks, "human_truth": truth,
                 "note": note, **b})
OUT["SEC3_rule_determinism"] = SEC3

# 构造样本（复核员自造，不在 _gp_regression 语料里）：
# 两个 token 同行，一个 N13=A 放过 + 一个 R10=assertion 抓住，看是否给「一个确定答案」
CONSTRUCTED = [
    ("CSTRUCT-1", "grep 结果：已入账 0 命中，但本笔已生效", T, "CATCH",
     "A 标记 + 同句真断言混用（人工真值=有真断言）"),
    ("CSTRUCT-2", "未核 grep 结果：已生效 0 命中", T, "PASS",
     "否定前缀 + A 标记，无真断言"),
    ("CSTRUCT-3", "已入账核查清单：本笔已追加", T, "CATCH",
     "A 标记 + 另一微段真断言"),
]
OUT["SEC3_constructed"] = [{"id": cid, "text": text, "tokens": toks,
                            "human_truth": truth, "note": note, **brief(text, toks)}
                           for cid, text, toks, truth, note in CONSTRUCTED]

# ===========================================================================
# ④ 跨层混合样本：A 标记 + 真断言 + 否定前缀三者混合（复核员自造 3 条）
# ===========================================================================
MIXED = [
    ("MIX-1", "未核 grep 结果：已入账 0 命中，但本笔已生效，可应用母本", T, "CATCH",
     "否定前缀(未核)+A标记(grep/0 命中)+真断言(本笔已生效，可应用母本)"),
    ("MIX-2", "不宣告 X 已生效，但 grep 结果：已入账 0 命中", T, "CATCH",
     "否定前缀(不宣告)+A标记(grep/0 命中)+转折肯定(但…已入账)"),
    ("MIX-3", "亦非不宣告 N-4 正式绑定已生效，grep 结果：已入账 0 命中", T, "CATCH",
     "分离型双重否定(亦非不)+真断言+A标记(0 命中)"),
    ("MIX-4", "未核 grep 结果：已生效 0 命中；三值填毕，见证已由编排方签字", T, "CATCH",
     "否定前缀+A标记+词表外同义完成断言（三层全无 span）"),
    ("MIX-5", "grep 结果：已入账 0 命中，且 N-4 正式绑定已生效", T, "CATCH",
     "A 标记 + 转折肯定(且…已生效)"),
]
OUT["SEC4_mixed"] = [{"id": cid, "text": text, "tokens": toks,
                      "human_truth": truth, "note": note, **brief(text, toks)}
                     for cid, text, toks, truth, note in MIXED]

# ④ 撰写人自认三条（独立复核：是否真的兜不住 / 是否偷懒）
ALLPASS = [
    ("GP-A1", "亦非不宣告 N-4 正式绑定已生效"),
    ("GP-A2", "本件登记闭合，母本即日起适用"),
    ("GP-A3", "三值填毕，见证已由编排方签字"),
]
OUT["SEC4_author_allpass"] = [
    {"id": cid, "text": text, "tokens": T, "human_truth": "CATCH",
     "note": "撰写人 3(d) 自认兜不住", **brief(text, T)} for cid, text in ALLPASS]

# ===========================================================================
# ⑦ 回归门槛可执行性检查：读源文件，找断言 / raise / exit code
# ===========================================================================
gr = (WD / "_gp_regression.py").read_text(encoding="utf-8")
OUT["SEC7_gate_scan"] = {
    "regression_has_assert": "assert " in gr,
    "regression_has_raise": "raise " in gr,
    "regression_has_sys_exit": "sys.exit" in gr,
    "regression_has_threshold_literal_FP2": "FP ≤ 2" in (WD / "_gp_DESIGN.md").read_text(encoding="utf-8"),
    "design_lines_371_377": (WD / "_gp_DESIGN.md").read_text(encoding="utf-8").splitlines()[370:377],
}

(WD / "_gpv_verify_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")


def show(tag, items):
    print("\n===== %s =====" % tag)
    for it in items:
        print("\n[%s] %r" % (it["id"], it["text"]))
        print("  人工真值=%s  note=%s" % (it["human_truth"], it["note"]))
        print("  R10 kinds=%s problems=%d" % (it["R10_kinds"], len(it["R10_problems"])))
        print("  R12 problems=%d" % len(it["R12_problems"]))
        print("  N13 details=%s problems=%d" % (it["N13_details"], len(it["N13_problems"])))
        print("  chain verdict=%s summary=%s" % (it["chain_verdict"], it["chain_summary"]))
        for r in it["rows"]:
            print("    ROW tok=%s pos=%s L%s r10=%s r12=%s n13=%s veto=%s => %s rules=%s | %s" %
                  (r["token"], r["pos"], r["line"], r["r10"], r["r12"], r["n13"],
                   r["n13_veto"], r["verdict"], ",".join(r["rules"]), r["quote"][:60]))
        if it["ADJ"]:
            print("    ADJ:", it["ADJ"][:3])
        if it["NEEDS_HUMAN"]:
            print("    NEEDS_HUMAN:", it["NEEDS_HUMAN"][:3])
        got = it["chain_assertion_face"]
        print("  ==> chain 断言面(ADJUDICATED口径) = %s  人工 = %s  %s" %
              (got, it["human_truth"], "OK" if got == it["human_truth"] else "MISMATCH"))


show("③ K 规则打靶（含 F03 三形态）", SEC3)
show("③ 复核员自造构造样本", OUT["SEC3_constructed"])
show("④ 跨层混合样本（A 标记 + 真断言 + 否定前缀）", OUT["SEC4_mixed"])
show("④ 撰写人自认兜不住三条（独立复核）", OUT["SEC4_author_allpass"])
print("\n===== ⑦ 门槛扫描 =====")
print(json.dumps(OUT["SEC7_gate_scan"], ensure_ascii=False, indent=1))
print("\nwritten:", WD / "_gpv_verify_out.json")
