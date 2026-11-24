# -*- coding: utf-8 -*-
# _mcv_fp.py -- independent fingerprint recompute (step 1)
# Runs: python -I -X utf8 <abs>/_mcv_fp.py
import hashlib, os, sys

ROOT = r"D:\Project\ra2-campaign-forge"

BASELINE = {
    "lead/r33e_merge_20261109/_re_linked.py": ("7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52", 19481),
    "lead/r33e_merge_20261109/_re_NOTES.md": ("388fe53e7636c61bbd981133229f6b4239ff9e771e4e2d69a54925edaa27d7c2", 7804),
    "lead/r33e_merge_20261109/R33E_MERGE.md": ("7f204882c0985e2708bd01110d720dec4aeaea47da37590462f15934d44a79c9", 26435),
    "lead/samedoc_link_20261109/_sl_link.py": ("a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5", 12475),
    "lead/r11_f2_fix_20261109/_f2_r11plus.py": ("83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_r9r12_20261109/_g9_gate.py": ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

allok = True
for rel, (want_sha, want_bytes) in BASELINE.items():
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        print("MISSING %s" % rel)
        allok = False
        continue
    with open(p, "rb") as f:
        data = f.read()
    got_sha = hashlib.sha256(data).hexdigest()
    got_bytes = len(data)
    ok = (got_sha == want_sha and got_bytes == want_bytes)
    if not ok:
        allok = False
    print("%s | sha=%s | bytes=%d | MATCH=%s" % (rel, got_sha, got_bytes, ok))
    print("   baseline sha=%s bytes=%d" % (want_sha, want_bytes))

print("ALL_NINE_MATCH = %s" % allok)
print("EXIT=%d" % (0 if allok else 1))
