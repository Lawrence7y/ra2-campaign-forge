# -*- coding: utf-8 -*-
"""_rs_final.py — Step 2/3/5 consolidated evidence:
 13-file list vs full carrier set (diff + intersection), per-file verdict,
 two-ledger §605-609 / §604 / needle hits, verbatim §607 vs §609 conflict text,
 full fingerprint table + binding line. Read-only.
"""
import os, hashlib, re

ROOT = "D:/Project/ra2-campaign-forge/lead"
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"

THIRTEEN = [
 "slowframe_r3_20261108/S604_GAP_RECHECK.md",
 "s604_attribution_20261108/S604_ATTRIBUTION.md",
 "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
 "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
 "ledger_appendix_20261108/_lad_tpl.md",
 "s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "s604_script_gap_20261109/_sg_FINDINGS.md",
 "s604_exclusive_20261109/S604_EXCLUSIVITY.md",
 "s604_exclusive_20261109/_ex_EXCLUSIVITY.md",
 "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
 "direction_ruling_20261108/RULING_DIRECTION.md",
 "direction_ruling_20261108/_dr_RULING.md",
]

# orchestrator exact 18-carrier map
ORCH = {
 "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "ledger_appendix_20261108/_lad_tpl.md",
 "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
 "ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
 "ledger_bound_20261109/_lb2_TEMPLATE.md",
 "ledger_bound_20261109/_lb_BOUND_VOLUME.md",
 "minhard_check_20261109/MINHARD_SET_CHECK.md",
 "minhard_check_20261109/_mh_MINHARD_CHECK.md",
 "s604_refsync_20261109/S604_REFSYNC_DRAFT.md",
 "s604_refsync_20261109/_rs_REFSYNC_DRAFT.md",
 "s604_refsync_full_20261109/S604_REFSYNC_FULL.md",
 "s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md",
 "s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md",
 "s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
 "slowframe_r3_20261108/S604_GAP_RECHECK.md",
 "slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md",
 "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
}

def load(rel):
    b = open(os.path.join(ROOT, rel), "rb").read()
    return b, b.decode("utf-8", "replace").splitlines()

def fp(b): return hashlib.sha256(b).hexdigest()

if __name__ == "__main__":
    T = set(THIRTEEN)
    print("### (Step 2c) 13-file scope vs 18-carrier scope: set algebra")
    print("13-file count =", len(T), " 18-carrier count =", len(ORCH))
    print("intersection (%d):" % len(T & ORCH))
    for r in sorted(T & ORCH): print("   BOTH  ", r)
    print("13-only (%d) [in 43-list but NOT a carrier of these 2 needles]:" % len(T - ORCH))
    for r in sorted(T - ORCH): print("   13ONLY", r)
    print("CARRIER-only (%d) [MISSED CARRIERS = full minus 13]:" % len(ORCH - T))
    for r in sorted(ORCH - T): print("   MISSED", r)
    print()
    print("### (Step 5d) two ledgers: are §605-§609 already recorded?")
    for rel in ["GOAL_THREE_TARGETS_20261018.md", "PENDING_DECISIONS.md"]:
        b, ls = load(rel)
        pats = [r"^##\s*§(?:60[5-9]|610)\b", r"§60[5-9]", r"§610",
                r"码形定谳", r"dur 字典", r"512655",
                N1, N2, r"^##\s*§604\b"]
        print("FILE", rel, "bytes", len(b), "sha256", fp(b), "lines", len(ls))
        for p in pats:
            hits = [i for i, L in enumerate(ls, 1) if re.search(p, L)]
            print("   %-28s hits=%d  %s" % (p, len(hits), hits[:12]))
        hdr = [(i, L) for i, L in enumerate(ls, 1) if re.match(r"^##\s*§", L)]
        print("   last 6 '^## §' headers:", hdr[-6:])
    print()
    print("### (Step 5c) verbatim §607 boundary line vs §609 negation line")
    _, d3 = load("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md")
    _, ve = load("s604_verdict_entry_20261109/_ve_DRAFT_S609.md")
    print("§607 draft :25 =", d3[24])
    print("§609 draft :22 =", ve[21])
    print("§607 :25 in §609 block 11..27? ", 11 <= 25 <= 27)
    print("N2 in §607 line? ", N2 in d3[24], " N2 in §609 line? ", N2 in ve[21])
    print()
    print("### (Step 0) full fingerprint table (hashlib, this session)")
    FP_TARGETS = [
      "s604_refsync_full_20261109/S604_REFSYNC_FULL.md",
      "s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md",
      "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
      "ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
      "ledger_appendix_20261108/_lad_tpl.md",
      "ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
      "ledger_bound_20261109/_lb_BOUND_VOLUME.md",
      "ledger_bound_20261109/_lb2_TEMPLATE.md",
      "s604_attribution_20261108/S604_ATTRIBUTION.md",
      "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
      "s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md",
      "s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
      "PENDING_DECISIONS.md", "GOAL_THREE_TARGETS_20261018.md",
    ]
    for rel in FP_TARGETS:
        b, ls = load(rel)
        print("%-90s sha256=%s bytes=%d lines=%d" %
              (rel, fp(b), len(b), len(ls)))
    print()
    bb, _ = load("s604_refsync_full_20261109/S604_REFSYNC_FULL.md")
    print("BINDING LINE:")
    print("被核对象 SHA256 = %s，字节数 = %d" % (fp(bb), len(bb)))
