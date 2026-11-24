# -*- coding: utf-8 -*-
"""_csv_recompute.py — 独立复核员：从两份只读回归 JSON 自己重算逐层成绩表。

不采信被核回件的任何数字；不采信 JSON 自带 single_layer_vs_chain 摘要
（只把它作为「被核对项」打印）。不导入任何只读模块，不跑真机，不写只读件。
"""
import json
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "chain_vs_single_20261109"
CUR = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json"
V1 = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_v1_union_out.json"
LAYERS = ("naive", "r10", "r12", "n13", "chain")


def sha(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def recompute(rows):
    out = {}
    for L in LAYERS:
        ok = fp = fn = 0
        cc = cp = pc = pp = 0
        for r in rows:
            e = r["expect"]
            v = r[L]
            if v not in ("PASS", "CATCH"):
                raise ValueError("bad verdict %r in %s" % (v, r["id"]))
            if e == "CATCH" and v == "CATCH":
                cc += 1; ok += 1
            elif e == "CATCH" and v == "PASS":
                cp += 1; fn += 1
            elif e == "PASS" and v == "CATCH":
                pc += 1; fp += 1
            elif e == "PASS" and v == "PASS":
                pp += 1; ok += 1
            else:
                raise ValueError("bad expect %r" % e)
        out[L] = dict(ok=ok, fp=fp, fn=fn, n=len(rows),
                      cc=cc, cp=cp, pc=pc, pp=pp)
    return out


def main():
    print("=== [A] 九件编排方指纹 + 被核对象（本会话 hashlib 实算） ===")
    TARGETS = [
        ("lead/gate_pipeline_20261109/_gp_regression_out.json", "d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
        ("lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json", "68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358", 37461),
        ("lead/gate_pipeline_20261109/_gp_pipeline.py", "25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
        ("lead/gate_pipeline_20261109/_gp_DESIGN.md", "412e816fb0ad75618c91ac40806f11cd2919195f2eba5300c469862a65f840bc", 39058),
        ("lead/gate_n13_20261109/_n13_predicates.py", "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
        ("lead/gate_v1v2_20261109/_v12_rule.py", "15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
        ("lead/gate_fp7_20261108/_g7_predicates.py", "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
        ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
        ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
        ("lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md", "3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2", 49850),
    ]
    for rel, expect, ebytes in TARGETS:
        p = ROOT / rel
        h, n = sha(p)
        status = "MATCH" if (h == expect and n == ebytes) else "*** MISMATCH ***"
        print("%s %s bytes=%d (expect %d) %s" % (h, rel, n, ebytes, status))
        if status != "MATCH":
            print("   got  sha=%s" % h)
            print("   want sha=%s" % expect)

    print("\n=== [B] 独立重算：当前版 74 条 ===")
    dcur = json.loads(CUR.read_text(encoding="utf-8"))
    rows = dcur["rows"]
    print("corpus_n(JSON)=%d rows_len=%d" % (dcur["corpus_n"], len(rows)))
    c = recompute(rows)
    for L in LAYERS:
        x = c[L]
        print("%-6s ok=%2d fp=%2d fn=%2d n=%2d | CATCH->CATCH=%2d CATCH->PASS=%2d PASS->CATCH=%2d PASS->PASS=%2d"
              % (L, x["ok"], x["fp"], x["fn"], x["n"], x["cc"], x["cp"], x["pc"], x["pp"]))
    print("--- 与 JSON 自带 single_layer_vs_chain 摘要逐项核对 ---")
    for L in LAYERS:
        s = dcur["single_layer_vs_chain"][L]
        same = all(c[L][k] == s[k] for k in ("ok", "fp", "fn"))
        print("%-6s %s json=%s" % (L, "MATCH" if same else "*** MISMATCH ***", s))

    print("\n=== [C] 独立重算：v1 并集版 72 条 ===")
    dv1 = json.loads(V1.read_text(encoding="utf-8"))
    v = recompute(dv1["rows"])
    print("corpus_n(JSON)=%d rows_len=%d unresolved_total=%s"
          % (dv1["corpus_n"], len(dv1["rows"]), dv1["chain_unresolved_total"]))
    for L in LAYERS:
        x = v[L]
        print("%-6s ok=%2d fp=%2d fn=%2d n=%2d | %2d / %2d / %2d / %2d"
              % (L, x["ok"], x["fp"], x["fn"], x["n"], x["cc"], x["cp"], x["pc"], x["pp"]))
    print("--- 与 JSON 自带摘要逐项核对 ---")
    for L in LAYERS:
        s = dv1["single_layer_vs_chain"][L]
        same = all(v[L][k] == s[k] for k in ("ok", "fp", "fn"))
        print("%-6s %s json=%s" % (L, "MATCH" if same else "*** MISMATCH ***", s))

    print("\n=== [D] 配对差异（chain vs n13）/ 精确二项双侧检验 ===")
    from math import comb
    b = sum(1 for r in rows if r["chain"] != r["expect"] and r["n13"] == r["expect"])
    cc = sum(1 for r in rows if r["chain"] == r["expect"] and r["n13"] != r["expect"])
    n = b + cc
    p = min(1.0, sum(comb(n, k) for k in range(0, min(b, cc) + 1)) / (2 ** n) * 2)
    print("b(chain错 n13对)=%d c(chain对 n13错)=%d n=%d exact_binomial_two_sided_p=%.4f" % (b, cc, n, p))
    print("chain 全部失败 id:", [r["id"] for r in rows if r["chain"] != r["expect"]])
    print("n13  全部失败 id:", [r["id"] for r in rows if r["n13"] != r["expect"]])
    print("不计入差距的两者同错 id:", [r["id"] for r in rows if r["chain"] != r["expect"] and r["n13"] != r["expect"]])

    print("\n=== [E] 失败样本逐条（含 expect/各层/tokens/family） ===")
    for r in rows:
        if r["chain"] != r["expect"] or r["n13"] != r["expect"]:
            print(json.dumps({k: r[k] for k in ("id", "family", "expect", "tokens", "text_head", "naive", "r10", "r12", "n13", "chain")}, ensure_ascii=False))

    print("\n=== [F] 74 行 tokens 词表分布 / N13 自家 42 条子集 ===")
    from collections import Counter
    dist = Counter(tuple(r["tokens"]) for r in rows)
    for t, k in dist.most_common():
        label = "N13三词" if t == ("已入账", "已追加", "已生效") else ("BAD_BAN五词" if len(t) == 5 else "C07/其它")
        print("  %2d 行 %-12s %s" % (k, label, list(t)))
    n13own = [r for r in rows if r["family"] in ("N13_NEG", "N13_POS")]
    print("N13 自家 42 条 =", len(n13own))
    for L in ("n13", "chain"):
        ok = sum(1 for r in n13own if r[L] == r["expect"])
        fp = sum(1 for r in n13own if r["expect"] == "PASS" and r[L] == "CATCH")
        fn = sum(1 for r in n13own if r["expect"] == "CATCH" and r[L] == "PASS")
        print("  %-6s ok=%d/%d fp=%d fn=%d" % (L, ok, len(n13own), fp, fn))
    real3 = [r for r in rows if r["family"] == "REAL3"]
    print("REAL3 组:", [(r["id"], r["expect"], r["n13"], r["chain"], r["tokens"]) for r in real3])

    print("\n=== [G] 74 vs 72 逐 id / expect / chain 差异 ===")
    a = {r["id"]: r for r in rows}
    z = {r["id"]: r for r in dv1["rows"]}
    print("only74:", sorted(set(a) - set(z)))
    print("only72:", sorted(set(z) - set(a)))
    print("expect 翻转:", [(i, z[i]["expect"], a[i]["expect"]) for i in sorted(set(a) & set(z)) if z[i]["expect"] != a[i]["expect"]])
    print("chain 翻转:", [(i, z[i]["chain"], a[i]["chain"]) for i in sorted(set(a) & set(z)) if z[i]["chain"] != a[i]["chain"]])

    print("\n=== [H] 分族正确数 ===")
    fams = sorted({r["family"] for r in rows})
    for f in fams:
        sub = [r for r in rows if r["family"] == f]
        print("  %-26s n=%2d  " % (f, len(sub)) + "  ".join("%s=%d" % (L, sum(1 for r in sub if r[L] == r["expect"])) for L in LAYERS))


if __name__ == "__main__":
    main()
