# -*- coding: utf-8 -*-
"""_eiv_01_corpus.py — 独立复核员：自重建 74 行语料 + 自跑三层/链/V1V2 全量实验。

独立性：不 import _gp_regression.py（它在模块级 :222 写只读域 JSON，无 __main__ 保护），
也不 import 撰写人的 _ei_* 脚本；语料从 _n13_regression.py 用 ast.literal_eval 抽取 +
按 _gp_regression.py:67-130 逐条转录重建，再与只读 JSON 的 (id,expect,text_head) 全量核对。
谓词模块按 hashlib 定位/校验后加载；判定口径逐行对齐 _gp_regression.py:133-150 与
_cs_holdout.py:65-72，但代码自己写。

运行: python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/evidence_indep_20261109/_eiv_01_corpus.py
零真机、零采样、只读源域；写只落本写域 _eiv_01_*。
"""
import ast
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
PIPEDIR = ROOT / "lead" / "gate_pipeline_20261109"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"

N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"
N13_N = 16649
G7_SHA = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
V12_SHA = "15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0"


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def literals_from(path, names):
    """从源文件用 ast.literal_eval 提取指定模块级赋值，完全不执行该文件。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    out[t.id] = ast.literal_eval(n.value)
    return out


def main():
    # ---- 按 hashlib 定位 N13 源（不采信任何文件名）----
    p13 = None
    for p in sorted(N13_DIR.iterdir()):
        if p.is_file() and fp(p) == (N13_SHA, N13_N):
            p13 = p
            break
    assert p13 is not None, "N13 源按 hashlib 未定位"
    g7p = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
    v12p = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
    assert fp(g7p) == (G7_SHA, 11743)
    assert fp(v12p) == (V12_SHA, 9148)

    g7 = load(g7p, "_eiv_g7")
    v12 = load(v12p, "_eiv_v12")
    n13 = load(p13, "_eiv_n13")
    sys.path.insert(0, str(PIPEDIR))
    import _gp_pipeline as P

    T = list(n13.DEFAULT_TOKENS)
    BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
    T_C07_SLOT = ["已补登", "已填入", "已填", "已代填"]
    T_C07_TRUTH = ["已填", "已代填", "已提交"]

    # ---- 重建语料（74 行）----
    reg_path = N13_DIR / "_n13_regression.py"
    lit = literals_from(reg_path, {"POSITIVES", "NEGATIVES"})
    POSITIVES, NEGATIVES = lit["POSITIVES"], lit["NEGATIVES"]
    CORPUS = []

    def add(cid, family, text, expect, tokens, note):
        CORPUS.append({"id": cid, "family": family, "text": text,
                       "expect": expect, "tokens": tokens, "note": note})

    for sid, text, note, src in NEGATIVES:
        add("N13-" + sid, "N13_NEG", text, "CATCH", T, "逐字：" + src + " | " + note)
    for sid, text, expect, src in POSITIVES:
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
            (ROOT / rel).read_text(encoding="utf-8"), "PASS", BAD_BAN, "逐字读盘 " + rel)
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
        ("GP-C01", "grep 结果：已生效，可应用母本", "CATCH", "F03 A 标记劫持真断言"),
        ("GP-C02", "不宣告 X 已生效，但 Y 已入账", "CATCH", "同句混用"),
        ("GP-C04", "并非不宣告已生效", "CATCH", "R12 双重否定"),
        ("GP-C05", "未核 grep 结果：已入账 0 命中", "PASS", "前置否定标签 + A 检索结果"),
        ("GP-C06", "未核 grep 结果：已生效 0 命中", "PASS", "同上（已生效）"),
        ("GP-C07", "未核：已入账 grep 结果 = 0 命中", "PASS", "标签在冒号前"),
        ("GP-C08", "grep 结果：已入账", "CATCH", "裸完成词拿不准默认 FAIL"),
        ("GP-C09", "未验：本笔已入账", "CATCH", "前置标签 + 主语"),
        ("GP-C10", "grep 结果：第 5 笔已入账", "CATCH", "A 标记 + 主语"),
    ]:
        add(cid, "GP_CONFLICT", text, expect, T, note)
    for cid, text, note in [
        ("GP-A1", "亦非不宣告 N-4 正式绑定已生效", "分离型双重否定=肯定"),
        ("GP-A2", "本件登记闭合，母本即日起适用", "词表外同义完成断言"),
        ("GP-A3", "三值填毕，见证已由编排方签字", "C07 域同义完成断言"),
    ]:
        add(cid, "GP_ALLPASS_TRUE_ASSERTION", text, "CATCH", T, note)

    # ---- 与只读 JSON 全量核对（id / expect / text_head / 数值层结论）----
    O = json.loads((PIPEDIR / "_gp_regression_out.json").read_text(encoding="utf-8"))
    ref = {r["id"]: r for r in O["rows"]}
    check = {"rebuilt_n": len(CORPUS), "json_n": len(O["rows"]),
             "ids_equal": set(r["id"] for r in CORPUS) == set(ref),
             "expect_mismatch": [], "head_mismatch": [], "layer_mismatch": []}

    def judge_one(it, mode):
        text, toks = it["text"], it["tokens"]
        if mode == "naive":
            return "CATCH" if any(t in text for t in toks) else "PASS"
        if mode == "r10":
            return "CATCH" if g7.r10_scan(text, toks)[0] else "PASS"
        if mode == "r12":
            return "CATCH" if g7.r12_scan(text, toks)[0] else "PASS"
        if mode == "n13":
            p, _ = n13.r13_assertions(text, T, r10_scan=g7.r10_scan,
                                      r12_scan=g7.r12_scan)
            return "CATCH" if p else "PASS"
        r = P.gate_check(text, toks, PIPEDIR, g7, n13, T)
        adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
        return "CATCH" if adj else "PASS"

    # ---- V1V2 判定口径：与 _cs_holdout.py:65-72 逐字对齐（自己实现）----
    def v12v(text):
        for tok in set(list(v12.V2_OVERRIDE) + T):
            for m in re.finditer(re.escape(tok), text):
                c = v12.classify_v12(text, m.start(), m.end(), tok)
                if c["verdict"] == "V2":
                    return "CATCH"
        return "PASS"

    def v12_detail(text):
        """逐 span 记录：是否 V2、是否硬 override、是否仅 DEFAULT(review_flag)。"""
        hits = []
        for tok in set(list(v12.V2_OVERRIDE) + T):
            for m in re.finditer(re.escape(tok), text):
                c = v12.classify_v12(text, m.start(), m.end(), tok)
                if c["verdict"] == "V2":
                    hits.append({"token": tok, "override": c["override"],
                                 "review": c["review_flag"], "hard": c["hard"],
                                 "reason": c["reason"][:70]})
        return {"catch": bool(hits),
                "hard_override": any(h["override"] for h in hits),
                "only_default": bool(hits) and all(h["review"] for h in hits),
                "hits": hits}

    rows = []
    for it in CORPUS:
        rid = it["id"]
        v = ref.get(rid)
        if v is None:
            continue
        head = it["text"][:90].replace("\n", "\\n")
        if v["expect"] != it["expect"]:
            check["expect_mismatch"].append(rid)
        if v["text_head"] != head:
            check["head_mismatch"].append((rid, head[:50], v["text_head"][:50]))
        got = {m: judge_one(it, m) for m in ("naive", "r10", "r12", "n13", "chain")}
        for m, val in got.items():
            if v[m] != val:
                check["layer_mismatch"].append((rid, m, v[m], val))
        d = v12_detail(it["text"])
        ext = P.extract_spans(it["text"], it["tokens"])
        rows.append({"id": rid, "expect": it["expect"], "family": it["family"],
                     "text_head": head, **got,
                     "base": v["chain"],
                     "spans": ext["count"],
                     "all_pass": all(v[k] == "PASS" for k in ("r10", "r12", "n13")),
                     "v12": "CATCH" if d["catch"] else "PASS",
                     "hard_override": d["hard_override"],
                     "only_default": d["only_default"],
                     "v12_hits": d["hits"]})

    check["all_match"] = (check["rebuilt_n"] == 74 and check["ids_equal"]
                          and not check["expect_mismatch"] and not check["head_mismatch"]
                          and not check["layer_mismatch"])

    # ---- ④ GP-A1/A2/A3 V1V2 是否 3/3 兜住 + 逐条明细 ----
    gpa = [r for r in rows if r["id"].startswith("GP-A")]
    gpa_out = {"n": len(gpa),
               "all_three_chain_PASS": all(r["base"] == "PASS" for r in gpa),
               "all_three_v12_CATCH": all(r["v12"] == "CATCH" for r in gpa),
               "all_three_layers_all_PASS": all(r["all_pass"] for r in gpa),
               "rows": [{k: r[k] for k in ("id", "expect", "base", "v12", "spans",
                                            "all_pass", "hard_override", "only_default",
                                            "v12_hits")} for r in gpa]}

    # ---- ⑤ V1V2 单层 74 行成绩（新误报量）----
    def score(pred_key):
        ok = sum(1 for r in rows if r["expect"] == r[pred_key])
        fp_ = sum(1 for r in rows if r["expect"] == "PASS" and r[pred_key] == "CATCH")
        fn_ = sum(1 for r in rows if r["expect"] == "CATCH" and r[pred_key] == "PASS")
        return {"correct": ok, "n": len(rows), "acc": ok / len(rows),
                "fp": fp_, "fn": fn_}

    v12_single = score("v12")
    v12_fp_ids = [r["id"] for r in rows if r["expect"] == "PASS" and r["v12"] == "CATCH"]
    v12_fn_ids = [r["id"] for r in rows if r["expect"] == "CATCH" and r["v12"] == "PASS"]
    v12_single["fp_ids"] = v12_fp_ids
    v12_single["fn_ids"] = v12_fn_ids

    # 20 条未见变体（从只读 _cs_holdout_out.json 取 expect/v12，不重跑其脚本）
    H = json.loads((ROOT / "lead" / "chain_vs_single_20261109" / "_cs_holdout_out.json")
                   .read_text(encoding="utf-8"))["unseen"]
    holdout = {"n": len(H),
               "v12_correct": sum(1 for r in H if r["expect"] == r["v12"]),
               "v12_fp": sum(1 for r in H if r["expect"] == "PASS" and r["v12"] == "CATCH"),
               "v12_fn": sum(1 for r in H if r["expect"] == "CATCH" and r["v12"] == "PASS"),
               "source": "lead/chain_vs_single_20261109/_cs_holdout_out.json (只读)"}

    # ---- 净收益：四种装配（自己实现，口径对齐 _ei_06_net.py:84-110）----
    def sc(finals):
        ok = sum(1 for r, f in zip(rows, finals) if r["expect"] == f)
        fp_ = sum(1 for r, f in zip(rows, finals) if r["expect"] == "PASS" and f == "CATCH")
        fn_ = sum(1 for r, f in zip(rows, finals) if r["expect"] == "CATCH" and f == "PASS")
        return {"correct": ok, "fp": fp_, "fn": fn_, "acc": ok / len(rows),
                "delta_correct": ok - 69, "delta_errors": (fp_ + fn_) - 5}

    variants = {
        "0_baseline_chain": [r["base"] for r in rows],
        "1_naive_OR_all4": ["CATCH" if r["base"] == "CATCH" or r["v12"] == "CATCH" else "PASS"
                            for r in rows],
        "2_monotone_spans0_or_allPASS": [
            "CATCH" if r["base"] == "CATCH" or
            ((r["spans"] == 0 or r["all_pass"]) and r["v12"] == "CATCH") else "PASS"
            for r in rows],
        "3_monotone_spans0_only": [
            "CATCH" if r["base"] == "CATCH" or (r["spans"] == 0 and r["v12"] == "CATCH")
            else "PASS" for r in rows],
        "4_monotone_spans0_hard_override": [
            "CATCH" if r["base"] == "CATCH" or
            (r["spans"] == 0 and r["v12"] == "CATCH" and r["hard_override"]) else "PASS"
            for r in rows],
        "5_monotone_allPASS_hard_override": [
            "CATCH" if r["base"] == "CATCH" or
            (r["all_pass"] and r["v12"] == "CATCH" and r["hard_override"]) else "PASS"
            for r in rows],
        "6_monotone_gated_hard_override": [
            "CATCH" if r["base"] == "CATCH" or
            ((r["spans"] == 0 or r["all_pass"]) and r["v12"] == "CATCH" and r["hard_override"])
            else "PASS" for r in rows],
    }
    net = {"n": len(rows),
           "spans0_ids": [r["id"] for r in rows if r["spans"] == 0],
           "all_pass_ids": [r["id"] for r in rows if r["all_pass"]],
           "variants": {}}
    for k, final in variants.items():
        s = sc(final)
        s["rescued_fn"] = [r["id"] for r, f in zip(rows, final)
                           if r["base"] == "PASS" and f == "CATCH" and r["expect"] == "CATCH"]
        s["new_fp"] = [r["id"] for r, f in zip(rows, final)
                       if r["base"] == "PASS" and f == "CATCH" and r["expect"] == "PASS"]
        net["variants"][k] = s

    out = {"n13_source": str(p13.relative_to(ROOT)).replace("\\", "/"),
           "corpus_check": check, "gp_a": gpa_out,
           "v12_single_74": v12_single, "holdout_20_v12": holdout,
           "net": net}
    (W / "_eiv_01_corpus_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 控制台摘要 ----
    print("== ① 74 行语料独立重建 ==")
    print("  rebuilt_n =", check["rebuilt_n"], "json_n =", check["json_n"],
          "ids_equal =", check["ids_equal"])
    print("  expect_mismatch =", len(check["expect_mismatch"]),
          "head_mismatch =", len(check["head_mismatch"]),
          "layer_mismatch =", len(check["layer_mismatch"]))
    print("  ALL_MATCH =", check["all_match"])
    if check["layer_mismatch"]:
        print("  层判定不一致样例 =", check["layer_mismatch"][:6])
    print("== ④ V1V2 兜 GP-A1/A2/A3 ==")
    print("  n =", gpa_out["n"], "chain全PASS =", gpa_out["all_three_chain_PASS"],
          "三层全PASS =", gpa_out["all_three_layers_all_PASS"],
          "V12全CATCH =", gpa_out["all_three_v12_CATCH"])
    for r in gpa_out["rows"]:
        print("   ", r["id"], "spans=", r["spans"], "v12=", r["v12"],
              "hard_override=", r["hard_override"], "only_default=", r["only_default"],
              "hits=", [(h["token"], h["override"][:22], h["review"]) for h in r["v12_hits"]])
    print("== ⑤ V1V2 单层 74 行 ==")
    print("  correct =", v12_single["correct"], "/", v12_single["n"],
          "acc =", round(v12_single["acc"] * 100, 2),
          "fp =", v12_single["fp"], "fn =", v12_single["fn"])
    print("  fp_ids =", v12_fp_ids)
    print("  fn_ids =", v12_fn_ids)
    print("  20 条未见变体 v12:", holdout)
    print("== 净收益 ==")
    for k, s in net["variants"].items():
        print("  %-38s correct=%d fp=%d fn=%d delta_correct=%+d rescued=%s new_fp=%s" %
              (k, s["correct"], s["fp"], s["fn"], s["delta_correct"],
               s["rescued_fn"], s["new_fp"]))
    print("  spans0_ids =", net["spans0_ids"], " all_pass_n =", len(net["all_pass_ids"]))
    print("written: _eiv_01_corpus_out.json")


if __name__ == "__main__":
    main()
