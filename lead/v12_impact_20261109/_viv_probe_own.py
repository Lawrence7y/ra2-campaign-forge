"""Independent library-corpus probe: S3 reachability, regressions, FP/FN, R10xV12.

Does not import the author's scripts. Only reads protected inputs and writes
_viv_probe_own.json. Resolves token lists by AST-scanning the two gate dirs.
"""
import sys
sys.dont_write_bytecode = True
import ast
import importlib.util
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "v12_impact_20261109"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13REG = ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py"
TV2 = ROOT / "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md"
TV3 = ROOT / "lead/gate_fp7_20261108/_g7_tv3_double_negation.md"


def load(p, n):
    s = importlib.util.spec_from_file_location(n, str(p))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


R = load(RULE, "_viv_rule2")
G7 = load(G7P, "_viv_g72")
N13 = load(N13REG, "_viv_n13")


def find_const(dirs, varname):
    hits = []
    for d in dirs:
        for p in sorted((ROOT / d).glob("*.py")):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == varname for t in node.targets):
                    try:
                        hits.append((str(p), list(ast.literal_eval(node.value))))
                    except Exception:
                        pass
    return hits


d_tok = find_const(["lead/gate_n13_20261109"], "DEFAULT_TOKENS")
a_tok = find_const(["lead/gate_fp7_20261108"], "ASSERT_TOKENS")
print("DEFAULT_TOKENS sources:", [(Path(x).name, v) for x, v in d_tok])
print("ASSERT_TOKENS  sources:", [(Path(x).name, v) for x, v in a_tok])
assert d_tok and a_tok
N13_TOKENS = d_tok[0][1]
ASSERT_TOKENS = a_tok[0][1]


def hits_of(text, toks):
    return sorted((m.start(), t) for t in toks for m in re.finditer(re.escape(t), text))


corpus = []
for sid, text, note, src in N13.NEGATIVES:
    corpus.append(("N13_NEG/" + sid, text, N13_TOKENS, "CATCH", src + " | " + note))
for sid, text, expect, src in N13.POSITIVES:
    corpus.append(("N13_POS/" + sid, text, N13_TOKENS, "PASS", src))
for lab, path in (("TV2", TV2), ("TV3", TV3)):
    for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if not hits_of(line, ASSERT_TOKENS):
            continue
        exp = "CATCH" if lab == "TV2" else ("PASS" if i == 10 else "CATCH")
        corpus.append(("R10_TV/%s:L%d" % (lab, i), line, ASSERT_TOKENS, exp,
                       "逐字读盘 %s L%d" % (path.as_posix(), i)))

rows = []
for cid, text, toks, expect, note in corpus:
    for pos, tok in hits_of(text, toks):
        v = R.classify_v12(text, pos, pos + len(tok), tok)
        k = G7.r10_context(text, pos, pos + len(tok))["kind"]
        r10_catch = k in ("assertion", "double_neg")  # R10 problem / R12 hand-off
        stage = ("S0" if v["hard"] else "S1" if v["override"] else "S2" if v["weak"] else "S3")
        rows.append(dict(cid=cid, expect=expect, tok=tok, pos=pos, text=text[:220],
                         r10_kind=k, r10_catch=r10_catch, v12=v["verdict"],
                         v12_catch=(v["verdict"] == "V2"), s3=bool(v["review_flag"]),
                         stage=stage, hard=list(v["hard"]), override=v["override"],
                         weak=list(v["weak"]), unit=v["unit"], note=note))

# unit-level aggregation
units = defaultdict(list)
for r in rows:
    units[r["cid"]].append(r)
unit_rows = []
for cid, rs in units.items():
    expect = rs[0]["expect"]
    r10_fail = any(x["r10_catch"] for x in rs)
    v12_fail = any(x["v12_catch"] for x in rs)
    unit_rows.append(dict(cid=cid, expect=expect, n=len(rs), r10_fail=r10_fail,
                          v12_fail=v12_fail,
                          r10_correct=(r10_fail == (expect == "CATCH")),
                          v12_correct=(v12_fail == (expect == "CATCH"))))

cross = dict(Counter(("R10%s_V12%s" % ("catch" if r["r10_catch"] else "pass",
                                      "catch" if r["v12_catch"] else "pass")) for r in rows))
