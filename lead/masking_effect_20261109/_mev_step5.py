# -*- coding: utf-8 -*-
"""_mev_step5.py — ASK 5: do the three "distinguishable PASS" plans REALLY
distinguish a true pass from the masked pass?

Decisive test named by the ask: take the SINGLE-NEEDLE FAIL scenario (the
orchestrator's actual command: --needle N1 only, SELF_TEST=FAIL) and apply
each plan to it. A plan that can "distinguish" must NOT certify PASS here.

Two variants:
  V1 = delivered two-needle scenario (we KNOW from the single-needle FAIL that
       this PASS is masked) -> a plan should output FAIL / not certify PASS.
  V2 = the literal single-needle command (k=1, NEEDLES=[N1]) -> scanner's own
       SELF_TEST is FAIL; plans must not report PASS.

We run (a) the author's EXACT pasteable PLAN_A/B/C strings, extracted read-only
from _me_design.py via ast, and (b) our own independent re-implementation of
the stated §3(a) criterion #2 (exclusive NEGATIVE CONTROL per needle).

Read-only outside this write domain. Outputs _mev_ prefixed.
"""
import os, io, ast, sys, subprocess, hashlib, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
DESIGN = os.path.join(HERE, "_me_design.py")
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
BROKEN = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
PY = sys.executable

CONTROLS = [
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
    ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
    ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196),
    ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129),
    ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22),
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
]

def extract_plans():
    tree = ast.parse(io.open(DESIGN, encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
           and isinstance(node.targets[0], ast.Name) \
           and node.targets[0].id in ("PLAN_A", "PLAN_B", "PLAN_C"):
            val = ast.literal_eval(node.value)
            out[node.targets[0].id] = val
    return out

def exec_plan(name, code):
    p = os.path.join(HERE, "_mev_%s_run.py" % name)
    io.open(p, "w", encoding="utf-8").write(code)
    cp = subprocess.run([PY, "-I", "-X", "utf8", p], cwd=ROOT,
                        capture_output=True, text=True, encoding="utf-8", shell=False)
    return cp.returncode, cp.stdout, cp.stderr

def single_needle_variant(code):
    """Replace the 2-needle literal with a 1-needle literal (literal single-needle FAIL)."""
    old = 'NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]'
    new = 'NEEDLES = ["只能判「不可复现」"]'
    if old not in code:
        raise RuntimeError("needle literal not found")
    return code.replace(old, new)

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
                b = open(p, "rb").read()
            except OSError:
                continue
            if b"\x00" in b:
                continue
            rel = os.path.relpath(p, LEAD).replace("\\", "/")
            for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
                yield rel, i, L

def criterion2(needles):
    """Report §3(a) criterion #2, literally: >=1 NEGATIVE CONTROL in each
    needle's EXCLUSIVE hit set. Returns per-needle exclusive-control counts."""
    bykey = {(r, n): L for r, n, L in corpus_lines()}
    ex = [0] * len(needles)
    for rel, n in CONTROLS:
        L = bykey.get((rel, n), "")
        hs = [i for i, nd in enumerate(needles) if nd in L]
        if len(hs) == 1:
            ex[hs[0]] += 1
    return ex

def main():
    o = []
    def P(s=""):
        o.append(s); print(s)
    plans = extract_plans()
    P("=== ASK 5: apply plans to the SINGLE-NEEDLE FAIL scenario ===")
    P("extracted plan keys = %s" % sorted(plans))
    P("")
    # ground truth from my own earlier run
    n1out = io.open(os.path.join(HERE, "_mev_mech_n1only_out.txt"),
                    encoding="utf-8", errors="replace").read()
    gt = next((l.strip() for l in n1out.splitlines() if l.startswith("SELF_TEST")), "<missing>")
    P("GROUND TRUTH (my own unmodified-scanner run, --needle N1 only): %s" % gt)
    P("(and :22 got=<not-scanned>, EXIT=1) -- see _mev_mech_out.txt / _mev_mech_n1only_out.txt")
    P("")
    P("--- V1: author's EXACT plans on the DELIVERED two-needle scenario ---")
    for k in ("PLAN_A", "PLAN_B", "PLAN_C"):
        ec, so, se = exec_plan("v1_" + k, plans[k])
        verdict = [l.strip() for l in so.splitlines()
                   if ("AGGREGATE" in l or "COVERAGE_GATE" in l or
                       "PER_NEEDLE_SELFTEST" in l or "MASKED_LINES" in l)]
        P("  %s EXIT=%d : %s" % (k, ec, " ; ".join(verdict)))
        if se.strip():
            P("     STDERR: " + se.strip()[:200])
    P("")
    P("--- V2: author's EXACT plans with NEEDLES=[N1] (literal single-needle FAIL) ---")
    for k in ("PLAN_A", "PLAN_B", "PLAN_C"):
        code = single_needle_variant(plans[k])
        ec, so, se = exec_plan("v2_" + k, code)
        verdict = [l.strip() for l in so.splitlines()
                   if ("AGGREGATE" in l or "COVERAGE_GATE" in l or
                       "PER_NEEDLE_SELFTEST" in l or "SELF_TEST" in l)]
        P("  %s EXIT=%d : %s" % (k, ec, " ; ".join(verdict)))
        if se.strip():
            P("     STDERR: " + se.strip()[:200])
    P("")
    P("--- V3: report §3(a) criterion #2 implemented literally (exclusive NEGATIVE CONTROLS) ---")
    ex2 = criterion2([N1, N2])
    P("  needles=[N1,N2] : exclusive-control counts = %s" % ex2)
    P("  => criterion #2 requires >=1 per needle; N1 has %d => should be UNPROVEN / FAIL" % ex2[0])
    ex1 = criterion2([N1])
    P("  needles=[N1]    : exclusive-control counts = %s" % ex1)
    P("  => with k=1 criterion #2 is trivially satisfied (all 5 N1 controls exclusive),")
    P("     i.e. criterion #2 also FAILS to catch the single-needle self-test FAIL")
    P("")
    P("=== JUDGMENT ===")
    P("  PLAN_A: catches it (AGGREGATE=FAIL in both V1 and V2) -- because it literally")
    P("          runs each needle alone and ANDs the results.")
    P("  PLAN_B: does NOT catch it (COVERAGE_GATE=PASS in V1 and V2) -- it gates on")
    P("          |exclusive CORPUS lines|>0, never runs a per-needle self-test and never")
    P("          checks the 6 negative controls. k=1 makes the gate trivially PASS.")
    P("  PLAN_C: does NOT catch it (COVERAGE_GATE=PASS, PER_NEEDLE_SELFTEST={0:'PASS'}) --")
    P("          its 'PER_NEEDLE_SELFTEST' label is a misnomer: it is derived purely from")
    P("          corpus exclusivity, not from any self-test run. It contradicts the actual")
    P("          N1-alone SELF_TEST=FAIL.")
    P("  => report §3(a) criterion #2 as WRITTEN ('>=1 negative control in the exclusive")
    P("     set') is not implemented in PLAN_B/PLAN_C; as implemented they certify the")
    P("     very masked PASS the report declares untrustworthy.")
    P("")
    io.open(os.path.join(HERE, "_mev_step5_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")

if __name__ == "__main__":
    main()
