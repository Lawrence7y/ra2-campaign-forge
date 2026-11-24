# -*- coding: utf-8 -*-
r"""_gp_regression.py — 合成语料分层回归（第四步）。

语料 = 三族混合，逐条给期望：
  A. N13 负样本 26 条（_n13_regression.py:85-113 逐字导入，全部 expect=CATCH）
  B. N13 正样本 16 条（同文件 :46-80，全部 expect=PASS）
  C. R10 既有样本（三族，逐字/构造如实标注）：
     - g7 TV 反向验证 8 件（_g7_reverse_validate.py:20-25 的四真实件 + :62-68 的 TV1..TV7b）
     - g7 四真实件（R10 S1：期望全部 PASS，见 _g7_reverse_validate.py:53-77）
     - R9/R10 30 件历史语料清单（_g9_regression.py:26-57）本报告只取前 30 件的
       **逐件门禁结论**做对比，不把整件塞进单句语料（报告里如实说明）
  D. 三件真实交付件（C07_SLOT / TRUTH / BOUND），按各自任务书词表跑
  E. 本任务构造的冲突形态样本（同句混用 / 双重否定 / A 标记劫持 / GV-L 残余）

对每条跑：naive / 单层 R10 / 单层 R12 / 单层 N13 / 合成链，给最终判定与冲突数。
统计：误报 / 漏报 / 层间冲突；与单层对比是变好还是变差，如实报告。

实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_regression.py
零真机、零采样；只读既有件，写只落本写域。
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

N13_REG = ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py"
G7_RV = ROOT / "lead" / "gate_fp7_20261108" / "_g7_reverse_validate.py"
G9_REG = ROOT / "lead" / "gate_r9r12_20261109" / "_g9_regression.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    # 既有回归脚本 import 时即加载谓词，但不执行 main（有 __main__ 保护）
    spec.loader.exec_module(m)
    return m


reg = _load(N13_REG, "_gp_n13_reg")
g9 = _load(G9_REG, "_gp_g9_reg")
g7, n13, T = P.load_predicates()
T_C07_SLOT = ["已补登", "已填入", "已填", "已代填"]
T_C07_TRUTH = ["已填", "已代填", "已提交"]
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

# ---- 语料构造 -------------------------------------------------------------
CORPUS = []


def add(cid, family, text, expect, tokens, note):
    CORPUS.append({"id": cid, "family": family, "text": text,
                   "expect": expect, "tokens": tokens, "note": note})


# A. N13 负样本 26 条（_n13_regression.py:85-113 逐字）
for sid, text, note, src in reg.NEGATIVES:
    add("N13-" + sid, "N13_NEG", text, "CATCH", T, "逐字：" + src + " | " + note)
# B. N13 正样本 16 条（:46-80 逐字）
for sid, text, expect, src in reg.POSITIVES:
    add("N13-" + sid, "N13_POS", text, "PASS", T, "逐字：" + src)
# C1. R10 反向验证真违规样本（TV2 / TV3，逐字读盘）
for name, rel, expect in [
    ("TV2", "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md", "CATCH"),
    ("TV3", "lead/gate_fp7_20261108/_g7_tv3_double_negation.md", "CATCH"),
]:
    add("R10-" + name, "R10_TV", (ROOT / rel).read_text(encoding="utf-8"),
        expect, BAD_BAN, "逐字读盘 " + rel)
# C2. R10 四真实件（S1 期望 R10 problems=0；本链按 BAD_BAN 五词口径）
for rel in [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]:
    add("R10-REAL-" + pathlib.Path(rel).stem, "R10_REAL",
        (ROOT / rel).read_text(encoding="utf-8"), "PASS", BAD_BAN,
        "逐字读盘 " + rel + "（g7 S1：R10 problems=0）")
# C3. R10 语料中的「断言词语境」误报 11 条形态（取自 g7 文档 :106-108 与 N13 P08-P10）
for cid, text, note in [
    ("R10-CTX-01", "不宣告 N-4 正式绑定已生效。", "否定式（C）"),
    ("R10-CTX-02", "**不得写成「本笔已生效」**；本件只登记。", "禁止 + 引证跨度"),
    ("R10-CTX-03", "或回件出现「可应用/放行 N-5」断言", "短引证跨度内提及"),
    ("R10-CTX-04", "并无越权断言：本件不出现「可应用母本…」。", "两独立否定短语"),
    ("R10-CTX-05", "本件并非不宣告已生效", "双重否定（R12 应 CATCH）"),
    ("R10-CTX-06", "审阅不得不承认本候选已生效", "双重否定（R12 应 CATCH）"),
    ("R10-CTX-07", "**已入账核查实跑命令**：", "A 检索动作（N13 放过）"),
    ("R10-CTX-08", "## 2 · 上游指纹 + 已入账 grep 结果", "B 小节标题"),
    ("R10-CTX-09", "| 笔 | 已入账? |", "B 表头列名"),
    ("R10-CTX-10", "### 1(c) 有没有已入账的？", "A 问句"),
    ("R10-CTX-11", "本交付件改为五节：§1 总览 / §2 已入账 grep / §3 冲突", "B 目录枚举"),
]:
    exp = "CATCH" if cid in ("R10-CTX-05", "R10-CTX-06") else "PASS"
    add(cid, "R10_CTX", text, exp, BAD_BAN, "构造/逐字形态：" + note)
# D. 三件真实交付件（按各自任务书词表）
for cid, rel, toks, expect in [
    ("REAL-SLOT", "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", T_C07_SLOT, "PASS"),
    ("REAL-TRUTH", "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", T_C07_TRUTH, "PASS"),
    ("REAL-BOUND", "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", T, "PASS"),
]:
    add(cid, "REAL3", (ROOT / rel).read_text(encoding="utf-8"), expect, toks,
        "逐字读盘 " + rel + "（编排方指纹已复核）")
# E. 本任务构造的冲突形态（第三步 a/b：同句混用 / 双重否定 / A 标记劫持）
for cid, text, expect, note in [
    ("GP-C01", "grep 结果：已生效，可应用母本", "CATCH", "F03：A 标记劫持真断言（N13 _n13_new_fp_probe.py:40）"),
    ("GP-C02", "不宣告 X 已生效，但 Y 已入账", "CATCH", "同句混用（R10 CLAUSE_BREAK 不含逗号）"),
    ("GP-C04", "并非不宣告已生效", "CATCH", "R12 双重否定"),
    ("GP-C05", "未核 grep 结果：已入账 0 命中", "PASS", "前置否定标签 + A 检索结果；人工判检索结果，非完成断言"),
    ("GP-C06", "未核 grep 结果：已生效 0 命中", "PASS", "同上（已生效）"),
    ("GP-C07", "未核：已入账 grep 结果 = 0 命中", "PASS", "同上（标签在冒号前）"),
    ("GP-C08", "grep 结果：已入账", "CATCH", "裸完成词拿不准默认 FAIL（N13 N24）"),
    ("GP-C09", "未验：本笔已入账", "CATCH", "N19 前置标签 + 主语"),
    ("GP-C10", "grep 结果：第 5 笔已入账", "CATCH", "N20 A 标记 + 主语"),
]:
    add(cid, "GP_CONFLICT", text, expect, T, note)
# F. 「三层全说放过但实际有真断言」构造样本（第三步 d）
#    A1：分离型双重否定（N13 回归 §5 实跑：R10=negation / R12=0 / N13=C 放过）；
#        「亦非不宣告…已生效」= 不(不宣告) → 语义上仍是宣告，人工判真断言。
#    A2/A3：词表未登记的同义完成断言，三层都无 span 可判 → 静默 PASS。
for cid, text, note in [
    ("GP-A1", "亦非不宣告 N-4 正式绑定已生效", "分离型双重否定=肯定；编排方背景点名的 GV-L 残余"),
    ("GP-A2", "本件登记闭合，母本即日起适用", "同义完成断言；三词/BAD_BAN 五词均无字面命中"),
    ("GP-A3", "三值填毕，见证已由编排方签字", "C07 域同义完成断言；C07 词表与 N13 三词均无命中"),
]:
    add(cid, "GP_ALLPASS_TRUE_ASSERTION", text, "CATCH", T, note)

# ---- 逐条跑 ---------------------------------------------------------------
def judge_one(item, mode):
    """mode ∈ {naive, r10, r12, n13, chain}。返回 CATCH/PASS。"""
    text, toks = item["text"], item["tokens"]
    if mode == "naive":
        return "CATCH" if any(t in text for t in toks) else "PASS"
    if mode == "r10":
        return "CATCH" if g7.r10_scan(text, toks)[0] else "PASS"
    if mode == "r12":
        return "CATCH" if g7.r12_scan(text, toks)[0] else "PASS"
    if mode == "n13":
        p, _ = n13.r13_assertions(text, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
        return "CATCH" if p else "PASS"
    r = P.gate_check(text, toks, WD, g7, n13, T)
    # 合成链只看越权断言面（R9/R11 是独立项，不混入本判定，逐层结果仍留盘）。
    # ★ 用【逐 span 裁决】的 ADJUDICATED problems，而不是三层 problems 的朴素并集。
    adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    final = "CATCH" if adj else "PASS"
    return final, r["summary"]["conflicts"], r["summary"]["unresolved"]


out_rows, stat = [], {m: {"ok": 0, "fp": 0, "fn": 0} for m in
                      ("naive", "r10", "r12", "n13", "chain")}
chain_conflicts = chain_unresolved = 0
for it in CORPUS:
    row = {"id": it["id"], "family": it["family"], "expect": it["expect"],
           "tokens": it["tokens"], "note": it["note"],
           "text_head": it["text"][:90].replace("\n", "\\n")}
    for m in ("naive", "r10", "r12", "n13"):
        got = judge_one(it, m)
        row[m] = got
        if got == it["expect"]:
            stat[m]["ok"] += 1
        elif it["expect"] == "PASS":
            stat[m]["fp"] += 1
        else:
            stat[m]["fn"] += 1
    fin, nc, nu = judge_one(it, "chain")
    row["chain"] = fin
    row["layer_conflicts"] = nc
    row["layer_unresolved"] = nu
    chain_conflicts += nc
    chain_unresolved += nu
    if fin == it["expect"]:
        stat["chain"]["ok"] += 1
    elif it["expect"] == "PASS":
        stat["chain"]["fp"] += 1
    else:
        stat["chain"]["fn"] += 1
    out_rows.append(row)

# 逐族统计
by_family = {}
for r in out_rows:
    f = r["family"]
    b = by_family.setdefault(f, {"n": 0, "chain_ok": 0, "chain_fp": 0,
                                 "chain_fn": 0, "conflicts": 0})
    b["n"] += 1
    b["conflicts"] += r["layer_conflicts"]
    if r["chain"] == r["expect"]:
        b["chain_ok"] += 1
    elif r["expect"] == "PASS":
        b["chain_fp"] += 1
    else:
        b["chain_fn"] += 1

payload = {
    "corpus_n": len(CORPUS),
    "sources": {
        "N13_NEG": "lead/gate_n13_20261109/_n13_regression.py:85-113（26 条逐字）",
        "N13_POS": "lead/gate_n13_20261109/_n13_regression.py:46-80（16 条逐字）",
        "R10_TV": "lead/gate_fp7_20261108/_g7_tv2/_g7_tv3（逐字读盘）",
        "R10_REAL": "lead/gate_fp7_20261108/_g7_reverse_validate.py:20-25 四真实件",
        "R10_CTX": "lead/gate_fp7_20261108/_g7_patch.md:106-108 + N13 P08-P10 形态（构造）",
        "REAL3": "三件编排方指纹件（逐字读盘）",
        "GP_CONFLICT": "本任务第三步构造（含三层全放过的真断言样本）",
    },
    "not_in_corpus": {
        "g9_DOCS_30": "lead/gate_r9r12_20261109/_g9_regression.py:26-57 的 30 件历史语料"
                      " 未作为单句语料塞入（其门禁项含 R9/R11 且与越权断言面不同口径）；"
                      " 本报告另在 _gp_probe.py 对其中四真实件做了 R10/N13 复跑",
        "g7_TV1_4_5_6_7_7b": "TV1/TV4/TV5/TV6/TV7/TV7b 是 R9/R11 的违规样本，"
                             " 不含越权断言面；本回归只收 TV2/TV3，其余如实排除",
    },
    "single_layer_vs_chain": stat,
    "chain_conflicts_total": chain_conflicts,
    "chain_unresolved_total": chain_unresolved,
    "by_family": by_family,
    "rows": out_rows,
}
(WD / "_gp_regression_out.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

# ---- 控制台输出 ----
print("== 合成语料 =", len(CORPUS), "条 ==")
for f, b in by_family.items():
    print("  %-12s n=%-3d chain_ok=%-3d FP=%-2d FN=%-2d 层间冲突=%d" %
          (f, b["n"], b["chain_ok"], b["chain_fp"], b["chain_fn"], b["conflicts"]))
print("\n== 单层 vs 合成（全语料 %d 条）==" % len(CORPUS))
for m in ("naive", "r10", "r12", "n13", "chain"):
    s = stat[m]
    print("  %-6s 正确=%-3d 误报(FP)=%-3d 漏报(FN)=%-3d" % (m, s["ok"], s["fp"], s["fn"]))
print("  合成链层间冲突总数 =", chain_conflicts, " 其中未消解 =", chain_unresolved)
print("\n== 逐条最终判定（仅列出与期望不符 / 有冲突的条，其余见 JSON）==")
for r in out_rows:
    bad = r["chain"] != r["expect"]
    if bad or r["layer_conflicts"]:
        print("  %-14s expect=%-5s naive=%-5s r10=%-5s r12=%-5s n13=%-5s chain=%-5s conflict=%d %s | %s" %
              (r["id"], r["expect"], r["naive"], r["r10"], r["r12"], r["n13"],
               r["chain"], r["layer_conflicts"], "MISMATCH" if bad else "",
               r["text_head"][:60]))
print("\n== 全表（每条最终判定）==")
for r in out_rows:
    print("  %-14s %-5s %s" % (r["id"], r["chain"], r["text_head"][:70]))
print("\nwritten:", WD / "_gp_regression_out.json")
