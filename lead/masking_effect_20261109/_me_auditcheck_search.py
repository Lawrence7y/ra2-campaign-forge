# -*- coding: utf-8 -*-
"""_me_auditcheck_search.py — bounded WHOLE-REPO multi-input test sweep.

NEW file in the sole write domain; read-only elsewhere; does not modify any
pre-existing file or script. Same three regex families as _me_search_git.py,
plus a wider bounded universe (git ls-files + whole-repo untracked sweep with
an explicit depth cap and long-path guard). Writes only _me_auditcheck_search_*.

Honest scope declaration: this is a BOUNDED sweep, NOT an unbounded whole-repo
walk. Directories whose absolute path exceeds LONG_PATH_GUARD are skipped and
counted; the previously-reported long_B3_longpath tree is not descended.
"""
import os, io, re, subprocess, time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TEXT_EXT = (".py", ".md", ".txt", ".json", ".ps1", ".sh", ".js", ".ts")
SKIP = {".git", "__pycache__", ".mimosa", "node_modules", ".tmp"}
MAX_DEPTH = 8
LONG_PATH_GUARD = 240

PAT_CLI = re.compile(r'action\s*=\s*["\']append["\']|add_argument\(\s*["\']--(?:needle|pattern|keyword|kw|term|token|match|exclude|include)', re.I)
PAT_LOOP = re.compile(r'(?:for\s+\w+\s+in\s+(?:needles|patterns|keywords|terms)|any\s*\(\s*\w+\s+in\s+\w+\s+for\s+\w+\s+in|min\s*\(\s*.*\.find\s*\(.*\)\s*for\s+\w+\s+in)', re.I)
PAT_ST = re.compile(r'SELF_TEST|self[-_ ]?test|负控|negative.?control', re.I)
PAT_FLAGS = re.compile(r'--(?:needle|pattern|keyword|kw|term|match|include|exclude)\b')

o = []
def P(s=""):
    o.append(s); print(s)

t0 = time.time()
cp = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
tracked = [b.decode("utf-8", "replace") for b in cp.stdout.split(b"\x00") if b]
seen = set()
for rel in tracked:
    seen.add(os.path.normcase(os.path.abspath(os.path.join(ROOT, rel))))
P("git ls-files entries = %d ; unique tracked paths = %d" % (len(tracked), len(seen)))

added = skipped_deep = skipped_long = skipped_dirs = 0
for dp, dn, fn in os.walk(ROOT, topdown=True):
    rel_d = os.path.relpath(dp, ROOT).replace("\\", "/")
    depth = 0 if rel_d == "." else rel_d.count("/") + 1
    if depth > MAX_DEPTH:
        dn[:] = []; skipped_deep += 1; continue
    if len(dp) > LONG_PATH_GUARD:
        dn[:] = []; skipped_long += 1
        P("  LONG-PATH SKIP (len=%d, depth=%d): %s" % (len(dp), depth, rel_d[:160]))
        continue
    kept = []
    for d in dn:
        if d in SKIP:
            skipped_dirs += 1
        else:
            kept.append(d)
    dn[:] = kept
    for f in fn:
        p = os.path.join(dp, f)
        k = os.path.normcase(os.path.abspath(p))
        if k not in seen:
            seen.add(k); added += 1
P("bounded untracked sweep (whole repo, depth<=%d, long-path guard %d) added = %d" %
  (MAX_DEPTH, LONG_PATH_GUARD, added))
P("skipped: depth-cap dirs=%d ; long-path dirs=%d ; excluded-name dirs=%d" %
  (skipped_deep, skipped_long, skipped_dirs))
P("universe paths = %d" % len(seen))

A, B, C, D = [], [], [], set()
nread = 0
for p in sorted(seen):
    if not p.lower().endswith(TEXT_EXT) or not os.path.isfile(p):
        continue
    try:
        b = io.open(p, "rb").read()
    except (OSError, ValueError):
        continue
    if b"\x00" in b:
        continue
    nread += 1
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
        if PAT_CLI.search(L):
            A.append((rel, i, L.strip()[:180]))
        if PAT_LOOP.search(L):
            B.append((rel, i, L.strip()[:180]))
        if PAT_ST.search(L):
            D.add(rel)
        if len(PAT_FLAGS.findall(L)) >= 2:
            C.append((rel, i, L.strip()[:180]))
P("scanned text files = %d" % nread)
P("A (CLI action=append / needle-like defs) = %d" % len(A))
P("B (any()/min() over multiple inputs) = %d" % len(B))
P("C (>=2 needle-like flags on one line) = %d" % len(C))
P("D (files mentioning self-test/negative control) = %d" % len(D))
P("elapsed = %.1f s" % (time.time() - t0))
P("")
P("=== A. entries (all) ===")
for rel, i, L in A:
    P("  %s:%d | %s" % (rel, i, L))
P("")
P("=== B. top scripts by hit count ===")
for rel, n in Counter(r for r, _, _ in B).most_common(20):
    P("  %-70s %d" % (rel, n))
P("")
P("=== C. top files by hit count ===")
for rel, n in Counter(r for r, _, _ in C).most_common(15):
    P("  %-70s %d" % (rel, n))
P("")
P("=== SCOPE HONESTY ===")
P("  This is a BOUNDED sweep (depth<=%d, path length<=%d, excluded names %s)." %
  (MAX_DEPTH, LONG_PATH_GUARD, sorted(SKIP)))
P("  It is NOT an unbounded whole-repo walk; skipped directories are counted above.")
P("  A/B/C/D are COUNTS of regex hits, not a per-file executed audit; only the")
P("  scripts listed in section 5 of MASKING_EFFECT_AUDIT.md were read/run here.")
P("  Everything else is 未验 (not individually verified).")
P("")
io.open(os.path.join(HERE, "_me_auditcheck_search_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")
