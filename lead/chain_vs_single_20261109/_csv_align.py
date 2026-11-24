# -*- coding: utf-8 -*-
"""_csv_align.py — 独立复核「输入对齐后 N13 66/74 vs chain 69/74」。

不采信 _cs_align_out.txt 的数字。语料全文显式重建（逐字照 _gp_regression.py:61-130），
与只读 JSON 的 (id,family,expect,tokens,text_head) 逐行核对；再独立调用只读谓词
n13.r13_assertions(text, item['tokens']) 与 n13.r13_assertions(text, T)。
chain/naive/r10/r12 直接取只读 JSON rows（本脚本不改任何语料/谓词/K 规则）。
"""
import hashlib
import importlib.util
import json
import pathlib
import sys
from math import comb

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "chain_vs_single_20261109"
GP = ROOT / "lead" / "gate_pipeline_20261109"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13P = ROOT / "lead" / "gate_n13_20261109" / "lead/gate_n13_20261109/_n13_predicates.py"
N13R = ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py"
sys.path.insert(0, str(GP))
import _gp_pipeline as P  # noqa: E402

g7, n13, T = P.load_predicates()
reg = importlib.util.spec_from_file_location("_csv_reg", N13R)
m = importlib.util.module_from_spec(reg)
reg.loader.exec_module(m)

T_SLOT = ["已补登", "已填入", "已填", "已代填"]
T_TRUTH = ["已填", "已代填", "已提交"]
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

CORPUS = []
def add(cid, family, text, expect, tokens):
    CORPUS.append({"id": cid, "family": family, "text": text,
                   "expect": expect, "tokens": list(tokens)})

for sid, text, note, src in m.NEGATIVES:
    add("N13-" + sid, "N13_NEG", text, "CATCH", T)
for sid, text, expect, src in m.POSITIVES:
    add("N13-" + sid, "N13_POS", text, "PASS", T)
for name, rel, expect in [
    ("TV2", "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md", "CATCH"),
    ("TV3", "lead/gate_fp7_20261108/_g7_tv3_double_negation.md", "CATCH"),
]:
    add("R10-" + name, "R10_TV", (ROOT / rel).read_text(encoding="utf-8"), expect, BAD_BAN)
for rel in [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]:
    add("R10-REAL-" + pathlib.Path(rel).stem, "R10_REAL",
        (ROOT / rel).read_text(encoding="utf-8"), "PASS", BAD_BAN)
for cid, text in [
    ("R10-CTX-01", "不宣告 N-4 正式绑定已生效。"),
    ("R10-CTX-02", "**不得写成「本笔已生效」**；本件只登记。"),
    ("R10-CTX-03", "或回件出现「可应用/放行 N-5」断言"),
    ("R10-CTX-04", "并无越权断言：本件不出现「可应用母本…」。"),
    ("R10-CTX-05", "本件并非不宣告已生效"),
    ("R10-CTX-06", "审阅不得不承认本候选已生效"),
    ("R10-CTX-07", "**已入账核查实跑命令**："),
    ("R10-CTX-08", "## 2 · 上游指纹 + 已入账 grep 结果"),
    ("R10-CTX-09", "| 笔 | 已入账? |"),
    ("R10-CTX-10", "### 1(c) 有没有已入账的？"),
    ("R10-CTX-11", "本交付件改为五节：§1 总览 / §2 已入账 grep / §3 冲突"),
]:
    add(cid, "R10_CTX", text, "CATCH" if cid in ("R10-CTX-05", "R10-CTX-06") else "PASS", BAD_BAN)
for cid, rel, toks in [
    ("REAL-SLOT", "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", T_SLOT),
    ("REAL-TRUTH", "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", T_TRUTH),
    ("REAL-BOUND", "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", T),
]:
    add(cid, "REAL3", (ROOT / rel).read_text(encoding="utf-8"), "PASS", toks)
for cid, text, expect in [
    ("GP-C01", "grep 结果：已生效，可应用母本", "CATCH"),
    ("GP-C02", "不宣告 X 已生效，但 Y 已入账", "CATCH"),
    ("GP-C04", "并非不宣告已生效", "CATCH"),
    ("GP-C05", "未核 grep 结果：已入账 0 命中", "PASS"),
    ("GP-C06", "未核 grep 结果：已生效 0 命中", "PASS"),
    ("GP-C07", "未核：已入账 grep 结果 = 0 命中", "PASS"),
    ("GP-C08", "grep 结果：已入账", "CATCH"),
    ("GP-C09", "未验：本笔已入账", "CATCH"),
    ("GP-C10", "grep 结果：第 5 笔已入账", "CATCH"),
]:
    add(cid, "GP_CONFLICT", text, expect, T)
