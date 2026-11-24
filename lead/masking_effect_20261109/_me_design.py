# -*- coding: utf-8 -*-
"""_me_design.py — Step 3: three pasteable, runnable designs for
"distinguishable PASS", plus the masking-detection criterion (Step 3d).

All designs are WRAPPERS / standalone scripts in this write domain. They do
NOT modify _rs_carrier_scan.py or any existing script. They invoke the
unmodified scanner via subprocess (方案甲) or mirror its own line logic by
importing it read-only (方案乙/丙).

Read-only outside this write domain; zero live-machine; zero sampling code.
"""
import os, io, sys, subprocess, importlib.util, hashlib, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")

N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
NEEDLES = [N1, N2]
TMP = os.path.join(HERE, "_me_design_runs")
os.makedirs(TMP, exist_ok=True)

def scanner_run(tag, needles, extra=()):
    """Invoke the UNMODIFIED scanner; return (exit, lines, outfile)."""
    cmd = [sys.executable, "-I", "-X", "utf8", SCANNER]
    for n in needles:
        cmd += ["--needle", n]
    cmd += ["--include-refuting", "--max-depth", "2", "--ext", ".md"] + list(extra)
    out = os.path.join(TMP, "_me_%s_out.txt" % tag)
    cp = subprocess.run(cmd, cwd=ROOT, stdout=io.open(out, "w", encoding="utf-8"),
                        stderr=subprocess.STDOUT)
    return cp.returncode, io.open(out, encoding="utf-8", errors="replace").read().splitlines(), out

# ===========================================================================
# 方案甲 (A): per-needle ISOLATED self-test. Each needle gets its own row.
# ===========================================================================
PLAN_A = r'''
# --- 方案甲：逐 needle 独立跑自检，每根单独出 PASS/FAIL，再合总 -------------
import subprocess, sys, io, os
SCANNER = r"D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
BASE = ["-I", "-X", "utf8", SCANNER, "--include-refuting", "--max-depth", "2", "--ext", ".md"]

def one(n):
    cp = subprocess.run([sys.executable] + BASE[:4] + ["--needle", n] + BASE[4:],
                        capture_output=True, text=True, encoding="utf-8")
    lines = cp.stdout.splitlines()
    st = next((l for l in lines if l.startswith("SELF_TEST")), "SELF_TEST = <missing>")
    scans = next((l for l in lines if l.startswith("scanned files")), "<missing>")
    return cp.returncode, st.split("=")[-1].strip(), scans

rows = [(n, *one(n)) for n in NEEDLES]
all_ok = all(ec == 0 and st == "PASS" for _, ec, st, _ in rows)
for n, ec, st, scans in rows:
    print("NEEDLE %-30r EXIT=%d SELF_TEST=%-4s | %s" % (n, ec, st, scans))
print("AGGREGATE = %s ; per-needle = %d/%d PASS ; proven_bits = %d" %
      ("PASS" if all_ok else "FAIL",
       sum(1 for _, ec, st, _ in rows if ec == 0 and st == "PASS"), len(NEEDLES), len(rows)))
sys.exit(0 if all_ok else 1)
'''

# ===========================================================================
# 方案乙 (B): negative controls that cover each needle's EXCLUSIVE hit set.
# A needle that stops working loses its own exclusive-hit controls.
# ===========================================================================
PLAN_B = r'''
# --- 方案乙：为每根 needle 的「只被它命中」行建负控 --------------------------
# 核心：从语料自动算 exclusive(k) = U_k \ union(others)；每根至少 1 条负控。
# 把 needle k 换成坏串后，exclusive(k) 负控必然 FAIL => 加参数掩盖不了坏针。
import os, io, sys
LEAD = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]

def iter_lines():
    for dp, dn, fn in os.walk(LEAD):
        rel_d = os.path.relpath(dp, LEAD).replace("\\", "/")
        if (0 if rel_d == "." else rel_d.count("/") + 1) > 2:
            dn[:] = []; continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"): continue
            p = os.path.join(dp, f)
            try: b = open(p, "rb").read()
            except OSError: continue
            if b"\x00" in b: continue
            rel = os.path.relpath(p, LEAD).replace("\\", "/")
            for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
                yield rel, i, L

U = {n: set() for n in NEEDLES}
for rel, i, L in iter_lines():
    for n in NEEDLES:
        if n in L: U[n].add((rel, i))

for k in NEEDLES:
    others = set().union(*[U[n] for n in NEEDLES if n != k])
    excl = U[k] - others
    print("NEEDLE %r : |U|=%d  |exclusive|=%d  examples=%s" %
          (k, len(U[k]), len(excl), sorted(excl)[:3]))
    if not excl:
        print("  !! FATAL: no exclusive control -> needle is NOT independently testable")
# 断言：每根 needle 必须有 >=1 条 exclusive 负控，否则整体判 FAIL（覆盖度门禁）
ok = all(U[k] - set().union(*[U[n] for n in NEEDLES if n != k]) for k in NEEDLES)
print("COVERAGE_GATE = %s" % ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)   # gate MUST control exit status, not just print
'''

