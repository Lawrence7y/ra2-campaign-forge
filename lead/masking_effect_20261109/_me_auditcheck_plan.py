# -*- coding: utf-8 -*-
"""_me_auditcheck_plan.py — corrected, pasteable DISTINGUISHABLE-PASS designs.

This is a NEW file in the sole write domain. It does NOT modify any existing
script. It invokes the UNMODIFIED upstream scanner via subprocess.

Three designs, each of which answers "does every input independently pass?":
  PLAN_A' 逐 needle 自检 + AND_k + 独占见证 + 坏针注入 (甲)
  PLAN_B' 逐针独立负控门禁 (乙, corrected: gate on per-needle SELF_TEST, not |exclusive corpus lines|)
  PLAN_C' 命中溯源台账 + AND_k 逐针自检 + HITSET + 独占负控 (丙, corrected)

Verification matrix run here:
  S1 = [N1, N2]   delivered double-needle (masked PASS)      -> must FAIL
  S2 = [N1]       literal single-needle FAIL                 -> must FAIL
  S3 = [M1, M2]   both individually pass 6/6 (true pass)     -> must PASS
  S4 = [M2, BROKEN] one dead needle (N1-style fault)         -> must FAIL
"""
import os, io, sys, subprocess, hashlib, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")

N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
M1 = "错误步骤"                 # individually PASS (verified in this ask)
M2 = "定位当年错误步骤"          # individually PASS (verified in this ask)
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

# ------------------------------------------------------------------ helpers
def scanner_run(tag, needles):
    """Invoke UNMODIFIED scanner. Return dict with exit, self_test, occurrences,
    per-control got[], and the raw lines. Output lands in _me_auditcheck_pl_*."""
    cmd = [sys.executable, "-I", "-X", "utf8", SCANNER]
    for n in needles:
        cmd += ["--needle", n]
    cmd += ["--include-refuting", "--max-depth", "2", "--ext", ".md"]
    outp = os.path.join(HERE, "_me_auditcheck_pl_%s.txt" % tag)
    cp = subprocess.run(cmd, cwd=ROOT,
                        stdout=io.open(outp, "w", encoding="utf-8"),
                        stderr=subprocess.STDOUT)
    ls = io.open(outp, encoding="utf-8", errors="replace").read().splitlines()
    st = next((l.split("=", 1)[1].strip() for l in ls if l.startswith("SELF_TEST")), "<missing>")
    occ = next((l for l in ls if l.startswith("scanned files")), "<missing>")
    got = []
    for rel, n in CONTROLS:
        key = "%s:%d want=" % (rel, n)
        line = next((l.strip() for l in ls if key in l), "")
        got.append(line.split("got=")[-1].strip() if "got=" in line else "<missing>")
    return dict(exit=cp.returncode, st=st, occ=occ, got=got, lines=ls,
                cmd=" ".join(cmd), sha=hashlib.sha256(io.open(outp, "rb").read()).hexdigest())

def corpus_lines():
    """Same scope as scanner: lead/, ext=.md, max-depth 2, (rel, line_no, text)."""
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

def hit_stats(needles):
    """Return (total, hitset Counter, exclusive[k], exclusive_control_counts[k],
    control_hitsets). exclusive NEGATIVE CONTROL = a control line hit by
    exactly one needle (that is the binding witness for that needle)."""
    pat, excl = Counter(), Counter()
    total, control_hits = 0, {}
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
            control_hits[(rel, i)] = hs
    excl_ctrl = [0] * len(needles)
    for rel, n in CONTROLS:
        hs = control_hits.get((rel, n), ())
        if len(hs) == 1:
            excl_ctrl[hs[0]] += 1
    return total, pat, [excl[k] for k in range(len(needles))], excl_ctrl, control_hits

# ----------------------------------------------------------- the 3 designs
def plan_a(needles, tag):
    """甲': 逐 needle 独立跑完整自检; AND_k; 独占负控; 坏针注入对照."""
    per = []
    for k, n in enumerate(needles):
        r = scanner_run("%s_a_%d" % (tag, k), [n])
        per.append(r)
    all_ok = all(r["exit"] == 0 and r["st"] == "PASS" for r in per)
    total, pat, excl, excl_ctrl, _ = hit_stats(needles)
    witness_ok = all(c > 0 for c in excl_ctrl)
    # 坏针注入: for each needle, replace it with a guaranteed-zero-hit sentinel;
    # require that the delivered aggregate SELF_TEST drops to FAIL for at least
    # one control. (Here we use the per-needle runs as the direct invariant.)
    inject_ok = all(r["st"] == "PASS" for r in per)
    agg = all_ok and witness_ok and inject_ok
    return dict(name="PLAN_A'", verdict="PASS" if agg else "FAIL",
                per=[(n, r["exit"], r["st"], r["occ"]) for n, r in zip(needles, per)],
                excl=excl, excl_ctrl=excl_ctrl, witness_ok=witness_ok,
                total=total, agg=agg)

