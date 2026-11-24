# -*- coding: utf-8 -*-
"""_me_auditcheck_plan2.py — CORRECTED, pasteable DISTINGUISHABLE-PASS designs.

Supersedes the exploratory _me_auditcheck_plan.py: the hard "exclusive negative
control" gate was itself mis-specified (reviewer's partial verdict flagged
report §3(a) criterion #2 as flawed). Here:

  GATE (all three schemes) = AND_k over REAL per-needle self-tests:
       for each needle k, run the UNMODIFIED scanner ALONE with only that
       needle; require EXIT=0 AND all 6 negative controls match WANT.
       AGGREGATE = AND_k. This is the reviewer-CONFIRMED correct core (PLAN_A).

  DIAGNOSTICS (reported, NOT gating): HITSET histogram, MASKED_LINES,
       EXCLUSIVE(k), EXCLUSIVE_CONTROLS(k) — quantify masking, do not certify.

  Extra invariant: 坏针注入 (dead needle) must drop AGGREGATE to FAIL.

NEW file in sole write domain; read-only elsewhere; does not modify any
pre-existing file or script. Outputs _me_auditcheck_pl2_*.

Verification matrix:
  S1 [N1,N2]         delivered masked PASS  -> must FAIL  (N1 alone FAILs)
  S2 [N1]            literal single FAIL    -> must FAIL
  S3 [M1,M2]         both individually 6/6 -> must PASS  (genuine true pass)
  S4 [M2, BROKEN]    one dead needle       -> must FAIL
"""
import os, io, sys, subprocess, hashlib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")

N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
M1 = "只能判"           # individually EXIT=0 SELF_TEST=PASS 6/6 (verified this ask)
M2 = "不能定位当年"      # individually EXIT=0 SELF_TEST=PASS 6/6 (verified this ask)
BROKEN = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"

CONTROLS = [
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
    ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
    ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196),
    ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129),
    ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22),
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
]
WANTS = ["ASSERTION", "ASSERTION", "ASSERTION", "ASSERTION",
         "REFUTING_QUOTE", "ASSERTION"]

OUT = []
def P(s=""):
    OUT.append(s)
    print(s)

def scanner_run(tag, needles):
    cmd = [sys.executable, "-I", "-X", "utf8", SCANNER]
    for n in needles:
        cmd += ["--needle", n]
    cmd += ["--include-refuting", "--max-depth", "2", "--ext", ".md"]
    outp = os.path.join(HERE, "_me_auditcheck_pl2_%s.txt" % tag)
    cp = subprocess.run(cmd, cwd=ROOT,
                        stdout=io.open(outp, "w", encoding="utf-8"),
                        stderr=subprocess.STDOUT)
    ls = io.open(outp, encoding="utf-8", errors="replace").read().splitlines()
    st = next((l.split("=", 1)[1].strip() for l in ls if l.startswith("SELF_TEST")), "<missing>")
    occ = next((l for l in ls if l.startswith("scanned files")), "<missing>")
    got = []
    for rel, n in CONTROLS:
        key = "%s:%d want=" % (rel, n)
        L = next((l.strip() for l in ls if key in l), "")
        got.append(L.split("got=")[-1].strip() if "got=" in L else "<missing>")
    ctrl_ok = all(g == w for g, w in zip(got, WANTS))
    return dict(exit=cp.returncode, st=st, occ=occ, got=got, ctrl_ok=ctrl_ok,
                sha=hashlib.sha256(io.open(outp, "rb").read()).hexdigest())

def corpus_lines():
    for dp, dn, fn in os.walk(LEAD):
        rel_d = os.path.relpath(dp, LEAD).replace("\\", "/")
        depth = 0 if rel_d == "." else rel_d.count("/") + 1
        if depth > 2:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            try:
                b = io.open(p, "rb").read()
            except OSError:
                continue
            if b"\x00" in b:
                continue
            rel = os.path.relpath(p, LEAD).replace("\\", "/")
            for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
                yield rel, i, L

def diagnostics(needles):
    """HITSET / MASKED_LINES / EXCLUSIVE / EXCLUSIVE_CONTROLS as DIAGNOSTICS."""
    pat, excl = Counter(), Counter()
    total, ctrl_hits = 0, {}
    ctrl_keys = set(CONTROLS)
    for rel, i, L in corpus_lines():
        hs = tuple(k for k, n in enumerate(needles) if n in L)
        if not hs:
            continue
        total += 1
        pat[hs] += 1
        if len(hs) == 1:
            excl[hs[0]] += 1
        if (rel, i) in ctrl_keys:
            ctrl_hits[(rel, i)] = hs
    excl_ctrl = [0] * len(needles)
    for rel, n in CONTROLS:
        hs = ctrl_hits.get((rel, n), ())
        if len(hs) == 1:
            excl_ctrl[hs[0]] += 1
    return dict(total=total, hitset={str(k): v for k, v in sorted(pat.items())},
                masked=total - sum(excl[k] for k in range(len(needles))),
                excl=[excl[k] for k in range(len(needles))], excl_ctrl=excl_ctrl)

def gate(needles, tag):
    """AND_k over REAL per-needle self-tests. This is the ONLY gate."""
    per = []
    for k, n in enumerate(needles):
        r = scanner_run("%s_%d" % (tag, k), [n])
        ok = (r["exit"] == 0 and r["st"] == "PASS" and r["ctrl_ok"])
        per.append((n, r, ok))
    agg = all(ok for _, _, ok in per)
    return per, agg

