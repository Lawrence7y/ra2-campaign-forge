# -*- coding: utf-8 -*-
# _cs_recompute.py : 独立从 rows 重算逐层 correct/fp/fn/n；混淆矩阵；链失败全清单；
#                    两份语料逐 id 对照；分组（N13 自家考题 / R10 考题 / 第三方）分层成绩
# 绝不采信 JSON 自带 single_layer_vs_chain 摘要，仅用它做交叉校验。
import os, json, collections
ROOT = r"D:\Project\ra2-campaign-forge"
os.chdir(ROOT)
CUR = "lead/gate_pipeline_20261109/_gp_regression_out.json"
UNI = "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json"
LAYERS = ["naive", "r10", "r12", "n13", "chain"]

def load(rel):
    with open(rel, "r", encoding="utf-8") as f:
        return json.load(f)

def stat(rows, layer):
    """expect CATCH=正类(应拦)，CATCH 判为预测正；fp=误拦(expect PASS 但判 CATCH)，fn=漏报(expect CATCH 但判 PASS)"""
    ok = fp = fn = 0
    cm = collections.Counter()
    for r in rows:
        e, p = r["expect"], r[layer]
        cm["%s->%s" % (e, p)] += 1
        if e == p:
            ok += 1
        elif e == "PASS" and p == "CATCH":
            fp += 1
        elif e == "CATCH" and p == "PASS":
            fn += 1
        else:
            raise ValueError("unexpected %r %r" % (e, p))
    return dict(correct=ok, fp=fp, fn=fn, n=len(rows), cm=dict(cm))

cur, uni = load(CUR), load(UNI)

for tag, o in [("CURRENT 74", cur), ("UNION 72", uni)]:
    rows = o["rows"]
    print("\n" + "=" * 110)
    print("%s  corpus_n=%s  len(rows)=%d  chain_conflicts_total=%s chain_unresolved_total=%s"
          % (tag, o["corpus_n"], len(rows), o["chain_conflicts_total"], o["chain_unresolved_total"]))
    print("=" * 110)
    print("\n--- (a) 逐层独立重算（从 rows 逐行 expect vs 各层） ---")
    print("%-8s %8s %6s %6s %6s %8s   %s" % ("layer", "correct", "fp", "fn", "n", "acc", "confusion (expect->pred)"))
    for L in LAYERS:
        s = stat(rows, L)
        print("%-8s %8d %6d %6d %6d %7.2f%%   %s"
              % (L, s["correct"], s["fp"], s["fn"], s["n"], 100.0 * s["correct"] / s["n"],
                 ", ".join("%s:%d" % (k, v) for k, v in sorted(s["cm"].items()))))
    print("\n--- 交叉校验：JSON 自带 single_layer_vs_chain（仅对比，不作为来源） ---")
    for L in LAYERS:
        s = stat(rows, L)
        j = o["single_layer_vs_chain"][L]
        print("  %-8s recompute=(ok=%d,fp=%d,fn=%d) json=(ok=%d,fp=%d,fn=%d) %s"
              % (L, s["correct"], s["fp"], s["fn"], j["ok"], j["fp"], j["fn"],
                 "MATCH" if (s["correct"], s["fp"], s["fn"]) == (j["ok"], j["fp"], j["fn"]) else "MISMATCH"))
    print("\n--- 合成链全部失败行（expect != chain） ---")
    for r in rows:
        if r["expect"] != r["chain"]:
            print("  %-34s fam=%-28s expect=%-5s chain=%-5s | naive=%-5s r10=%-5s r12=%-5s n13=%-5s | %s"
                  % (r["id"], r["family"], r["expect"], r["chain"],
                     r["naive"], r["r10"], r["r12"], r["n13"], r["text_head"][:60]))
    print("\n--- N13 单层全部失败行 ---")
    for r in rows:
        if r["expect"] != r["n13"]:
            print("  %-34s fam=%-28s expect=%-5s n13=%-5s chain=%-5s | %s"
                  % (r["id"], r["family"], r["expect"], r["n13"], r["chain"], r["text_head"][:60]))

