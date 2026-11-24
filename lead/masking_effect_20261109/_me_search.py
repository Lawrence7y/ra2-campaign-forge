# -*- coding: utf-8 -*-
"""_me_search.py — Step 4(a): whole-repo search for other multi-parameter /
multi-input tests (needle / pattern / keyword / term) and self-tests.

Read-only. Walks the repo, skips .git, handles long paths via os.walk with
errors='ignore' semantics; text-like files only; no writes except our own out.
"""
import os, io, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SKIP_DIRS = {".git", "__pycache__", ".mimosa", "node_modules"}

PAT_CLI = re.compile(r'action\s*=\s*["\']append["\']|add_argument\(\s*["\']--(?:needle|pattern|keyword|kw|term|token|match|include|exclude)', re.I)
PAT_LOOP = re.compile(r'(?:for\s+\w+\s+in\s+needles|any\s*\(\s*\w+\s+in\s+\w+\s+for\s+\w+\s+in\s+\w+|min\s*\(\s*.*\.find\s*\(.*\)\s*for\s+\w+\s+in)', re.I)
PAT_SELFTEST = re.compile(r'SELF_TEST|self[-_ ]?test|负控|negative.?control', re.I)
PAT_MULTI = re.compile(r'--needle|--pattern|--keyword|--kw|--term|--match', re.I)

TEXT_EXT = (".py", ".md", ".txt", ".json", ".ps1", ".sh", ".js", ".ts")

def walk():
    for dp, dn, fn in os.walk(ROOT, topdown=True):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in sorted(fn):
            if not f.lower().endswith(TEXT_EXT):
                continue
            p = os.path.join(dp, f)
            try:
                b = open(p, "rb").read()
            except (OSError, ValueError):
                continue
            if b"\x00" in b:
                continue
            yield p, b.decode("utf-8", "replace")

def main():
    out = []
    def P(s=""):
        out.append(s); print(s)
    P("ROOT = %s" % ROOT)
    P("SEARCH-1 pattern: %s" % PAT_CLI.pattern)
    P("SEARCH-2 pattern: %s" % PAT_LOOP.pattern)
    P("SEARCH-3 self-test: %s" % PAT_SELFTEST.pattern)
    P("")
    cli_hits, loop_hits, st_hits, multi_cmd = [], [], [], []
    nfiles = 0
    for p, txt in walk():
        nfiles += 1
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        ls = txt.splitlines()
        for i, L in enumerate(ls, 1):
            if PAT_CLI.search(L):
                cli_hits.append((rel, i, L.strip()[:200]))
            if PAT_LOOP.search(L):
                loop_hits.append((rel, i, L.strip()[:200]))
            if PAT_SELFTEST.search(L):
                st_hits.append((rel, i, L.strip()[:160]))
            if PAT_MULTI.search(L) and ("--" in L) and (L.count("--needle") + L.count("--pattern") + L.count("--keyword") + L.count("--term") + L.count("--match") >= 2):
                multi_cmd.append((rel, i, L.strip()[:220]))
    P("scanned text files = %d" % nfiles)
    P("")
    P("=== A. CLI 'action=append' / --needle|--pattern|--keyword... definitions (%d hits) ===" % len(cli_hits))
    for rel, i, L in cli_hits:
        P("  %s:%d | %s" % (rel, i, L))
    P("")
    P("=== B. loop/min(any(...)) over multiple needles (%d hits) ===" % len(loop_hits))
    for rel, i, L in loop_hits:
        P("  %s:%d | %s" % (rel, i, L))
    P("")
    P("=== C. commands that pass >=2 needle-like flags on ONE line (%d hits) ===" % len(multi_cmd))
    for rel, i, L in multi_cmd:
        P("  %s:%d | %s" % (rel, i, L))
    P("")
    P("=== D. self-test / negative-control mentions (%d hits, grouped by file) ===" % len(st_hits))
    by = {}
    for rel, i, L in st_hits:
        by.setdefault(rel, []).append((i, L))
    for rel in sorted(by):
        P("  %s  (%d lines)" % (rel, len(by[rel])))
        for i, L in by[rel][:4]:
            P("      :%d | %s" % (i, L))
    P("")
    io.open(os.path.join(HERE, "_me_search_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()
