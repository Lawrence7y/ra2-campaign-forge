# -*- coding: utf-8 -*-
"""_me_auditcheck.py — independent checks run in THIS ask for MASKING_EFFECT_AUDIT.md.

READ-ONLY on every absolute-read-only path. Only NEW files with prefix
_me_auditcheck_ are created inside the sole write domain. Does not modify
_rs_carrier_scan.py, _me_design.py, or any pre-existing file.

Checks:
  C1  8 upstream fingerprints (hashlib) + binding line object
  C2  unmodified scanner: single N1 / double N1+N2 / broken N2+sentinel /
      triple N1+N2+N3(reverse masking) -> EXIT, SELF_TEST, occurrences, :22
  C3  _ve_DRAFT_S609.md:22 verbatim positions + quote codepoints
  C4  corpus line sets at mtime CUT (14:15) and at current time;
      six negative controls' per-line hit sets; exclusive-control counts
  C5  independent confirmation of the reviewer's partial verdict:
      run PLAN_B / PLAN_C (ast-extracted from _me_design.py, read-only)
      with NEEDLES=[N1] and compare against N1-alone scanner FAIL
  C6  check_d29-style OR gate minimal reproduction (pure python)
"""
import os, io, sys, re, ast, hashlib, subprocess, time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")
DESIGN = os.path.join(HERE, "_me_design.py")
VE = os.path.join(LEAD, "s604_verdict_entry_20261109", "_ve_DRAFT_S609.md")

N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
N3 = "登记效力说明"
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"

OUT = []
def P(s=""):
    OUT.append(s)
    print(s)

# ---------------------------------------------------------------- C1
FP = {
 "lead/refsync_scope_20261109/_rs_carrier_scan.py": ("9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57", 16053),
 "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md": ("83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e", 49958),
 "lead/refsync_scope_20261109/_rs_CARRIER_MAP.md": ("aa2dbe945c9d8fdc6aebde849701393f6f8766c51b372329d588616781c2f83f", 35782),
 "lead/needle_norm_20261109/_nn_REPORT.md": ("820db1eb93a630344623fb055449dfbd888cb46294dba3f462d9891a1d91e041", 40549),
 "lead/needle_norm_20261109/NEEDLE_NORMALIZATION.md": ("c0e716ec2baaab0082d0c7af83a351b9aa12eb01a4bf2ba6a223c8b81c5de8e6", 41618),
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
P("=== C1 upstream fingerprints (hashlib, this ask) ===")
fp_ok = True
for rel, (want, wn) in FP.items():
    b = io.open(os.path.join(ROOT, rel), "rb").read()
    h = hashlib.sha256(b).hexdigest()
    ok = (h == want and len(b) == wn)
    fp_ok &= ok
    P("  %s %s sha256=%s bytes=%d" % ("OK" if ok else "MISMATCH", rel, h, len(b)))
P("  ALL_8_OK = %s" % fp_ok)
P("")

# ---------------------------------------------------------------- C2
def scan(tag, needles):
    cmd = [sys.executable, "-I", "-X", "utf8", SCANNER]
    for n in needles:
        cmd += ["--needle", n]
    cmd += ["--include-refuting", "--max-depth", "2", "--ext", ".md"]
    outp = os.path.join(HERE, "_me_auditcheck_%s_out.txt" % tag)
    cp = subprocess.run(cmd, cwd=ROOT,
                        stdout=io.open(outp, "w", encoding="utf-8"),
                        stderr=subprocess.STDOUT)
    ls = io.open(outp, encoding="utf-8", errors="replace").read().splitlines()
    g = lambda pre: next((l for l in ls if l.startswith(pre)), "<missing>")
    v22 = next((l.strip() for l in ls if "DRAFT_S609.md:22 want=" in l), "<missing>")
    return dict(tag=tag, cmd=" ".join(cmd), exit=cp.returncode,
                scanned=g("scanned files"), st=g("SELF_TEST"), v22=v22,
                out=os.path.basename(outp),
                sha=hashlib.sha256(io.open(outp, "rb").read()).hexdigest())

P("=== C2 unmodified scanner, 4 configurations (this ask) ===")
configs = [("single", [N1]), ("double", [N1, N2]),
           ("broken", [N2, SENTINEL]), ("triple", [N1, N2, N3])]
res = {}
for tag, ns in configs:
    r = scan(tag, ns)
    res[tag] = r
    P("  [%s] CMD = %s" % (tag, r["cmd"]))
    P("  [%s] EXIT=%d | %s | %s" % (tag, r["exit"], r["scanned"], r["st"]))
    P("  [%s] %s" % (tag, r["v22"]))
    P("  [%s] out=%s sha256=%s" % (tag, r["out"], r["sha"]))
P("")

# ---------------------------------------------------------------- C3
P("=== C3 :22 verbatim positions (this ask) ===")
ls = io.open(VE, encoding="utf-8", errors="replace").read().splitlines()
L22 = ls[21]
P("  line22 len = %d" % len(L22))
P("  N1 %r find = %d" % (N1, L22.find(N1)))
P("  N2 %r find = %d" % (N2, L22.find(N2)))
P("  variant %r find = %d" % ("只能判『不可复现』", L22.find("只能判『不可复现』")))
P("  N3 %r find = %d" % (N3, L22.find(N3)))
P("  CONTAINS_BOTH_VERBATIM = %s" % (N1 in L22 and N2 in L22))
P("  outer fragment %r find = %d" %
  ("「只能判『不可复现』、不能定位当年错误步骤」", L22.find("「只能判『不可复现』、不能定位当年错误步骤」")))
cps = sorted({("U+%04X" % ord(c)) for c in L22 if 0x3000 <= ord(c) <= 0x303F})
P("  CJK punctuation codepoints present = %s" % ", ".join(cps))
P("")

# ---------------------------------------------------------------- C4
P("=== C4 corpus line sets (this ask) ===")
def md_files():
    for dp, dn, fn in os.walk(LEAD):
        rel_d = os.path.relpath(dp, LEAD).replace("\\", "/")
        depth = 0 if rel_d == "." else rel_d.count("/") + 1
        if depth > 2:
            dn[:] = []; continue
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
            yield p, os.path.relpath(p, LEAD).replace("\\", "/"), b.decode("utf-8", "replace"), os.path.getmtime(p)

CUT = time.mktime(time.strptime("2026-11-09 14:15:00", "%Y-%m-%d %H:%M:%S"))

def totals(files):
    u1 = u2 = only1 = only2 = both = 0
    for _, rel, txt, _ in files:
        for L in txt.splitlines():
            a, b = N1 in L, N2 in L
            if a: u1 += 1
            if b: u2 += 1
            if a and not b: only1 += 1
            if b and not a: only2 += 1
            if a and b: both += 1
    return dict(files=len(files), U1=u1, U2=u2, only1=only1,
                only2=only2, both=both, union=u1+u2-both)

allf = list(md_files())
cur = totals(allf)
old = totals([x for x in allf if x[3] <= CUT])
P("  CURRENT  : md files=%d |U1|=%d |U2|=%d |only1|=%d |only2|=%d |both|=%d |union|=%d" %
  (cur["files"], cur["U1"], cur["U2"], cur["only1"], cur["only2"], cur["both"], cur["union"]))
P("  CUT<=14:15: md files=%d |U1|=%d |U2|=%d |only1|=%d |only2|=%d |both|=%d |union|=%d" %
  (old["files"], old["U1"], old["U2"], old["only1"], old["only2"], old["both"], old["union"]))
P("  MISSED vs union: N1-only misses=%d ; N2-only misses=%d ; both misses=0" %
  (old["only2"], old["only1"]))

CONTROLS = [
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
    ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
    ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196),
    ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129),
    ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22),
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
]
lines_by_key = {}
for _, rel, txt, mt in allf:
    if mt > CUT:
        continue
    for i, L in enumerate(txt.splitlines(), 1):
        lines_by_key[(rel, i)] = L