# ---- 分层（分组）成绩：为公平性分析提供数据 ----
print("\n" + "=" * 110)
print("分层成绩：把 74 条按来源切成三组，看 N13 与 chain 的差距出现在哪一组")
print("=" * 110)
GROUPS = {
    "N13自家考题(26负+16正)": {"N13_NEG", "N13_POS"},
    "R10考题(TV/REAL/CTX)": {"R10_TV", "R10_REAL", "R10_CTX"},
    "中性第三方(REAL3/GP)": {"REAL3", "GP_CONFLICT", "GP_ALLPASS_TRUE_ASSERTION"},
}
rows = cur["rows"]
for gname, fams in GROUPS.items():
    sub = [r for r in rows if r["family"] in fams]
    print("\n-- %s  n=%d  (family=%s)" % (gname, len(sub), ",".join(sorted(fams))))
    print("   %-8s %8s %5s %5s %6s" % ("layer", "correct", "fp", "fn", "n"))
    for L in LAYERS:
        s = stat(sub, L)
        print("   %-8s %8d %5d %5d %6d" % (L, s["correct"], s["fp"], s["fn"], s["n"]))
    # 每 family 的 chain vs n13
    for fam in sorted(fams):
        ss = [r for r in sub if r["family"] == fam]
        if not ss:
            continue
        a, b = stat(ss, "chain"), stat(ss, "n13")
        print("     %-28s n=%2d  chain=%2d/%2d  n13=%2d/%2d" % (fam, len(ss), a["correct"], len(ss), b["correct"], len(ss)))

# ---- (d) 74 vs 72 逐 id 差异 ----
print("\n" + "=" * 110)
print("(d) 74 条 vs 72 条：逐 id 差异")
print("=" * 110)
cmap = {r["id"]: r for r in cur["rows"]}
umap = {r["id"]: r for r in uni["rows"]}
only_cur = sorted(set(cmap) - set(umap))
only_uni = sorted(set(umap) - set(cmap))
print("  仅在 74 版（新增）: %s" % only_cur)
print("  仅在 72 版（删除）: %s" % only_uni)
print("  两版共有但字段变化:")
common = sorted(set(cmap) & set(umap))
diff_fields = ("family", "expect", "tokens", "note", "text_head", "naive", "r10", "r12", "n13", "chain", "layer_conflicts", "layer_unresolved")
nchg = 0
for k in common:
    d = [f for f in diff_fields if cmap[k].get(f) != umap[k].get(f)]
    if d:
        nchg += 1
        short = [f for f in d if f in ("expect", "chain", "n13", "r10", "r12", "naive", "family")]
        print("    %-12s changed=%s  关键字段: %s" % (k, d, {f: (umap[k].get(f), cmap[k].get(f)) for f in short}))
print("  共有 id 数=%d，其中有字段变化=%d" % (len(common), nchg))
print("\n  family 计数对照:")
ca, ua = collections.Counter(r["family"] for r in cur["rows"]), collections.Counter(r["family"] for r in uni["rows"])
for f in sorted(set(ca) | set(ua)):
    print("    %-30s 74版=%2d  72版=%2d" % (f, ca[f], ua[f]))

# ---- (b)(c) 排名推演：只在各子集上重排名 ----
print("\n" + "=" * 110)
print("(c) 排名推演：换考题集后各层 correct 排名")
print("=" * 110)
SUBSETS = {
    "N13自家考题(42)": [r for r in rows if r["family"] in {"N13_NEG", "N13_POS"}],
    "R10考题(17)": [r for r in rows if r["family"] in {"R10_TV", "R10_REAL", "R10_CTX"}],
    "中性第三方(15)": [r for r in rows if r["family"] in {"REAL3", "GP_CONFLICT", "GP_ALLPASS_TRUE_ASSERTION"}],
    "仅真断言(应CATCH 39)": [r for r in rows if r["expect"] == "CATCH"],
    "仅应放行(应PASS 35)": [r for r in rows if r["expect"] == "PASS"],
    "全74": rows,
    "全72(union版)": uni["rows"],
}
for name, sub in SUBSETS.items():
    sc = [(L, stat(sub, L)["correct"]) for L in LAYERS]
    rank = sorted(sc, key=lambda x: -x[1])
    print("  %-24s n=%2d  ranking: %s" % (name, len(sub), " > ".join("%s=%d" % x for x in rank)))