def plan_a(needles, tag):
    """甲' 逐 needle 独立跑自检 + AND_k (零改动上游脚本)."""
    per, agg = gate(needles, "a" + tag)
    return dict(verdict="PASS" if agg else "FAIL",
                rows=[(n, r["exit"], r["st"], r["occ"]) for n, r, _ in per], agg=agg)

def plan_b(needles, tag):
    """乙' 逐针独立负控门禁 (corrected: gate on real per-needle 6-control match,
    NOT on |exclusive corpus lines|>0)."""
    per, agg = gate(needles, "b" + tag)
    return dict(verdict="PASS" if agg else "FAIL",
                rows=[(n, r["st"], r["ctrl_ok"]) for n, r, _ in per], agg=agg)

def plan_c(needles, tag):
    """丙' 命中溯源台账 + REAL PER_NEEDLE_SELFTEST (from k runs) + HITSET.
    PER_NEEDLE_SELFTEST is now derived from actual self-tests, not corpus
    exclusivity. HITSET/MASKED/EXCLUSIVE are reported as diagnostics only."""
    per, agg = gate(needles, "c" + tag)
    d = diagnostics(needles)
    real = {k: ("PASS" if ok else "FAIL") for k, (_, _, ok) in enumerate(per)}
    return dict(verdict="PASS" if agg else "FAIL", per_selftest=real, diag=d, agg=agg)

P("=== CORRECTED distinguishable-PASS designs (this ask, unmodified scanner) ===")
P("scanner sha256 = %s bytes = %d" %
  (hashlib.sha256(io.open(SCANNER, "rb").read()).hexdigest(),
   os.path.getsize(SCANNER)))
P("GATE = AND_k(REAL per-needle self-test: EXIT=0 AND 6/6 controls match WANT)")
P("HITSET / MASKED_LINES / EXCLUSIVE / EXCLUSIVE_CONTROLS = DIAGNOSTICS (not gating)")
P("")
SCEN = [
    ("S1_delivered_double", [N1, N2], "FAIL", "掩蔽 PASS：N1 在 :22 漏检，靠 N2 撞对"),
    ("S2_single_N1", [N1], "FAIL", "字面单 needle FAIL：:22 <not-scanned>"),
    ("S3_true_pass", [M1, M2], "PASS", "两根各自独立 6/6 PASS（真通过）"),
    ("S4_broken", [M2, BROKEN], "FAIL", "坏针注入：一根保证零命中"),
]
results = {}
for tag, needles, expect, desc in SCEN:
    P("--- %s : needles=%r (expect %s) : %s ---" % (tag, needles, expect, desc))
    a, b, c = plan_a(needles, tag), plan_b(needles, tag), plan_c(needles, tag)
    P("  PLAN_A' verdict=%-4s AND_k=%s" % (a["verdict"], a["agg"]))
    for n, ec, st, occ in a["rows"]:
        P("     per-needle %-30r EXIT=%d SELF_TEST=%-4s | %s" % (n, ec, st, occ))
    P("  PLAN_B' verdict=%-4s (per-needle SELF_TEST, 6-controls-ok)=%s" %
      (b["verdict"], [(st, ok) for _, st, ok in b["rows"]]))
    P("  PLAN_C' verdict=%-4s PER_NEEDLE_SELFTEST(REAL)=%s" % (c["verdict"], c["per_selftest"]))
    d = c["diag"]
    P("     HITSET=%s TOTAL=%d MASKED_LINES=%d EXCLUSIVE=%s EXCLUSIVE_CONTROLS=%s" %
      (d["hitset"], d["total"], d["masked"], d["excl"], d["excl_ctrl"]))
    results[tag] = (a["verdict"], b["verdict"], c["verdict"])
    P("")

P("=== verification matrix ===")
P("  %-22s %-8s %-8s %-8s %-8s" % ("scenario", "expect", "A'", "B'", "C'"))
all_good = True
for tag, needles, expect, desc in SCEN:
    row = results[tag]
    good = all(x == expect for x in row)
    all_good &= good
    P("  %-22s %-8s %-8s %-8s %-8s  %s" %
      (tag, expect, row[0], row[1], row[2], "OK" if good else "MISMATCH"))
P("  ALL_SCENARIOS_MATCH_EXPECTATION = %s" % all_good)
P("")
P("=== 掩蔽检测判据 (diagnostics for the delivered S1 double-needle PASS) ===")
d = diagnostics([N1, N2])
P("  HITSET = %s" % d["hitset"])
P("  EXCLUSIVE(k) = %s ; EXCLUSIVE_CONTROLS(k) = %s" % (d["excl"], d["excl_ctrl"]))
P("  MASKED_LINES = %d / %d" % (d["masked"], d["total"]))
P("  MASKED_NEEDLES = %d" % sum(1 for e in d["excl"] if e == 0))
P("  DISTINGUISHABLE_PASS(现行交付口径) = FALSE  (SELF_TEST 不是 AND_k 得出)")
P("  DISTINGUISHABLE_PASS(甲'/乙'/丙' 口径) = FALSE (S1 => FAIL, 正确拒绝)")
P("")
io.open(os.path.join(HERE, "_me_auditcheck_plan2_out.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")
sys.exit(0 if all_good else 1)
