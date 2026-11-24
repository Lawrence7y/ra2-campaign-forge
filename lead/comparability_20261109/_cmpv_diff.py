# -*- coding: utf-8 -*-
"""_cmpv_diff.py — 独立复核员自行实现的两版 JSON 逐条比对（不复用被核脚本）。
只读两个固定绝对常量路径 + 一个 manifest；只写唯一写域固定文件 _cmpv_diff_out.json。
Python: python -I -X utf8 <abs _cmpv_diff.py>
"""
import hashlib
import json
import math
import pathlib

P72 = pathlib.Path("D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json")
P74 = pathlib.Path("D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_regression_out.json")
OUT = pathlib.Path("D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpv_diff_out.json")

JUDGE_COLS = ("naive", "r10", "r12", "n13", "chain", "layer_conflicts", "layer_unresolved")
SINGLE = ("naive", "r10", "r12", "n13")


def rd(p):
    b = p.read_bytes()
    return json.loads(b.decode("utf-8")), hashlib.sha256(b).hexdigest(), len(b)


def binom2(b, c):
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(max(b, c), n + 1)) * (0.5 ** n)
    return min(1.0, 2.0 * tail)


def main():
    A, ha, na = rd(P72)   # 72 版 = 朴素并集
    B, hb, nb = rd(P74)   # 74 版 = 逐 span
    ra = {r["id"]: r for r in A["rows"]}
    rb = {r["id"]: r for r in B["rows"]}
    ia, ib = set(ra), set(rb)
    common = sorted(ia & ib)
    only_a, only_b = sorted(ia - ib), sorted(ib - ia)
    res = {}

    res["inputs"] = {
        "v1_72": {"sha256": ha, "bytes": na, "corpus_n": A.get("corpus_n"), "len_rows": len(A["rows"])},
        "v2_74": {"sha256": hb, "bytes": nb, "corpus_n": B.get("corpus_n"), "len_rows": len(B["rows"])},
    }

    # ---- ② 逐条比对：三个核心数字 ----
    expect_changes = [(i, ra[i]["expect"], rb[i]["expect"], ra[i]["text_head"])
                      for i in common if ra[i]["expect"] != rb[i]["expect"]]
    text_changes = [i for i in common if ra[i]["text_head"] != rb[i]["text_head"]]
    toks_changes = [i for i in common if ra[i]["tokens"] != rb[i]["tokens"]]
    fam_changes = [(i, ra[i]["family"], rb[i]["family"])
                   for i in common if ra[i]["family"] != rb[i]["family"]]
    note_changes = [(i, ra[i].get("note"), rb[i].get("note"))
                    for i in common if ra[i].get("note") != rb[i].get("note")]
    res["id_diff"] = {"n_a_72": len(ia), "n_b_74": len(ib),
                      "ids_only_72": only_a, "ids_only_74": only_b, "n_common": len(common)}
    res["expect_changes"] = {"n": len(expect_changes), "rows": expect_changes}
    res["text_head_changes_on_common"] = {"n": len(text_changes), "rows": text_changes}
    res["tokens_changes_on_common"] = {"n": len(toks_changes), "rows": toks_changes}
    res["family_changes_on_common"] = {"n": len(fam_changes), "rows": fam_changes}
    res["note_changes_on_common"] = {"n": len(note_changes), "rows": note_changes}

    # 判定列逐行变化
    colchg = {}
    for c in JUDGE_COLS:
        ch = [(i, ra[i][c], rb[i][c]) for i in common if ra[i][c] != rb[i][c]]
        colchg[c] = {"n": len(ch), "rows": ch[:30]}
    res["judgement_col_changes_on_common"] = colchg

    # 文本键对齐（换 id 不换题）
    head_a = {i: ra[i]["text_head"] for i in only_a}
    head_b = {i: rb[i]["text_head"] for i in only_b}
    ta = {r["text_head"] for r in A["rows"]}
    tb = {r["text_head"] for r in B["rows"]}
    res["text_key_align"] = {
        "unique_texts_72": len(ta), "unique_texts_74": len(tb),
        "shared_texts": len(ta & tb),
        "texts_only_72": sorted(ta - tb), "texts_only_74": sorted(tb - ta),
        "rename_pairs": [(x, y) for x in only_a for y in only_b if head_a[x] == head_b[y]],
        "GP_C03_text_eq_GP_A1_text": (
            ra["GP-C03"]["text_head"] == rb["GP-A1"]["text_head"]
            if "GP-C03" in ra and "GP-A1" in rb else None),
        "GP_C03_all_judgement_cols_eq_GP_A1": (
            all(ra["GP-C03"][c] == rb["GP-A1"][c] for c in JUDGE_COLS)
            if "GP-C03" in ra and "GP-A1" in rb else None),
    }

    # 声明值 vs rows 重算 / 类别先验 / 顶层字段逐项
    def recompute(d, ids=None):
        rows = d["rows"] if ids is None else [r for r in d["rows"] if r["id"] in set(ids)]
        st = {}
        for m in SINGLE + ("chain",):
            ok = fp = fn = 0
            for r in rows:
                if r[m] == r["expect"]:
                    ok += 1
                elif r["expect"] == "PASS":
                    fp += 1
                else:
                    fn += 1
            st[m] = {"ok": ok, "fp": fp, "fn": fn}
        return st

    res["declared_vs_recomputed"] = {
        "v1_72": {"declared": A["single_layer_vs_chain"], "recomputed": recompute(A),
                  "match": A["single_layer_vs_chain"] == recompute(A)},
        "v2_74": {"declared": B["single_layer_vs_chain"], "recomputed": recompute(B),
                  "match": B["single_layer_vs_chain"] == recompute(B)},
    }
    res["class_balance"] = {
        "v1_72": {"CATCH": sum(1 for r in A["rows"] if r["expect"] == "CATCH"),
                  "PASS": sum(1 for r in A["rows"] if r["expect"] == "PASS")},
        "v2_74": {"CATCH": sum(1 for r in B["rows"] if r["expect"] == "CATCH"),
                  "PASS": sum(1 for r in B["rows"] if r["expect"] == "PASS")},
    }
    res["toplevel_field_equality"] = {}
    for k in ("sources", "not_in_corpus"):
        res["toplevel_field_equality"][k] = {"identical": A.get(k) == B.get(k)}
    res["toplevel_field_equality"]["by_family"] = {
        "n_families_72": len(A["by_family"]), "n_families_74": len(B["by_family"]),
        "families_only_74": sorted(set(B["by_family"]) - set(A["by_family"])),
        "sources_has_new_family": any(
            f in A.get("sources", {}) for f in set(B["by_family"]) - set(A["by_family"])),
    }
    res["conflicts_unresolved"] = {
        "v1_72": {"declared_conflicts": A["chain_conflicts_total"],
                  "declared_unresolved": A["chain_unresolved_total"],
                  "sum_layer_conflicts": sum(r["layer_conflicts"] for r in A["rows"]),
                  "sum_layer_unresolved": sum(r["layer_unresolved"] for r in A["rows"])},
        "v2_74": {"declared_conflicts": B["chain_conflicts_total"],
                  "declared_unresolved": B["chain_unresolved_total"],
                  "sum_layer_conflicts": sum(r["layer_conflicts"] for r in B["rows"]),
                  "sum_layer_unresolved": sum(r["layer_unresolved"] for r in B["rows"])},
    }

    # ---- ③ 到底变了几样：把所有可辨识的变更面逐项列出 ----
    changed_faces = []
    def face(name, truth, evidence):
        if truth:
            changed_faces.append({"face": name, "evidence": evidence})
    face("S 样本集(id/分母/文本键)", bool(only_a or only_b), "n 72->74, only72=%s only74=%s" % (only_a, only_b))
    face("G 真值 expect", bool(expect_changes), "%d 条 %s" % (len(expect_changes), [x[0] for x in expect_changes]))
    face("G' 标注判读本体 note", bool(note_changes), "%d 条 %s" % (len(note_changes), [x[0] for x in note_changes]))
    face("S' 族分类法 family/by_family", bool(fam_changes) or set(A["by_family"]) != set(B["by_family"]),
         "族数 %d->%d" % (len(A["by_family"]), len(B["by_family"])))
    face("I 被测实现 chain 判定", colchg["chain"]["n"] > 0, "%d 行 chain 变" % colchg["chain"]["n"])
    face("E 评测脚本(72 版未留盘)", True, "仅 74 版 _gp_regression.py 在盘；72 版生成器无")
    face("M 度量/class_balance/分母", res["class_balance"]["v1_72"] != res["class_balance"]["v2_74"],
         "%s -> %s" % (res["class_balance"]["v1_72"], res["class_balance"]["v2_74"]))
    face("U 未消解冲突语义", A["chain_unresolved_total"] != B["chain_unresolved_total"],
         "unresolved %d->%d 而 conflicts %d->%d" % (A["chain_unresolved_total"], B["chain_unresolved_total"],
                                                     A["chain_conflicts_total"], B["chain_conflicts_total"]))
    face("R 来源登记 sources 未随新族更新",
         not res["toplevel_field_equality"]["sources"]["identical"] is False and
         bool(set(B["by_family"]) - set(A["by_family"])) and
         not any(f in A.get("sources", {}) for f in set(B["by_family"]) - set(A["by_family"])),
         "sources 两版逐字相同但 74 版多一族")
    res["changed_faces"] = {"n": len(changed_faces), "faces": changed_faces}
    unchanged = {
        "text_head_on_common": len(text_changes) == 0,
        "tokens_on_common": len(toks_changes) == 0,
        "family_on_common": len(fam_changes) == 0,
        "single_layer_4cols_on_common": all(
            all(ra[i][m] == rb[i][m] for m in SINGLE) for i in common),
        "layer_conflicts_on_common": all(
            ra[i]["layer_conflicts"] == rb[i]["layer_conflicts"] for i in common),
        "sources_identical": A.get("sources") == B.get("sources"),
        "not_in_corpus_identical": A.get("not_in_corpus") == B.get("not_in_corpus"),
        "scoring_formula": "ok=(got==expect); fp=(expect=PASS,got=CATCH); fn=(expect=CATCH,got=PASS)",
    }
    res["unchanged"] = unchanged

    # ---- 21 分分解 ----
    ok72 = A["single_layer_vs_chain"]["chain"]["ok"]
    ok74 = B["single_layer_vs_chain"]["chain"]["ok"]
    def chain_ok(d, ids):
        s = set(ids)
        return sum(1 for r in d["rows"] if r["id"] in s and r["chain"] == r["expect"])
    flipped = [x[0] for x in expect_changes]
    strict = [i for i in common if ra[i]["expect"] == rb[i]["expect"]
              and ra[i]["text_head"] == rb[i]["text_head"]
              and ra[i]["tokens"] == rb[i]["tokens"]]
    parts = {
        "frozen68": chain_ok(B, strict) - chain_ok(A, strict),
        "flipped3": sum(1 for i in flipped if rb[i]["chain"] == rb[i]["expect"])
                    - sum(1 for i in flipped if ra[i]["chain"] == ra[i]["expect"]),
        "new3_74": sum(1 for i in only_b if rb[i]["chain"] == rb[i]["expect"]),
        "deleted1_72": -sum(1 for i in only_a if ra[i]["chain"] == ra[i]["expect"]),
    }
    res["delta21"] = {
        "v1_72_chain_ok": ok72, "n72": len(A["rows"]), "rate72": ok72 / len(A["rows"]),
        "v2_74_chain_ok": ok74, "n74": len(B["rows"]), "rate74": ok74 / len(B["rows"]),
        "raw_delta": ok74 - ok72, "pp_delta": (ok74 / len(B["rows"]) - ok72 / len(A["rows"])) * 100,
        "parts": parts, "parts_sum": sum(parts.values()),
        "flipped_rows_model_output_identical": all(
            all(ra[i][c] == rb[i][c] for c in JUDGE_COLS) for i in flipped),
    }

    # ---- ⑤ 68 条冻结子集反推 ----
    v1 = chain_ok(A, strict)
    v2 = chain_ok(B, strict)
    b = sum(1 for i in strict if ra[i]["chain"] != ra[i]["expect"] and rb[i]["chain"] == rb[i]["expect"])
    c = sum(1 for i in strict if ra[i]["chain"] == ra[i]["expect"] and rb[i]["chain"] != rb[i]["expect"])
    strat = {}
    for ex in ("CATCH", "PASS"):
        sub = [i for i in strict if ra[i]["expect"] == ex]
        strat[ex] = {"n": len(sub),
                     "v1": {m: sum(1 for i in sub if ra[i][m] == ra[i]["expect"]) for m in SINGLE + ("chain",)},
                     "v2": {m: sum(1 for i in sub if rb[i][m] == rb[i]["expect"]) for m in SINGLE + ("chain",)}}
    flipped_chain = [i for i in strict if ra[i]["chain"] != rb[i]["chain"]]
    res["frozen68"] = {
        "n": len(strict), "v1_chain_ok": v1, "v2_chain_ok": v2,
        "chain_changed_ids": flipped_chain, "n_chain_changed": len(flipped_chain),
        "paired": {"b": b, "c": c, "p_2sided_exact_binomial": binom2(b, c)},
        "stratified": strat,
        "single_layer_4cols_identical": all(all(ra[i][m] == rb[i][m] for m in SINGLE) for i in strict),
        "all_flipped_expect_PASS": all(rb[i]["expect"] == "PASS" for i in flipped_chain),
        "all_flipped_CATCH_to_PASS": all(ra[i]["chain"] == "CATCH" and rb[i]["chain"] == "PASS"
                                         for i in flipped_chain),
        "all_flipped_v1_unresolved_gt0": all(ra[i]["layer_unresolved"] > 0 for i in flipped_chain),
        "v1_unresolved_sum_on_flipped": sum(ra[i]["layer_unresolved"] for i in flipped_chain),
        "unresolved_changed_rows": [i for i in common if ra[i]["layer_unresolved"] != rb[i]["layer_unresolved"]],
        "flipped_eq_unresolved_changed": set(flipped_chain) == set(
            i for i in common if ra[i]["layer_unresolved"] != rb[i]["layer_unresolved"]),
    }

    # ---- 显著性三项（74 内 / 72 内 / 68 子集内 v2） ----
    def paired_cols(d, ids, x, y):
        s = set(ids)
        rr = {r["id"]: r for r in d["rows"]}
        bb = sum(1 for i in s if rr[i][x] == rr[i]["expect"] and rr[i][y] != rr[i]["expect"])
        cc = sum(1 for i in s if rr[i][x] != rr[i]["expect"] and rr[i][y] == rr[i]["expect"])
        return {"x": x, "y": y, "b(x对y错)": bb, "c(x错y对)": cc,
                "p_2sided": binom2(bb, cc)}
    res["significance"] = {
        "v2_74_all74_chain_vs_n13": paired_cols(B, list(ib), "chain", "n13"),
        "v1_72_all72_chain_vs_n13": paired_cols(A, list(ia), "chain", "n13"),
        "frozen68_v2_chain_vs_n13": paired_cols(B, strict, "chain", "n13"),
        "frozen68_v1_chain_vs_n13": paired_cols(A, strict, "chain", "n13"),
    }

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({
        "inputs": res["inputs"],
        "id_diff": res["id_diff"],
        "n_expect_changes": res["expect_changes"]["n"],
        "expect_rows": [(x[0], x[1], x[2]) for x in expect_changes],
        "n_text_head_changes": res["text_head_changes_on_common"]["n"],
        "n_tokens_changes": res["tokens_changes_on_common"]["n"],
        "n_family_changes": res["family_changes_on_common"]["n"],
        "n_note_changes": res["note_changes_on_common"]["n"],
        "note_ids": [x[0] for x in note_changes],
        "judgement_col_changes": {k: v["n"] for k, v in colchg.items()},
        "text_key_align": res["text_key_align"],
        "declared_match": {k: v["match"] for k, v in res["declared_vs_recomputed"].items()},
        "class_balance": res["class_balance"],
        "toplevel": res["toplevel_field_equality"],
        "conflicts_unresolved": res["conflicts_unresolved"],
        "changed_faces_n": res["changed_faces"]["n"],
        "changed_faces": [f["face"] for f in changed_faces],
        "unchanged": unchanged,
        "delta21": res["delta21"],
        "frozen68": {k: v for k, v in res["frozen68"].items() if k not in ("chain_changed_ids", "unresolved_changed_rows")},
        "frozen68_flipped_eq_unresolved_changed": res["frozen68"]["flipped_eq_unresolved_changed"],
        "significance": res["significance"],
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