summary = dict(
    corpus_units=len(corpus), units_with_hits=len(units), hits=len(rows),
    v12_verdict=dict(Counter(r["v12"] for r in rows)),
    stage=dict(Counter(r["stage"] for r in rows)),
    s3_review_flag_true=sum(1 for r in rows if r["s3"]),
    s3_and_should_PASS=sum(1 for r in rows if r["s3"] and r["expect"] == "PASS"),
    s3_and_should_CATCH=sum(1 for r in rows if r["s3"] and r["expect"] == "CATCH"),
    cross_R10xV12=cross,
    unit_level=dict(
        r10_correct=sum(1 for u in unit_rows if u["r10_correct"]),
        v12_correct=sum(1 for u in unit_rows if u["v12_correct"]),
        r10_FP=sum(1 for u in unit_rows if u["expect"] == "PASS" and u["r10_fail"]),
        r10_FN=sum(1 for u in unit_rows if u["expect"] == "CATCH" and not u["r10_fail"]),
        v12_FP=sum(1 for u in unit_rows if u["expect"] == "PASS" and u["v12_fail"]),
        v12_FN=sum(1 for u in unit_rows if u["expect"] == "CATCH" and not u["v12_fail"]),
        r10_FP_eliminated_by_V12=sum(1 for u in unit_rows if u["expect"] == "PASS" and u["r10_fail"] and not u["v12_fail"]),
        new_FP_vs_R10=sum(1 for u in unit_rows if u["expect"] == "PASS" and not u["r10_fail"] and u["v12_fail"]),
        regression_vs_R10=sum(1 for u in unit_rows if u["expect"] == "CATCH" and u["r10_fail"] and not u["v12_fail"]),
        corrected_R10_FN=sum(1 for u in unit_rows if u["expect"] == "CATCH" and not u["r10_fail"] and u["v12_fail"]),
    ),
)
print(json.dumps(summary, ensure_ascii=False, indent=1))

print("\n--- ALL S3(review_flag) HITS, each with expect / R10 / V12 ---")
for r in rows:
    if r["s3"]:
        print("  %-17s expect=%-5s stage=%s R10=%-11s V12=%s | %s" % (r["cid"], r["expect"], r["stage"], r["r10_kind"], r["v12"], r["text"][:90]))

print("\n--- R10 catch & V12 pass (7 hits) ---")
for r in rows:
    if r["r10_catch"] and not r["v12_catch"]:
        print("  %-17s expect=%-5s R10=%-11s V12=%s hard=%r | %s" % (r["cid"], r["expect"], r["r10_kind"], r["v12"], r["hard"], r["text"][:90]))

print("\n--- R10 pass & V12 catch (8 hits) ---")
for r in rows:
    if not r["r10_catch"] and r["v12_catch"]:
        print("  %-17s expect=%-5s R10=%-11s V12=%s stage=%s | %s" % (r["cid"], r["expect"], r["r10_kind"], r["v12"], r["stage"], r["text"][:90]))

print("\n--- unit MISMATCH lists ---")
print("V12 FP units:", [u["cid"] for u in unit_rows if u["expect"] == "PASS" and u["v12_fail"]])
print("V12 FN units:", [u["cid"] for u in unit_rows if u["expect"] == "CATCH" and not u["v12_fail"]])
print("R10 FP units:", [u["cid"] for u in unit_rows if u["expect"] == "PASS" and u["r10_fail"]])
print("R10 FN units:", [u["cid"] for u in unit_rows if u["expect"] == "CATCH" and not u["r10_fail"]])
print("R10 FP eliminated by V12:", [u["cid"] for u in unit_rows if u["expect"] == "PASS" and u["r10_fail"] and not u["v12_fail"]])
print("V12 new FP vs R10:", [u["cid"] for u in unit_rows if u["expect"] == "PASS" and not u["r10_fail"] and u["v12_fail"]])
print("V12 regression vs R10:", [u["cid"] for u in unit_rows if u["expect"] == "CATCH" and u["r10_fail"] and not u["v12_fail"]])
print("R10 FN corrected by V12:", [u["cid"] for u in unit_rows if u["expect"] == "CATCH" and not u["r10_fail"] and u["v12_fail"]])

# n4_yi_final:155 hard/override co-trigger spot check
p = ROOT / "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md"
t = p.read_text(encoding="utf-8")
line155 = t.split("\n")[154]
print("\n--- n4_yi_final:155 ---")
print("LINE =", line155)
for tok in ("可应用母本", "放行 N-5"):
    pos = line155.find(tok)
    if pos < 0:
        continue
    # use full-text positions
    base = t.find(line155)
    q = base + pos
    v = R.classify_v12(t, q, q + len(tok), tok)
    line, U, off, is_table, rel_u = R._unit_and_line(t, q, q + len(tok), tok)
    bare = R._strip_quotes(U)
    print("  tok=%s U=%r" % (tok, U))
    print("    U contains 已签 =", "已签" in U, "| U_bare contains 已签 =", "已签" in bare)
    print("    V2_OVERRIDE hits U =", [k for k in R.V2_OVERRIDE if k in U],
          "hits U_bare =", [k for k in R.V2_OVERRIDE if k in bare])
    print("    hard =", v["hard"], "verdict =", v["verdict"], "override_field =", repr(v["override"]))

(WD / "_viv_probe_own.json").write_text(
    json.dumps(dict(summary=summary, rows=rows, units=unit_rows), ensure_ascii=False, indent=1),
    encoding="utf-8")
