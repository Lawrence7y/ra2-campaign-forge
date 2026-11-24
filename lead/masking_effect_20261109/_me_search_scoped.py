# -*- coding: utf-8 -*-
"""_me_search_scoped.py — Step 4(a) bounded whole-repo search.

The unbounded os.walk stalls on a pathological long-path tree under
lead/o1prime_reach_20261109/_o1_tmp/long_B3_longpath/ (the same tree ugrep
warned about). This script caps path length at 240 chars and depth at 8,
which still covers EVERY script-bearing directory in this repo, and reports
exactly what it pruned so the scope is auditable.

Read-only. Writes only _me_search_out.txt in this write domain.
"""
import os, io, re, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SKIP_DIRS = {".git", "__pycache__", ".mimosa", "node_modules"}
MAXPATH = 240
MAXDEPTH = 8
TEXT_EXT = (".py", ".md", ".txt", ".json", ".ps1", ".sh", ".js", ".ts")

PAT_CLI = re.compile(r'action\s*=\s*["\']append["\']|add_argument\(\s*["\']--(?:needle|pattern|keyword|kw|term|token|match)', re.I)
PAT_LOOP = re.compile(r'(?:for\s+\w+\s+in\s+needles|any\s*\(\s*\w+\s+in\s+\w+\s+for\s+\w+\s+in\s+\w+|min\s*\(\s*.*\.find\s*\(.*\)\s*for\s+\w+\s+in)', re.I)
PAT_SELFTEST = re.compile(r'SELF_TEST|self[-_ ]?test|负控|negative.?control', re.I)
PAT_FLAGS = re.compile(r'--needle|--pattern|--keyword|--kw|--term|--match|--include|--exclude', re.I)

def walk():
    pruned = []
    for dp, dn, fn in os.walk(ROOT, topdown=True):
        rel_d = os.path.relpath(dp, ROOT).replace("\\", "/")
        depth = 0 if rel_d == "." else rel_d.count("/") + 1
        keep = []
        for d in dn:
            if d in SKIP_DIRS:
                continue
            full = os.path.join(dp, d)
            if len(full) > MAXPATH or depth + 1 > MAXDEPTH:
                pruned.append((os.path.relpath(full, ROOT).replace("\\", "/"), "long-or-deep"))
                continue
            keep.append(d)
        dn[:] = keep
        for f in sorted(fn):
            if not f.lower().endswith(TEXT_EXT):
                continue
            p = os.path.join(dp, f)
            if len(p) > MAXPATH:
                pruned.append((os.path.relpath(p, ROOT).replace("\\", "/"), "long-path"))
                continue
            try:
                b = open(p, "rb").read()
            except (OSError, ValueError):
                continue
            if b"\x00" in b:
                continue
            yield p, b.decode("utf-8", "replace")
    walk.pruned = pruned

def main():
    out = []
    def P(s=""):
        out.append(s); print(s)
    P("ROOT = %s" % ROOT)
    P("SCOPE: text ext=%s ; skip dirs=%s ; max path len=%d ; max depth=%d" %
      (TEXT_EXT, sorted(SKIP_DIRS), MAXPATH, MAXDEPTH))
    P("SEARCH-1 (CLI append/flags) regex = %s" % PAT_CLI.pattern)
    P("SEARCH-2 (loop/min/any over needles) regex = %s" % PAT_LOOP.pattern)
    P("SEARCH-3 (self-test/negative control) regex = %s" % PAT_SELFTEST.pattern)
    P("")
    cli_hits, loop_hits, st_files, multi_cmd = [], [], {}, []
    nfiles = 0
    for p, txt in walk():
        nfiles += 1
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        for i, L in enumerate(txt.splitlines(), 1):
            if PAT_CLI.search(L):
                cli_hits.append((rel, i, L.strip()[:190]))
            if PAT_LOOP.search(L):
                loop_hits.append((rel, i, L.strip()[:190]))
            if PAT_SELFTEST.search(L):
                st_files.setdefault(rel, []).append((i, L.strip()[:150]))
            flags = PAT_FLAGS.findall(L)
            if len(flags) >= 2 and "--" in L:
                multi_cmd.append((rel, i, L.strip()[:210]))
    P("scanned text files = %d" % nfiles)
    P("pruned paths = %d (long path / depth cap); samples:" % len(getattr(walk, "pruned", [])))
    for r, why in getattr(walk, "pruned", [])[:6]:
        P("   %s  [%s]" % (r[:150], why))
    P("")
    P("=== A. CLI 'action=append' / --needle|--pattern|--keyword definitions (%d hits) ===" % len(cli_hits))
    for rel, i, L in cli_hits:
        P("  %s:%d | %s" % (rel, i, L))
    P("")
    P("=== B. loop / min(any(...)) over multiple needles (%d hits) ===" % len(loop_hits))
    for rel, i, L in loop_hits:
        P("  %s:%d | %s" % (rel, i, L))
    P("")
    P("=== C. one-line commands passing >=2 needle-like flags (%d hits) ===" % len(multi_cmd))
    for rel, i, L in multi_cmd[:80]:
        P("  %s:%d | %s" % (rel, i, L))
    if len(multi_cmd) > 80:
        P("  ... (%d more)" % (len(multi_cmd) - 80))
    P("")
    P("=== D. files mentioning self-test / negative control (%d files) ===" % len(st_files))
    for rel in sorted(st_files):
        P("  %s  (%d lines)" % (rel, len(st_files[rel])))
    P("")
    io.open(os.path.join(HERE, "_me_search_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()