for cid, text in [
    ("GP-A1", "亦非不宣告 N-4 正式绑定已生效"),
    ("GP-A2", "本件登记闭合，母本即日起适用"),
    ("GP-A3", "三值填毕，见证已由编排方签字"),
]:
    add(cid, "GP_ALLPASS_TRUE_ASSERTION", text, "CATCH", T)

print("=== [A] 语料重建保真度核对 ===")
cur = json.loads((GP / "_gp_regression_out.json").read_text(encoding="utf-8"))
J = {r["id"]: r for r in cur["rows"]}
print("重建 len=%d  JSON rows=%d" % (len(CORPUS), len(J)))
mism = []
for it in CORPUS:
    j = J.get(it["id"])
    head = it["text"][:90].replace("\n", "\\n")
    if j is None or not (j["family"] == it["family"] and j["expect"] == it["expect"]
                         and list(j["tokens"]) == list(it["tokens"]) and j["text_head"] == head):
        mism.append(it["id"])
print("逐行 (id,family,expect,tokens,text_head) 不一致 =", len(mism), mism[:10])

print("\n=== [B] 独立重跑 N13：固定三词 vs 该行 tokens ===")
def stat(pairs):
    ok = fp = fn = 0
    for e, v in pairs:
        if e == v: ok += 1
        elif e == "PASS": fp += 1
        else: fn += 1
    return ok, fp, fn, len(pairs)

fixed, aligned = [], []
for it in CORPUS:
    p1, _ = n13.r13_assertions(it["text"], T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    p2, _ = n13.r13_assertions(it["text"], it["tokens"], r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    v1 = "CATCH" if p1 else "PASS"
    v2 = "CATCH" if p2 else "PASS"
    fixed.append((it["expect"], v1))
    aligned.append((it["expect"], v2))
    if v1 != J[it["id"]]["n13"]:
        print("  !! harness n13 不一致", it["id"], v1, J[it["id"]]["n13"])
print("N13(固定三词 T)      ok/fp/fn/n =", stat(fixed))
print("N13(对齐 per-row)     ok/fp/fn/n =", stat(aligned))
print("chain(只读 JSON)      ok/fp/fn/n =", stat([(r["expect"], r["chain"]) for r in cur["rows"]]))
print("对齐后 N13 新增 FP id =", [it["id"] for it, (e, v), (e2, v2) in zip(CORPUS, fixed, aligned)
                                if e == "PASS" and v == "PASS" and v2 == "CATCH"])

print("\n=== [C] 对齐口径配对检验（exact binomial 双侧） ===")
b = sum(1 for it, (e, v) in zip(CORPUS, aligned) if J[it["id"]]["chain"] != e and v == e)
c = sum(1 for it, (e, v) in zip(CORPUS, aligned) if J[it["id"]]["chain"] == e and v != e)
n = b + c
p = min(1.0, 2 * sum(comb(n, k) for k in range(0, min(b, c) + 1)) / (2 ** n))
print("b(chain错 n13_aligned对)=%d c(chain对 n13_aligned错)=%d n=%d p=%.4f" % (b, c, n, p))

print("\n=== [D] 换考题集（用重建语料 + 只读 JSON 的 chain 列） ===")
SETS = {
    "N13自家42": {"N13_NEG", "N13_POS"},
    "R10考题17": {"R10_TV", "R10_REAL", "R10_CTX"},
    "中性第三方15": {"REAL3", "GP_CONFLICT", "GP_ALLPASS_TRUE_ASSERTION"},
    "全74": None,
}
for name, fams in SETS.items():
    idx = [i for i, it in enumerate(CORPUS) if fams is None or it["family"] in fams]
    sub_fix = stat([fixed[i] for i in idx])[0]
    sub_aln = stat([aligned[i] for i in idx])[0]
    sub_ch = stat([(r["expect"], r["chain"]) for r in cur["rows"] if r["id"] in {CORPUS[i]["id"] for i in idx}])[0]
    print("  %-14s n=%2d n13_fixed=%2d n13_aligned=%2d chain=%2d" % (name, len(idx), sub_fix, sub_aln, sub_ch))

print("\n=== [E] 本脚本是否写只读件 ===")
print("  本脚本只读 GP/_gp_regression_out.json 与 N13 谓词，所有输出打印到 stdout；未写任何只读目录。")