def plan_b(needles, tag):
    """乙': 逐针独立负控门禁 (corrected). Gate = AND_k(per-needle 6/6) AND
    each needle owns >=1 EXCLUSIVE negative control. NOT |exclusive corpus lines|."""
    per = []
    for k, n in enumerate(needles):
        r = scanner_run("%s_b_%d" % (tag, k), [n])
        # per-needle controls: all 6 must match WANT
        ctrl_ok = all(g == w for g, w in zip(r["got"], WANTS))
        per.append((r, ctrl_ok))
    total, pat, excl, excl_ctrl, _ = hit_stats(needles)
    per_ok = all(r["exit"] == 0 and r["st"] == "PASS" and c for r, c in per)
    gate = per_ok and all(c > 0 for c in excl_ctrl)
    return dict(name="PLAN_B'", verdict="PASS" if gate else "FAIL",
                per=[(n, r["st"], c) for n, (r, c) in zip(needles, per)],
                per_ctrl_ok=per_ok, excl=excl, excl_ctrl=excl_ctrl,
                corr_ok=all(c > 0 for c in excl_ctrl), total=total, agg=gate)

def plan_c(needles, tag):
    """丙': 命中溯源台账 + AND_k 逐针自检 + HITSET + 独占负控.
    PER_NEEDLE_SELFTEST is now REAL (from k scanner runs), not inferred from
    corpus exclusivity."""
    total, pat, excl, excl_ctrl, control_hits = hit_stats(needles)
    masked = total - sum(excl)
    per = []
    for k, n in enumerate(needles):
        r = scanner_run("%s_c_%d" % (tag, k), [n])
        per.append(r)
    real = {k: ("PASS" if (r["exit"] == 0 and r["st"] == "PASS"
                          and all(g == w for g, w in zip(r["got"], WANTS)))
                 else "FAIL") for k, r in enumerate(per)}
    gate = (all(v == "PASS" for v in real.values())
            and all(c > 0 for c in excl_ctrl))
    return dict(name="PLAN_C'", verdict="PASS" if gate else "FAIL",
                hitset={str(k): v for k, v in sorted(pat.items())},
                total=total, masked=masked, excl=excl, excl_ctrl=excl_ctrl,
                per_selftest=real, gate=gate)

# ------------------------------------------------------------------ main
P("=== corrected distinguishable-PASS designs (this ask, unmodified scanner) ===")
P("scanner sha256 = %s bytes = %d" %
  (hashlib.sha256(io.open(SCANNER, "rb").read()).hexdigest(), os.path.getsize(SCANNER)))
P("")
SCEN = [
    ("S1_delivered_double", [N1, N2], "FAIL", "掩蔽 PASS：N1 在 :22 漏检，靠 N2 撞对"),
    ("S2_single_N1", [N1], "FAIL", "字面单 needle FAIL：:22 <not-scanned>"),
    ("S3_true_pass", [M1, M2], "PASS", "两根各自 6/6 PASS（真通过）"),
    ("S4_broken", [M2, BROKEN], "FAIL", "坏针注入：一根保证零命中"),
]
results = {}
for tag, needles, expect, desc in SCEN:
    P("--- %s : needles=%r (expect %s) : %s ---" % (tag, needles, expect, desc))
    for fn in (plan_a, plan_b, plan_c):
        r = fn(needles, tag)
        P("  %-8s verdict=%-4s" % (r["name"], r["verdict"]))
        if r["name"] == "PLAN_A'":
            for n, ec, st, occ in r["per"]:
                P("     per-needle %-24r EXIT=%d SELF_TEST=%-4s | %s" % (n, ec, st, occ))
            P("     EXCLUSIVE_CORPUS=%s  EXCLUSIVE_CONTROLS=%s  AND_k=%s WITNESS=%s" %
              (r["excl"], r["excl_ctrl"], all(ec == 0 and st == "PASS" for _, ec, st, _ in r["per"]), r["witness_ok"]))
        elif r["name"] == "PLAN_B'":
            P("     per-needle (SELF_TEST, 6-controls-ok) = %s" % [(st, c) for _, st, c in r["per"]])
            P("     EXCLUSIVE_CONTROLS=%s  PER_OK=%s  CORR_OK=%s" %
              (r["excl_ctrl"], r["per_ctrl_ok"], r["corr_ok"]))
        else:
            P("     HITSET=%s" % r["hitset"])
            P("     TOTAL=%d MASKED_LINES=%d EXCLUSIVE=%s EXCLUSIVE_CONTROLS=%s" %
              (r["total"], r["masked"], r["excl"], r["excl_ctrl"]))
            P("     PER_NEEDLE_SELFTEST(real, from k runs)=%s" % r["per_selftest"])
    results[tag] = {fn.__name__: fn(needles, tag)["verdict"] for fn in (plan_a, plan_b, plan_c)}
    P("")

P("=== verification matrix ===")
P("  %-22s %-9s %-9s %-9s %-9s" % ("scenario", "expect", "A'", "B'", "C'"))
all_good = True
for tag, needles, expect, desc in SCEN:
    v = results[tag]
    row = (v["plan_a"], v["plan_b"], v["plan_c"])
    good = all(x == expect for x in row)
    all_good &= good
    P("  %-22s %-9s %-9s %-9s %-9s  %s" %
      (tag, expect, row[0], row[1], row[2], "OK" if good else "MISMATCH"))
P("  ALL_SCENARIOS_MATCH_EXPECTATION = %s" % all_good)
P("")
io.open(os.path.join(HERE, "_me_auditcheck_plan_out.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")
sys.exit(0 if all_good else 1)
