# -*- coding: utf-8 -*-
# _mcv_danger.py -- step 3 independent check: the "match=True => path non-empty" pattern.
# Runs: python -I -X utf8 <abs>/_mcv_danger.py
# For every .py under ROOT (pruned, depth<=8, <=400KB), locate lines that gate on
# match being True, then dump a +/- 8 line window containing any pathish/bytes access.
# Prints to stdout only; writes nothing.
import os, re

ROOT = "D:\\Project\\ra2-campaign-forge"
PRUNE = {"__pycache__", ".git", ".mimosa", "node_modules", ".tmp", ".workbuddy",
         ".zcode", ".zcode-watch", ".dsh-watch", ".pi", ".commandcode",
         ".blind1_tmp", "%TEMP%qc95rev_pyc", "venv", ".venv", "site-packages"}
SKIP = "merged_consumer_audit_20261109"

GATE = re.compile(r"match\"\]\s*(?:is|==)\s*True|match'\]\s*(?:is|==)\s*True|"
                  r"get\(\s*[\"']match[\"']\s*\)\s*(?:is|==)\s*True|"
                  r"\[\s*[\"']match[\"']\s*\]\s*\)|"
                  r"match\s*(?:is|==)\s*True")
PATHISH = re.compile(r"verified_path|\[\s*[\"']path[\"']\s*\]|\.get\(\s*[\"']path[\"']|"
                     r"\[\s*[\"']bytes[\"']\s*\]|recomputed|Path\(")

def main():
    dv = sc = pr = hits = 0
    out = []
    for cur, dirs, files in os.walk(ROOT):
        rel_dir = cur[len(ROOT):].lstrip("\\/")
        depth = 0 if not rel_dir else rel_dir.count(os.sep) + 1
        dv += 1
        kept = [d for d in dirs if d not in PRUNE]
        pr += len(dirs) - len(kept)
        dirs[:] = kept
        if depth >= 8:
            dirs[:] = []
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = cur + os.sep + fn
            if SKIP in fp:
                continue
            try:
                if os.path.getsize(fp) > 400000:
                    continue
                L = open(fp, encoding="utf-8", errors="replace").read().splitlines()
            except Exception:
                continue
            sc += 1
            rel = fp[len(ROOT) + 1:]
            for i, line in enumerate(L):
                if not GATE.search(line):
                    continue
                lo, hi = max(0, i - 2), min(len(L), i + 9)
                win = [(j + 1, L[j]) for j in range(lo, hi)]
                if any(PATHISH.search(x[1]) for x in win):
                    hits += 1
                    out.append((rel, i + 1, win))
    print("dirsVisited=%d scannedPy=%d pruned=%d DANGER_WINDOWS=%d" % (dv, sc, pr, hits))
    for rel, ln, win in out:
        print("\n--- %s : GATE_LINE=%d ---" % (rel, ln))
        for j, s in win:
            print("  %5d | %s" % (j, s.rstrip()[:200]))
    print("\nEXIT=0")

main()
