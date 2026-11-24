# -*- coding: utf-8 -*-
"""_ecw_summarize.py — 从 _ec_s4_results.json / _ec_s3_results.json 取逐件证据（只读）。"""
import json, collections, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

with open(os.path.join(HERE, "_ec_s4_results.json"), encoding="utf-8") as f:
    S4 = json.load(f)

print("== s4 顶层 ==")
print("n_no_exit =", S4["n_no_exit"], "| cls_counts =", S4["cls_counts"],
      "| verdict_counts =", S4["verdict_counts"], "| exit_disagree =", S4["exit_disagree"])

res = S4["results"]
by = collections.defaultdict(list)
for r in res:
    by[r["class"]].append(r)

print("\n== GATE 21 件逐件（reasons 首条 + E 码）==")
for r in by["GATE"]:
    codes = sorted({x[0] for x in r["reasons"]})
    first = r["reasons"][0]
    print("%s | %s | %s | %s" % (r["verdict"], r["rel"], ",".join(codes), str(first[2])[:130]))

print("\n== UNKNOWN 18 件逐件（是否有库提示）==")
hint, nohint = [], []
for r in by["UNKNOWN"]:
    txt = " ".join(str(x[2]) for x in r["reasons"])
    (hint if "疑似库模块" in txt else nohint).append(r["rel"])
print("有库提示 %d 件:" % len(hint))
for rel in hint:
    print("  " + rel)
print("无提示 %d 件:" % len(nohint))
for rel in nohint:
    print("  " + rel)

print("\n== ARTIFACT 真写形态分布 ==")
how = collections.Counter()
for r in by["ARTIFACT"]:
    tw = r["facts"].get("true_writes") or []
    if tw:
        h = tw[0]["how"]
        how[h.split("(")[0]] += 1
    else:
        how["<facts 截断无 true_writes>"] += 1
print(dict(how), "合计", sum(how.values()))
# write_text 计数用 facts.true_writes 前 6 条，逐件全量重算需要重扫；先按首写形态给分布
print("\n== ARTIFACT 代表 6 件（首条真写行）==")
for r in by["ARTIFACT"][:0]:
    pass
for rel in ["lead/a_dim_reduced_20261108/_verify_hy4_recompute.py",
            "lead/advset_indep_20261109/_ai_grade.py",
            "lead/advset_indep_20261109/_ai_invariants.py",
            "lead/b2_preaudit_20261106/_b2_probe.py",
            "lead/cert_realcheck_20261109/_cr_real_verify.py",
            "lead/check_family_20261109/_cf_compose_lineage.py"]:
    m = [r for r in by["ARTIFACT"] if r["rel"] == rel]
    if m:
        r = m[0]
        tw = r["facts"].get("true_writes") or []
        print("  %s  n_true_writes=%s  首写=%s" % (rel, r["facts"].get("n_true_writes"),
                                                  json.dumps(tw[0], ensure_ascii=False) if tw else "[]"))

print("\n== PROBE 代表 4 件 ==")
for rel in ["lead/advset_indep_20261109/_ai2_baseline.py",
            "lead/advset_indep_20261109/_ai2_selfcheck.py",
            "lead/b2b_candidate_review3_20261107/_review_probe_r3.py",
            "lead/bexec_n4_20261108/_n4_fingerprint.py"]:
    m = [r for r in by["PROBE"] if r["rel"] == rel]
    if m:
        r = m[0]
        print("  %s  verdict=%s n_prints=%s" % (rel, r["verdict"], r["facts"].get("n_prints")))

# 真写形态全量分布（需要重扫源码；这里按 facts.true_writes 里出现的 how 全集粗算 + 单独重扫一遍以取证）
print("\n== 真写形态全量重扫（判据 collect_true_writes 口径）==")
import importlib.util
spec = importlib.util.spec_from_file_location("_ec_criterion", os.path.join(HERE, "_ec_criterion.py"))
EC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EC)
import ast
cnt = collections.Counter()
for r in by["ARTIFACT"]:
    p = os.path.join(ROOT, r["rel"].replace("/", os.sep))
    src, enc, err = EC.read_source(p)
    tree, perr = EC.parse_source(src)
    ws = EC.collect_true_writes(tree, src)
    for w in ws:
        cnt[w["how"].split("(")[0]] += 1
print("全部真写站点形态计数:", dict(cnt))

print("\n== 263 件中 match/case（ast.Match）计数 ==")
n_match = 0
match_rels = []
for r in res:
    p = os.path.join(ROOT, r["rel"].replace("/", os.sep))
    try:
        with open(p, "rb") as f:
            raw = f.read()
        for enc in ("utf-8-sig", "utf-8", "gbk"):
            try:
                src = raw.decode(enc); break
            except UnicodeDecodeError:
                continue
        else:
            src = raw.decode("utf-8", "replace")
        tree = ast.parse(src)
        if any(isinstance(nd, getattr(ast, "Match", ())) for nd in ast.walk(tree)):
            n_match += 1
            match_rels.append(r["rel"])
    except Exception as e:
        print("  ERR", r["rel"], repr(e))
print("含 ast.Match 的件数 =", n_match, match_rels)

print("\n== PROBE/ARTIFACT/UNKNOWN 占 263 的 rel 前缀分布（前 12 目录）==")
pref = collections.Counter(r["rel"].rsplit("/", 1)[0] for r in res)
for k, v in pref.most_common(12):
    print("  %3d  %s" % (v, k))

print("\n== _ecv 合成控与 12 件比对结果（复核员 _ecv_compare_results.json）==")
with open(os.path.join(HERE, "_ecv_compare_results.json"), encoding="utf-8") as f:
    V = json.load(f)
if isinstance(V, list):
    agree = sum(1 for x in V if x.get("agree") or x.get("match") or x.get("same"))
    print("条目数 =", len(V), "键样例 =", sorted(V[0].keys()) if V else [])
    for x in V[:40]:
        print("  ", json.dumps(x, ensure_ascii=False)[:200])
else:
    print("顶层键 =", sorted(V.keys()))
    print(json.dumps(V, ensure_ascii=False)[:2000])
