# -*- coding: utf-8 -*-
"""_mev_search.py — ASK 6: independently verify the "whole-repo" search claim.

Re-implements the search WITHOUT running the author's _me_search_git.py (which
would overwrite their _me_search_out.txt). Uses git ls-files -z for the tracked
universe (whole repo) plus a bounded os.walk for untracked text files with an
explicit depth cap and long-path guard. Reports counts and compares with the
author's recorded _me_search_out.txt headers. Read-only; outputs _mev_ prefixed.
"""
import os, io, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TEXT_EXT = (".py", ".md", ".txt", ".json", ".ps1", ".sh", ".js", ".ts")
SKIP = {".git", "__pycache__", ".mimosa", "node_modules"}
MAX_DEPTH = 6

PAT_CLI = re.compile(r'action\s*=\s*["\']append["\']|add_argument\(\s*["\']--(?:needle|pattern|keyword|kw|term|token|match|exclude|include)', re.I)
PAT_LOOP = re.compile(r'(?:for\s+\w+\s+in\s+(?:needles|patterns|keywords|terms)|any\s*\(\s*\w+\s+in\s+\w+\s+for\s+\w+\s+in|min\s*\(\s*.*\.find\s*\(.*\)\s*for\s+\w+\s+in)', re.I)
PAT_ST = re.compile(r'SELF_TEST|self[-_ ]?test|负控|negative.?control', re.I)
PAT_FLAGS = re.compile(r'--(?:needle|pattern|keyword|kw|term|match|include|exclude)\b')

def main():
    o = []
    def P(s=""):
        o.append(s); print(s)
    P("=== ASK 6: independent whole-repo search verification ===")
    seen = set()
    cp = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
    tracked = [raw.decode("utf-8", "replace") for raw in cp.stdout.split(b"\x00") if raw]
    for rel in tracked:
        seen.add(os.path.normcase(os.path.abspath(os.path.join(ROOT, rel))))
    ntracked = len(seen)
    P("git ls-files entries = %d ; unique tracked paths = %d" % (len(tracked), ntracked))
    # bounded untracked sweep over the WHOLE repo (not just lead/)
    added = 0
    for dp, dn, fn in os.walk(ROOT):
        rel_d = os.path.relpath(dp, ROOT).replace("\\", "/")
        depth = 0 if rel_d == "." else rel_d.count("/") + 1
        if depth > MAX_DEPTH:
            dn[:] = []
            continue
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp, f)
            k = os.path.normcase(os.path.abspath(p))
            if k not in seen:
                seen.add(k); added += 1
    P("bounded untracked sweep (depth<=%d, whole repo) added = %d" % (MAX_DEPTH, added))
    P("universe paths = %d" % len(seen))
    cli, loop, stfiles, multi, nread = [], [], set(), [], 0
    for p in sorted(seen):
        if not p.lower().endswith(TEXT_EXT) or not os.path.isfile(p):
            continue
        try:
            b = open(p, "rb").read()
        except (OSError, ValueError):
            continue
        if b"\x00" in b:
            continue
        nread += 1
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
            if PAT_CLI.search(L): cli.append((rel, i))
            if PAT_LOOP.search(L): loop.append((rel, i))
            if PAT_ST.search(L): stfiles.add(rel)
            if len(PAT_FLAGS.findall(L)) >= 2: multi.append((rel, i))
    P("scanned text files = %d" % nread)
    P("A (CLI append / needle-like defs) = %d" % len(cli))
    P("B (any()/min() over multiple inputs) = %d" % len(loop))
    P("C (>=2 needle-like flags on one line) = %d" % len(multi))
    P("D (files mentioning self-test/negative control) = %d" % len(stfiles))
    P("")
    P("=== author's recorded headers (read-only from _me_search_out.txt) ===")
    au = io.open(os.path.join(HERE, "_me_search_out.txt"), encoding="utf-8", errors="replace").read().splitlines()
    for l in au:
        if l.startswith("=== ") or l.startswith("universe paths") or l.startswith("scanned text files"):
            P("  " + l.strip())
    P("")
    P("=== scope-honesty assessment ===")
    P("  author's SCOPE line: %s" % next((l.strip() for l in au if l.startswith("SCOPE =")), "<missing>"))
    P("  author explicitly logged a long-path-tree stall and declared the scan is")
    P("  NOT an unbounded whole-repo walk (_me_search_out.txt:4-6; _me_REPORT.md:222).")
    P("  Report §6 item 13 labels it '全库多输入测试清单' and the five-step summary")
    P("  says '全库搜出' -- that wording overstates a bounded search, though the")
    P("  limitation IS declared in the report body and in the search output itself.")
    P("")
    io.open(os.path.join(HERE, "_mev_search_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")

if __name__ == "__main__":
    main()
