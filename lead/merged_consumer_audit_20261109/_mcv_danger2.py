# -*- coding: utf-8 -*-
# _mcv_danger2.py -- step 3, BROADENED gate: any line referencing match as a boolean guard
# (including "is not True: continue", "if not ... match", "match is True", "match == True",
#  "if b['match']", "for ... if match", "sum(1 for ... match)").
# For each such line, dump a +/- 6 line window; flag windows containing a path/bytes/Path() access.
# Prints stdout only; writes nothing.
import os, re

ROOT = "D:\\Project\\ra2-campaign-forge"
PRUNE = {"__pycache__", ".git", ".mimosa", "node_modules", ".tmp", ".workbuddy",
         ".zcode", ".zcode-watch", ".dsh-watch", ".pi", ".commandcode",
         ".blind1_tmp", "%TEMP%qc95rev_pyc", "venv", ".venv", "site-packages"}
SKIP = "merged_consumer_audit_20261109"

# ANY line mentioning 'match' (as a word) AND a boolean-ish context
GATE = re.compile(r"\bmatch\b")
BOOL = re.compile(r"is\s+(?:not\s+)?True|==\s*(?:not\s+)?True|is\s+not\s+|\bif\b|\bnot\b|\band\b|\bor\b|sum\(|assert|for\b")
PATHISH = re.compile(r"verified_path|\[\s*[\"']path[\"']\s*\]|\.get\(\s*[\"']path[\"']|"
                     r"\[\s*[\"']bytes[\"']\s*\]|\.get\(\s*[\"']bytes[\"']|recomputed|\bPath\(")

def main():
    dv = sc = pr = 0
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
            # only files in the two relevant families (link-family dirs + r11/gate dirs)
            if not any(k in rel for k in ("r33e_merge_20261109", "samedoc_link_20261109",
                                          "equiv_class_20261109", "r11_f2_fix_20261109",
                                          "gate_r9r12_20261109", "gate_fp7_20261108")):
                continue
            seen = set()
            for i, line in enumerate(L):
                if not GATE.search(line) or not BOOL.search(line):
                    continue
                lo, hi = max(0, i - 3), min(len(L), i + 7)
                win = [(j + 1, L[j]) for j in range(lo, hi)]
                if not any(PATHISH.search(x[1]) for x in win):
                    continue
                key = (rel, lo)
                if key in seen:
                    continue
                seen.add(key)
                out.append((rel, i + 1, win))
    print("dirsVisited=%d scannedPy=%d pruned=%d SCOPED_WINDOWS=%d" % (dv, sc, pr, len(out)))
    for rel, ln, win in out:
        print("\n--- %s : MATCH_LINE=%d ---" % (rel, ln))
        for j, s in win:
            print("  %5d | %s" % (j, s.rstrip()[:190]))
    print("\nEXIT=0")

main()
