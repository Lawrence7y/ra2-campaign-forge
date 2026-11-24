# -*- coding: utf-8 -*-
"""_ei_04_v12_layer.py — run V1V2 as a 4th layer on the exact 74-row corpus.

The corpus is rebuilt in-memory from the same read-only sources used by
lead/gate_pipeline_20261109/_gp_regression.py:61-130 (N13 regression samples,
g7 TV docs, 4 real docs, constructed R10_CTX / GP_CONFLICT / GP_A forms, 3 real
deliverables). No predicate module and no corpus file is modified: this script
only reads them and writes outputs into lead/evidence_indep_20261109/.

V1V2 operationalization (identical to the harness in
lead/chain_vs_single_20261109/_cs_holdout.py:65-72):
  for tok in set(V2_OVERRIDE + N13.DEFAULT_TOKENS):
      for each occurrence: if classify_v12(...).verdict == 'V2' -> CATCH

python -I -X utf8 -B <abs path>
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"
G7_PATH = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
V12_PATH = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
REG_OUT = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json"
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"
N13_N = 16649


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def n13_path():
    hits = [p for p in sorted(N13_DIR.iterdir()) if p.is_file() and fp(p) == (N13_SHA, N13_N)]
    assert len(hits) == 1
    return hits[0]


def load(path, name, want=None):
    got = fp(path)
    if want:
        assert got == want, "FP mismatch %s" % path
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build_corpus(n13, reg):
    """Mirror _gp_regression.py:52-130 exactly (read-only sources)."""
    T = list(n13.DEFAULT_TOKENS)
    T_C07_SLOT = ["已补登", "已填入", "已填", "已代填"]
    T_C07_TRUTH = ["已填", "已代填", "已提交"]
    BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
    C = []

    def add(cid, family, text, expect, tokens, note):
        C.append({"id": cid, "family": family, "text": text,
                  "expect": expect, "tokens": tokens, "note": note})

    for sid, text, note, src in reg.NEGATIVES:
        add("N13-" + sid, "N13_NEG", text, "CATCH", T, "逐字：" + src + " | " + note)
    for sid, text, expect, src in reg.POSITIVES:
        add("N13-" + sid, "N13_POS", text, "PASS", T, "逐字：" + src)
    for name, rel, expect in [
        ("TV2", "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md", "CATCH"),
        ("TV3", "lead/gate_fp7_20261108/_g7_tv3_double_negation.md", "CATCH"),
    ]:
        add("R10-" + name, "R10_TV", (ROOT / rel).read_text(encoding="utf-8"),
            expect, BAD_BAN, "逐字读盘 " + rel)
    for rel in [
        "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
        "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
        "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
        "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
    ]:
        add("R10-REAL-" + pathlib.Path(rel).stem, "R10_REAL",
            (ROOT / rel).read_text(encoding="utf-8"), "PASS", BAD_BAN,
            "逐字读盘 " + rel + "（g7 S1：R10 problems=0）")
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
    for cid, rel, toks, expect in [
        ("REAL-SLOT", "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", T_C07_SLOT, "PASS"),
        ("REAL-TRUTH", "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", T_C07_TRUTH, "PASS"),
        ("REAL-BOUND", "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", T, "PASS"),
    ]:
        add(cid, "REAL3", (ROOT / rel).read_text(encoding="utf-8"), expect, toks,
            "逐字读盘 " + rel)
    for cid, text, expect, note in [
        ("GP-C01", "grep 结果：已生效，可应用母本", "CATCH", "F03"),
        ("GP-C02", "不宣告 X 已生效，但 Y 已入账", "CATCH", "同句混用"),
        ("GP-C04", "并非不宣告已生效", "CATCH", "R12 双重否定"),
        ("GP-C05", "未核 grep 结果：已入账 0 命中", "PASS", "前置否定标签"),
        ("GP-C06", "未核 grep 结果：已生效 0 命中", "PASS", "同上"),
        ("GP-C07", "未核：已入账 grep 结果 = 0 命中", "PASS", "同上"),
        ("GP-C08", "grep 结果：已入账", "CATCH", "裸完成词默认 FAIL"),
        ("GP-C09", "未验：本笔已入账", "CATCH", "N19"),
        ("GP-C10", "grep 结果：第 5 笔已入账", "CATCH", "N20"),
    ]:
        add(cid, "GP_CONFLICT", text, expect, T, note)
    for cid, text, note in [
        ("GP-A1", "亦非不宣告 N-4 正式绑定已生效", "分离型双重否定"),
        ("GP-A2", "本件登记闭合，母本即日起适用", "同义完成断言"),
        ("GP-A3", "三值填毕，见证已由编排方签字", "C07 域同义完成断言"),
    ]:
        add(cid, "GP_ALLPASS_TRUE_ASSERTION", text, "CATCH", T, note)
    return C


def v12_judge(text, v12, toks):
    """Return (CATCH/PASS, details of V2 spans)."""
    hits = []
    for tok in sorted(set(list(v12.V2_OVERRIDE) + list(toks)), key=len, reverse=True):
        for m in re.finditer(re.escape(tok), text):
            c = v12.classify_v12(text, m.start(), m.end(), tok)
            hits.append({"token": tok, "pos": m.start(), "verdict": c["verdict"],
                         "hard": c["hard"], "weak": c["weak"],
                         "override": c["override"], "review_flag": c["review_flag"],
                         "reason": c["reason"], "unit": c["unit"][:120]})
    v2 = [h for h in hits if h["verdict"] == "V2"]
    return ("CATCH" if v2 else "PASS"), hits, v2


def score(rows, key):
    ok = sum(1 for r in rows if r["expect"] == r[key])
    fp = sum(1 for r in rows if r["expect"] == "PASS" and r[key] == "CATCH")
    fn = sum(1 for r in rows if r["expect"] == "CATCH" and r[key] == "PASS")
    return {"correct": ok, "n": len(rows), "acc": ok / len(rows), "fp": fp, "fn": fn}


def main():
    p13 = n13_path()
    n13 = load(p13, "_ei_v12_n13", (N13_SHA, N13_N))
    g7 = load(G7_PATH, "_ei_v12_g7",
              ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743))
    v12 = load(V12_PATH, "_ei_v12_rule",
               ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148))
    reg = load(ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py", "_ei_v12_n13reg")
    C = build_corpus(n13, reg)
    O = json.loads(REG_OUT.read_text(encoding="utf-8"))
    ref = {r["id"]: r for r in O["rows"]}
    assert len(C) == 74 and set(r["id"] for r in C) == set(ref), "corpus rebuild mismatch"

    rows = []
    for it in C:
        text = it["text"]
        v, hits, v2 = v12_judge(text, v12, list(n13.DEFAULT_TOKENS))
        r = dict(it)
        r.pop("text")
        r["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        r["text_head"] = text[:70].replace("\n", "\\n")
        r["v12"] = v
        r["v12_hits_n"] = len(hits)
        r["v12_V2_n"] = len(v2)
        r["v12_V2_tokens"] = sorted({h["token"] for h in v2})
        r["v12_review_flags"] = sum(1 for h in v2 if h["review_flag"])
        r["r10"], r["r12"], r["n13"], r["chain"] = (
            ref[it["id"]][k] for k in ("r10", "r12", "n13", "chain"))
        r["fourth_layer_OR"] = "CATCH" if any(r[k] == "CATCH" for k in ("r10", "r12", "n13", "v12")) else "PASS"
        rows.append(r)

    A = [r for r in rows if r["id"].startswith("GP-A")]
    res = {
        "corpus_n": len(rows),
        "rebuild_ids_match_regression_json": True,
        "v12_harness": "identical token set to lead/chain_vs_single_20261109/_cs_holdout.py:65-72",
        "a_GP_A1_A2_A3": [{
            "id": r["id"], "expect": r["expect"],
            "three_layer": [r["r10"], r["r12"], r["n13"]], "chain": r["chain"],
            "v12": r["v12"], "v12_V2_tokens": r["v12_V2_tokens"],
            "v12_review_flags": r["v12_review_flags"], "text": r["text_head"]} for r in A],
        "a_rescued": sum(1 for r in A if r["v12"] == "CATCH"),
        "b_v12_alone_74": score(rows, "v12"),
        "b_chain_74": score(rows, "chain"),
        "b_n13_74": score(rows, "n13"),
        "b_v12_fp_ids": [r["id"] for r in rows if r["expect"] == "PASS" and r["v12"] == "CATCH"],
        "b_v12_fn_ids": [r["id"] for r in rows if r["expect"] == "CATCH" and r["v12"] == "PASS"],
        "b_v12_by_family": {f: score([r for r in rows if r["family"] == f], "v12")
                            for f in sorted({r["family"] for r in rows})},
        "c_fourth_layer_OR": score(rows, "fourth_layer_OR"),
        "c_fourth_layer_OR_fp_ids": [r["id"] for r in rows
                                     if r["expect"] == "PASS" and r["fourth_layer_OR"] == "CATCH"],
        "c_fourth_layer_OR_fn_ids": [r["id"] for r in rows
                                     if r["expect"] == "CATCH" and r["fourth_layer_OR"] == "PASS"],
        "rows": rows,
    }
    # net benefit of adding V12 to chain (OR / catch union)
    base = res["b_chain_74"]
    comb = res["c_fourth_layer_OR"]
    res["c_net_benefit"] = {
        "base_chain_correct": base["correct"], "combined_correct": comb["correct"],
        "delta_correct": comb["correct"] - base["correct"],
        "rescued_fn": [r["id"] for r in A if r["chain"] == "PASS" and r["v12"] == "CATCH"],
        "new_fp": [r["id"] for r in rows if r["chain"] == "PASS" and r["v12"] == "CATCH"
                   and r["expect"] == "PASS"],
        "new_fp_count": len([r["id"] for r in rows
                            if r["chain"] == "PASS" and r["v12"] == "CATCH" and r["expect"] == "PASS"]),
        "net_delta_errors": (comb["fp"] + comb["fn"]) - (base["fp"] + base["fn"]),
        "net_delta_correct": comb["correct"] - base["correct"],
    }
    (W / "_ei_04_v12_layer_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    print("written: _ei_04_v12_layer_out.json")


if __name__ == "__main__":
    main()
