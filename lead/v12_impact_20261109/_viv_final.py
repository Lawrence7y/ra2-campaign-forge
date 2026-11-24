"""Final consolidated checks: incumbent-relative deltas, real-gate scan, hash stability."""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "v12_impact_20261109"


def load(p, n):
    s = importlib.util.spec_from_file_location(n, str(p))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


G = load(ROOT / "lead/gate_fp7_20261108/_g7_predicates.py", "_viv_f_g")
N = load(ROOT / "lead/gate_n13_20261109/_n13_predicates.py", "_viv_f_n")
R = load(ROOT / "lead/gate_v1v2_20261109/_v12_rule.py", "_viv_f_r")
NR = load(ROOT / "lead/gate_n13_20261109/_n13_regression.py", "_viv_f_nr")
r10fn = [getattr(G, k) for k in dir(G) if callable(getattr(G, k))
         and getattr(getattr(G, k), "__code__", None)
         and getattr(getattr(G, k), "__code__").co_argcount == 2
         and "r10_context" in getattr(getattr(G, k), "__code__").co_names
         and "warnings" in getattr(getattr(G, k), "__code__").co_varnames][0]

print("=== A. incumbent R10+R12 gate vs V12 vs N13 gate, on the 45 units ===")
corpus = []
for sid, text, note, src in NR.NEGATIVES:
    corpus.append(("N13_NEG/" + sid, text, list(N.DEFAULT_TOKENS), "CATCH"))
for sid, text, expect, src in NR.POSITIVES:
    corpus.append(("N13_POS/" + sid, text, list(N.DEFAULT_TOKENS), "PASS"))
ASSERT = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
for lab, fn in (("TV2", "_g7_tv2_overreach_positive.md"), ("TV3", "_g7_tv3_double_negation.md")):
    for i, line in enumerate((ROOT / "lead/gate_fp7_20261108" / fn).read_text(encoding="utf-8").split("\n"), 1):
        if any(t in line for t in ASSERT):
            corpus.append(("R10_TV/%s:L%d" % (lab, i), line, ASSERT,
                           "CATCH" if lab == "TV2" else ("PASS" if i == 10 else "CATCH")))
res = []
for cid, text, toks, expect in corpus:
    hit = sorted((m.start(), t) for t in toks for m in re.finditer(re.escape(t), text))
    if not hit:
        continue
    p10, w10, _ = r10fn(text, toks)
    p12, _ = G.r12_scan(text, toks)
    r10r12_fail = bool(p10 or p12)
    any_v2 = False
    for pos, tok in hit:
        if R.classify_v12(text, pos, pos + len(tok), tok)["verdict"] == "V2":
            any_v2 = True
    p13, _ = N.r13_assertions(text, list(N.DEFAULT_TOKENS), r10fn, G.r12_scan)
    n13_fail = bool(p13)
    res.append((cid, expect, r10r12_fail, any_v2, n13_fail,
                (r10r12_fail == (expect == "CATCH")), (any_v2 == (expect == "CATCH")),
                (n13_fail == (expect == "CATCH"))))
print("units_with_hits =", len(res))
print("R10+R12 correct = %d/%d  FP=%d FN=%d" % (sum(r[5] for r in res), len(res),
      sum(1 for r in res if r[1] == "PASS" and r[2]), sum(1 for r in res if r[1] == "CATCH" and not r[2])))
print("V12      correct = %d/%d  FP=%d FN=%d" % (sum(r[6] for r in res), len(res),
      sum(1 for r in res if r[1] == "PASS" and r[3]), sum(1 for r in res if r[1] == "CATCH" and not r[3])))
print("N13 gate correct = %d/%d  FP=%d FN=%d" % (sum(r[7] for r in res), len(res),
      sum(1 for r in res if r[1] == "PASS" and r[4]), sum(1 for r in res if r[1] == "CATCH" and not r[4])))
print("V12 vs R10+R12: eliminated_FP=%d new_FP=%d corrected_FN=%d regressions=%d" % (
    sum(1 for r in res if r[1] == "PASS" and r[2] and not r[3]),
    sum(1 for r in res if r[1] == "PASS" and not r[2] and r[3]),
    sum(1 for r in res if r[1] == "CATCH" and not r[2] and r[3]),
    sum(1 for r in res if r[1] == "CATCH" and r[2] and not r[3])))

print()
print("=== B. real-gate scan: does any gate pipeline script call classify_v12? ===")
hits = []
for p in ROOT.glob("lead/**/*.py"):
    try: t = p.read_text(encoding="utf-8")
    except Exception: continue
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    if "classify_v12" in t and "v12_impact_20261109" not in rel and "gate_v1v2_20261109" not in rel:
        hits.append(rel)
print("outside the two design/impact dirs:", hits)
gp = ROOT / "lead/gate_pipeline_20261109"
if gp.exists():
    for p in gp.glob("*.py"):
        t = p.read_text(encoding="utf-8")
        print("  ", p.name, "classify_v12=", "classify_v12" in t, "V2_OVERRIDE=", "V2_OVERRIDE" in t)

print()
print("=== C. 9 baseline hashes at end of this review ===")
BASE = {
 "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
 "lead/gate_v1v2_20261109/_v12_REPORT.md": ("10a90814d09f49b88fa378943960e137c20a426a47785de4dea22c55c3324100", 30098),
 "lead/gate_v1v2_20261109/_v12_regression.json": ("994e36a2bf6b977cff2eb3887607e6f2682966e19008389cd9391c0c78435bfb", 10484),
 "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
 "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
 "lead/gate_r9r12_20261109/_g9_gate.py": ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
 "lead/gate_doc_name_fix_20261109/_dn_regate_out.json": ("0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096", 22133),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
ok = 0
for rel, (h0, n0) in BASE.items():
    b = (ROOT / rel).read_bytes()
    h, n = hashlib.sha256(b).hexdigest(), len(b)
    m = (h == h0 and n == n0); ok += m
    print("  %-58s %s bytes=%-7d match=%s" % (rel, h[:12], n, m))
print("FINAL 9/9:", ok, "/9")
