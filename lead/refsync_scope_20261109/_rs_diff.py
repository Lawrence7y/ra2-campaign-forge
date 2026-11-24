# -*- coding: utf-8 -*-
"""_rs_diff.py — compare independent scan vs orchestrator-supplied carrier map,
report per-line needle membership and depth statistics. Read-only.
"""
import os, hashlib, json

ROOT = "D:/Project/ra2-campaign-forge/lead"
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"

# Transcribed verbatim from the ask's 【全量载体扫描】 block (orchestrator-run).
ORCH = {
 "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": [123, 215],
 "ledger_appendix_20261108/_lad_tpl.md": [151],
 "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": [25],
 "ledger_bound_20261109/LEDGER_BOUND_VOLUME.md": [179, 196, 270, 288],
 "ledger_bound_20261109/_lb2_TEMPLATE.md": [152, 202],
 "ledger_bound_20261109/_lb_BOUND_VOLUME.md": [112, 129, 201, 216, 226],
 "minhard_check_20261109/MINHARD_SET_CHECK.md": [34, 75, 79, 94, 164, 207, 214, 238],
 "minhard_check_20261109/_mh_MINHARD_CHECK.md": [49, 52, 66, 125, 146, 187, 196, 197],
 "s604_refsync_20261109/S604_REFSYNC_DRAFT.md": [58, 65, 102, 108, 121, 127],
 "s604_refsync_20261109/_rs_REFSYNC_DRAFT.md": [26, 32, 36, 126, 131, 135, 144],
 "s604_refsync_full_20261109/S604_REFSYNC_FULL.md": [125, 127, 143, 206],
 "s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md": [130, 131, 132, 133, 206, 319],
 "s604_script_gap_20261109/S604_SCRIPT_GAP.md": [55],
 "s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": [58, 79, 94, 107, 150, 151],
 "s604_verdict_entry_20261109/_ve_DRAFT_S609.md": [22, 46, 53, 69, 70],
 "slowframe_r3_20261108/S604_GAP_RECHECK.md": [101],
 "slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md": [63],
 "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md": [91, 127],
}

def md_all():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        dd = 0 if rel == "." else rel.count("/") + 1
        for f in fn:
            if f.lower().endswith(".md"):
                p = os.path.join(dp, f)
                out.append((p, os.path.relpath(p, ROOT).replace("\\", "/"), dd))
    return out

if __name__ == "__main__":
    files = md_all()
    scoped = [x for x in files if x[2] <= 2]
    dirs_with_md = set()
    for p, rel, dd in scoped:
        dirs_with_md.add(os.path.dirname(rel).replace("\\", "/") if "/" in rel else ".")
    print("scoped md (dir-depth<=2) =", len(scoped))
    print("distinct dirs containing scoped md =", len(dirs_with_md),
          "(orchestrator reported dirs=288)")

    mine = {}
    for p, rel, dd in scoped:
        b = open(p, "rb").read()
        ls = b.decode("utf-8", "replace").splitlines()
        h = [i for i, L in enumerate(ls, 1) if N1 in L or N2 in L]
        if h:
            mine[rel] = h
    print("mine carrier files =", len(mine),
          " hit lines =", sum(len(v) for v in mine.values()))
    print("orch carrier files =", len(ORCH),
          " hit lines =", sum(len(v) for v in ORCH.values()))
    print()
    print("### per-file line-set diff (mine vs orchestrator)")
    for rel in sorted(set(mine) | set(ORCH)):
        a = set(mine.get(rel, [])); b = set(ORCH.get(rel, []))
        if a == b:
            print("  MATCH  %-85s %d lines" % (rel, len(a)))
        else:
            print("  DIFF   %-85s mine-only=%s orch-only=%s" %
                  (rel, sorted(a - b), sorted(b - a)))
    print()
    print("### per-line needle membership for _mh_MINHARD_CHECK.md (all hits)")
    p = os.path.join(ROOT, "minhard_check_20261109/_mh_MINHARD_CHECK.md")
    ls = open(p, "rb").read().decode("utf-8", "replace").splitlines()
    for i, L in enumerate(ls, 1):
        if N1 in L or N2 in L:
            print("%4d N1=%-5s N2=%-5s len=%4d | %s" %
                  (i, N1 in L, N2 in L, len(L), L[:95]))
    print()
    print("### all-depth carriers NOT in depth<=2 scope")
    for p, rel, dd in sorted(files, key=lambda x: x[1]):
        if dd <= 2: continue
        b = open(p, "rb").read()
        ls = b.decode("utf-8", "replace").splitlines()
        h = [i for i, L in enumerate(ls, 1) if N1 in L or N2 in L]
        if h:
            print("  dir-depth=%d %-100s bytes=%d lines=%s sha256=%s" %
                  (dd, rel, len(b), h, hashlib.sha256(b).hexdigest()[:16]))
