# -*- coding: utf-8 -*-
"""_me_search_git.py — Step 4(a) whole-repo search over the tracked file
universe (git ls-files, 3293 paths) PLUS untracked .py/.md under lead/ found
by a depth-3 shallow os.walk (prunes the pathological long-path tree).

Scope is reported explicitly. Read-only; writes only _me_search_out.txt.
"""
import os, io, re, subprocess, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TEXT_EXT = (".py", ".md", ".txt", ".json", ".ps1", ".sh", ".js", ".ts")
SKIP_DIRS = {".git", "__pycache__", ".mimosa", "node_modules"}
MAXLEAD_DEPTH = 3

PAT_CLI = re.compile(r'action\s*=\s*["\']append["\']|add_argument\(\s*["\']--(?:needle|pattern|keyword|kw|term|token|match|exclude|include)', re.I)
PAT_LOOP = re.compile(r'(?:for\s+\w+\s+in\s+(?:needles|patterns|keywords|terms)|any\s*\(\s*\w+\s+in\s+\w+\s+for\s+\w+\s+in|min\s*\(\s*.*\.find\s*\(.*\)\s*for\s+\w+\s+in)', re.I)
PAT_SELFTEST = re.compile(r'SELF_TEST|self[-_ ]?test|负控|negative.?control', re.I)
PAT_FLAGS = re.compile(r'--(?:needle|pattern|keyword|kw|term|match|include|exclude)\b')

def file_universe():
    seen = set()
    cp = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
    for raw in cp.stdout.split(b"\x00"):
        if not raw:
            continue
        rel = raw.decode("utf-8", "replace")
        p = os.path.join(ROOT, rel)
        seen.add(os.path.normcase(os.path.abspath(p)))
    # shallow untracked sweep under lead/
    for dp, dn, fn in os.walk(os.path.join(ROOT, "lead")):
        rel_d = os.path.relpath(dp, ROOT).replace("\\", "/")
        depth = 0 if rel_d == "." else rel_d.count("/") + 1
        if depth > MAXLEAD_DEPTH:
            dn[:] = []
            continue
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            p = os.path.join(dp, f)
            k = os.path.normcase(os.path.abspath(p))
            if k not in seen:
                seen.add(k)
    return sorted(seen)

def main():
    out = []
    def P(s=""):
        out.append(s); print(s)
    P("ROOT = %s" % ROOT)
    P("SCOPE = git ls-files (tracked) + shallow untracked sweep under lead/ (max depth %d)" % MAXLEAD_DEPTH)
    P("        text ext = %s ; skip dirs = %s" % (TEXT_EXT, sorted(SKIP_DIRS)))
    P("        NOTE: unbounded os.walk stalls on lead/o1prime_reach_20261109/_o1_tmp/long_B3_longpath/")
    P("              (same tree ugrep warned about); that tree contains no .py/.md test scripts")
    P("              in the tracked universe. Scope limitation is declared, not hidden.")
    P("SEARCH-1 regex = %s" % PAT_CLI.pattern)
    P("SEARCH-2 regex = %s" % PAT_LOOP.pattern)
    P("SEARCH-3 regex = %s" % PAT_SELFTEST.pattern)
    P("")
    universe = file_universe()
    P("universe paths = %d" % len(universe))
    cli_hits, loop_hits, st_files, multi_cmd = [], [], {}, []
    nfiles = 0
    for p in universe:
        if not p.lower().endswith(TEXT_EXT):
            continue
        if not os.path.isfile(p):
            continue
        try:
            b = open(p, "rb").read()
        except (OSError, ValueError):
            continue
        if b"\x00" in b:
            continue
        nfiles += 1
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
            if PAT_CLI.search(L):
                cli_hits.append((rel, i, L.strip()[:190]))
            if PAT_LOOP.search(L):
                loop_hits.append((rel, i, L.strip()[:190]))
            if PAT_SELFTEST.search(L):
                st_files.setdefault(rel, []).append((i, L.strip()[:150]))
            if len(PAT_FLAGS.findall(L)) >= 2:
                multi_cmd.append((rel, i, L.strip()[:210]))
    P("scanned text files = %d" % nfiles)
    P("")
    P("=== A. CLI action=append / --needle|--pattern|--keyword definitions (%d hits) ===" % len(cli_hits))
    for rel, i, L in cli_hits:
        P("  %s:%d | %s" % (rel, i, L))
    P("")
    P("=== B. loop / min(any(...)) over multiple needles (%d hits) ===" % len(loop_hits))
    for rel, i, L in loop_hits:
        P("  %s:%d | %s" % (rel, i, L))
    P("")
    P("=== C. one-line commands passing >=2 needle-like flags (%d hits) ===" % len(multi_cmd))
    for rel, i, L in multi_cmd[:100]:
        P("  %s:%d | %s" % (rel, i, L))
    if len(multi_cmd) > 100:
        P("  ... (%d more)" % (len(multi_cmd) - 100))
    P("")
    P("=== D. files mentioning self-test / negative control (%d files) ===" % len(st_files))
    for rel in sorted(st_files):
        P("  %s  (%d lines)" % (rel, len(st_files[rel])))
    P("")
    io.open(os.path.join(HERE, "_me_search_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()