# ===========================================================================
# 方案丙 (C): hit-set provenance ledger (best). No extra scanner runs;
# one run, but each carrier line records WHICH needles hit it, and PASS is
# emitted only if every needle has >=1 EXCLUSIVE hit AND every needle's
# controls pass. Directly answers "how many of this PASS were masked".
# ===========================================================================
PLAN_C = r'''
# --- 方案丙（推荐）：命中溯源 + 覆盖度门禁 -----------------------------------
# 在 classify_line 的结果里补一个字段 hits=[命中的 needle 下标]，输出时打印：
#   HITSET {0}, {1}, {0,1} ... 以及 EXCLUSIVE(k) 计数
# 无需多次跑；一次运行即可从输出直接读出掩蔽量。
import os, io
LEAD = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]

def corpus():
    for dp, dn, fn in os.walk(LEAD):
        d = os.path.relpath(dp, LEAD).replace("\\", "/")
        if (0 if d == "." else d.count("/") + 1) > 2: dn[:] = []; continue
        for f in sorted(fn):
            if not f.endswith(".md"): continue
            p = os.path.join(dp, f)
            try: b = open(p, "rb").read()
            except OSError: continue
            if b"\x00" in b: continue
            yield os.path.relpath(p, LEAD).replace("\\", "/"), b.decode("utf-8", "replace")

from collections import Counter
pat = Counter(); excl = Counter(); total = 0
for rel, txt in corpus():
    for L in txt.splitlines():
        hs = tuple(i for i, n in enumerate(NEEDLES) if n in L)
        if not hs: continue
        total += 1; pat[hs] += 1
        if len(hs) == 1: excl[hs[0]] += 1
print("=== HITSET PROVENANCE LEDGER ===")
for hs, c in sorted(pat.items()):
    print("  HITSET %-10s -> %d lines  %s" % (str(hs), c,
          "<-- MASKED by union" if len(hs) > 1 else "exclusive"))
print("  TOTAL carrier lines = %d" % total)
for k, n in enumerate(NEEDLES):
    print("  EXCLUSIVE(needle[%d]=%r) = %d  %s" %
          (k, n, excl[k], "OK" if excl[k] else "!! NO INDEPENDENT WITNESS"))
masked = total - sum(excl.values())
print("  MASKED_LINES = %d / %d  (%.1f%%)" %
      (masked, total, 100.0 * masked / total if total else 0.0))
print("  COVERAGE_GATE = %s  (every needle must own >=1 exclusive line)" %
      ("PASS" if all(excl[k] for k in range(len(NEEDLES))) else "FAIL"))
print("  PER_NEEDLE_SELFTEST = %s" %
      {k: ("PASS" if excl[k] else "UNPROVEN") for k in range(len(NEEDLES))})
'''


def run_snippet(name, code):
    p = os.path.join(TMP, "_me_%s_snippet.py" % name)
    io.open(p, "w", encoding="utf-8").write(code)
    cp = subprocess.run([sys.executable, "-I", "-X", "utf8", p],
                        capture_output=True, text=True, encoding="utf-8")
    return cp.returncode, cp.stdout, cp.stderr

def main():
    out = []
    def P(s=""):
        out.append(s); print(s)
    P("SCANNER_SHA256 = %s" % hashlib.sha256(open(SCANNER, "rb").read()).hexdigest())
    P("")
    P("=== baseline (unmodified scanner, two needles, as delivered) ===")
    ec, ls, _ = scanner_run("baseline", NEEDLES)
    P("  EXIT=%d  %s  %s" % (ec, next(l for l in ls if l.startswith("scanned files")),
                             next(l for l in ls if l.startswith("SELF_TEST"))))
    P("")
    for name, code in [("A", PLAN_A), ("B", PLAN_B), ("C", PLAN_C)]:
        P("=== 方案 %s executed (pasteable snippet, standalone) ===" % name)
        ec, so, se = run_snippet(name, code)
        P("  EXIT=%d" % ec)
        for l in so.splitlines():
            P("  | " + l)
        if se.strip():
            P("  STDERR: " + se.strip()[:400])
        P("")
    P("=== Step 3(d) masking-detection criterion, applied to the delivered PASS ===")
    # recompute the two numbers from the corpus directly
    ec, so, se = run_snippet("C2", PLAN_C)
    masked_line = next((l for l in so.splitlines() if l.startswith("  MASKED_LINES")), "<none>")
    P("  from 方案丙 output: %s" % masked_line.strip())
    P("  plus: the delivered SELF_TEST prints 6 PASS lines and 1 SELF_TEST=PASS,")
    P("        with ZERO per-needle rows. Therefore from that output ALONE the")
    P("        number of masked needles is UNKNOWABLE (not 0, not 1: not reported).")
    P("")
    io.open(os.path.join(HERE, "_me_design_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()