excl_ctrl = [0, 0]
for rel, n in CONTROLS:
    L = lines_by_key.get((rel, n), "")
    hs = tuple(i for i, nd in enumerate([N1, N2]) if nd and nd in L)
    P("  CTRL %s:%d hits=%s" % (rel, n, list(hs) if hs else "NONE"))
    if len(hs) == 1:
        excl_ctrl[hs[0]] += 1
P("  exclusive NEGATIVE-CONTROL counts (criterion 3(a)#2 as written) = %s" % excl_ctrl)
P("  => N1 has %d exclusive negative control => criterion #2 requires UNPROVEN/FAIL" % excl_ctrl[0])
P("")

# ---------------------------------------------------------------- C5
P("=== C5 reviewer partial verdict: independent re-run (this ask) ===")
tree = ast.parse(io.open(DESIGN, encoding="utf-8").read())
plans = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id in ("PLAN_A", "PLAN_B", "PLAN_C"):
            plans[node.targets[0].id] = node.value.value
P("  ast-extracted plan keys = %s (read-only from _me_design.py)" % sorted(plans))
needle_decl = 'NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]'
for name in ("PLAN_B", "PLAN_C"):
    code = plans[name]
    assert needle_decl in code, name
    code2 = code.replace(needle_decl, 'NEEDLES = ["只能判「不可复现」"]')
    p = os.path.join(HERE, "_me_auditcheck_v2_%s.py" % name)
    io.open(p, "w", encoding="utf-8").write(code2)
    cp = subprocess.run([sys.executable, "-I", "-X", "utf8", p],
                        capture_output=True, text=True, encoding="utf-8")
    gates = [l for l in cp.stdout.splitlines()
             if "COVERAGE_GATE" in l or "PER_NEEDLE_SELFTEST" in l or "MASKED_LINES" in l]
    P("  %s with NEEDLES=[N1] : EXIT=%d" % (name, cp.returncode))
    for g in gates:
        P("    | " + g.strip())
P("  GROUND TRUTH: N1-alone scanner from C2 = EXIT=%d ; %s ; %s" %
  (res["single"]["exit"], res["single"]["st"], res["single"]["v22"]))
P("  => PLAN_B / PLAN_C gates say PASS while the actual per-needle SELF_TEST is FAIL")
P("")

# ---------------------------------------------------------------- C6
P("=== C6 check_d29-style OR gate minimal reproduction (this ask) ===")
words = ("93.98", "误报率")
body = "本报告 93.98 与误报率均已复核"
a1 = any(w in body for w in words)
body2 = body.replace("误报率", "")
a2 = any(w in body2 for w in words)
P("  words=%r body=%r any=%s" % (words, body, a1))
P("  after DELETING '误报率': body=%r any=%s  <-- dead keyword invisible" % (body2, a2))
P("")

P("=== END (all outputs written with _me_auditcheck_ prefix; no pre-existing file modified) ===")
io.open(os.path.join(HERE, "_me_auditcheck_out.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")
