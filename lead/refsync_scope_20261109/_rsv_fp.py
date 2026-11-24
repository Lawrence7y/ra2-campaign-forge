"""_rsv_fp.py — INDEPENDENT reviewer: recompute the 14 baseline fingerprints.
No reliance on the author's scripts. Read-only.
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rsv_fp.py"
"""
import hashlib, os, sys

ROOT = r"D:/Project/ra2-campaign-forge"

BASELINE = {
"lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md": ("8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5", 61819, 366),
"lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md": ("d9b9c5acd0077060fe7ab0a064c263aa609881bfdc1736407d66d5eec890e1f3", 55331, 338),
"lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719, 237),
"lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": ("d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703, 41),
"lead/ledger_appendix_20261108/_lad_tpl.md": ("a2313396db2ad9535ea211daf027d3956d4c84fb9927a138403ff1ee72ec083a", 25723, 173),
"lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md": ("47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70", 70587, 439),
"lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md": ("7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43", 60272, 320),
"lead/ledger_bound_20261109/_lb2_TEMPLATE.md": ("ba1dc5cc9fb35dbc3010a470909079fdd9afbd6fbea9cccdaed82b6dc317a425", 42186, 353),
"lead/s604_attribution_20261108/S604_ATTRIBUTION.md": ("8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182, 196),
"lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md": ("7241026122978426838d6c8ccaa8ea3335fe6213adef6bae10ab9c7aa83df2f2", 17272, 129),
"lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": ("1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097, 171),
"lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980, 83),
"lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, 382),
"lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, 9758),
}

# line count convention: number of lines as counted by splitting raw bytes on b"\n"
# without adding a phantom trailing line. Report multiple conventions to be explicit.
def linecounts(b):
    by_splitlines = len(b.splitlines())
    by_count_nl = b.count(b"\n")
    by_count_nl_plus = by_count_nl + (0 if b.endswith(b"\n") else 1)
    return by_splitlines, by_count_nl, by_count_nl_plus

all_ok = True
print("=== INDEPENDENT FINGERPRINT RECOMPUTE (14 files) ===")
for rel, (exp_sha, exp_bytes, exp_lines) in BASELINE.items():
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    sha = hashlib.sha256(b).hexdigest()
    n = len(b)
    sl, nl, nlp = linecounts(b)
    sha_ok = (sha == exp_sha)
    by_ok = (n == exp_bytes)
    by_split_n = len(b.decode("utf-8").split("\n"))  # author's convention: LF count + 1
    ln_ok = (by_split_n == exp_lines)
    ok = sha_ok and by_ok and ln_ok
    all_ok &= ok
    print(f"{'OK  ' if ok else 'FAIL'} {rel}")
    print(f"      sha256 got={sha} exp={exp_sha} {'EQUAL' if sha_ok else 'NOT-EQUAL'}")
    print(f"      bytes  got={n} exp={exp_bytes} {'EQUAL' if by_ok else 'NOT-EQUAL'}")
    print(f"      lines  splitlines={sl} countLF={nl} LF+1={by_split_n} exp={exp_lines} {'EQUAL' if ln_ok else 'NOT-EQUAL'}")

# The bound object itself
p_bound = os.path.join(ROOT, "lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md")
with open(p_bound, "rb") as f:
    bb = f.read()
print()
print("=== BINDING TARGET (S604_REFSYNC_FULL.md) ===")
print("BINDING LINE: 被核对象 SHA256 = " + hashlib.sha256(bb).hexdigest() + "，字节数 = " + str(len(bb)))
print()
print("ALL_14_MATCH =", all_ok)
