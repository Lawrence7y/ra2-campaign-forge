# -*- coding: utf-8 -*-
# _acv_fp.py — A类改文复核员独立指纹实算（只读）
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    r"lead\matrix_reach_20261109\MATRIX_DEFECT_REACHABILITY.md",
    r"lead\matrix_reach_20261109\_mr_REACH_EVIDENCE_20261109.md",
    r"lead\w2_samecause_20261109\W2_SAME_CAUSE.md",
    r"lead\handoff_pack_20261109\APPROVAL_PACK.md",
    r"lead\handoff_pack_20261109\_hp_U8.md",
    r"lead\handoff_pack_20261109\_hp_U9.md",
    r"lead\oldwording_sweep_20261109\_ow_SWEEP_REPORT_20261109.md",
    r"lead\text_fix_unified_20261109\_uf_UNIFIED_FIX_LIST_20261109.md",
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    # 复核对象本身：
    r"lead\a_class_fix_20261109\_ac_A1A4A5_FIX_DRAFT_20261109.md",
    r"lead\a_class_fix_20261109\_ac_fp.py",
]
EXPECTED = {
    r"lead\matrix_reach_20261109\MATRIX_DEFECT_REACHABILITY.md": ("cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6", 27825),
    r"lead\matrix_reach_20261109\_mr_REACH_EVIDENCE_20261109.md": ("67d0fc90ceae277f23d43f80484da9445a6385994752a882d04a8517809f10e9", 20820),
    r"lead\w2_samecause_20261109\W2_SAME_CAUSE.md": ("75a0369b97f72f9d615ced86c580c6e63bfcce4f29de1c86bd74e8542aa5c895", 19552),
    r"lead\handoff_pack_20261109\APPROVAL_PACK.md": ("36ee1d6a0d93363ad6004543fa98fb4876e67ac6d7aecac33b3651c376b327f3", 40024),
    r"lead\handoff_pack_20261109\_hp_U8.md": ("c87ef405e0ee8ffeaccf96972287422c3ab23376b4fe2153ef6b44d2afe0079f", 3705),
    r"lead\handoff_pack_20261109\_hp_U9.md": ("90a566c84c5e8dfc1e1782c0fca560cbca8539d71ad06e5a5ca5cc8964a03630", 1806),
    r"lead\oldwording_sweep_20261109\_ow_SWEEP_REPORT_20261109.md": ("7378a419c896a05bafc10d4189769dc248dccb37c548f56d381d6d83209e16dc", 16900),
    r"lead\text_fix_unified_20261109\_uf_UNIFIED_FIX_LIST_20261109.md": ("441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923", 25095),
    r"lead\PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    r"lead\GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

ok = 0
for rel in FILES:
    p = os.path.join(BASE, rel)
    with open(p, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    n = len(data)
    if rel in EXPECTED:
        exp_sha, exp_n = EXPECTED[rel]
        match = "MATCH" if (sha == exp_sha and n == exp_n) else "MISMATCH"
        if match == "MATCH":
            ok += 1
        print("%s | %s | sha256=%s | bytes=%d | expected sha256=%s bytes=%d" % (match, rel, sha, n, exp_sha, exp_n))
    else:
        print("INFO | %s | sha256=%s | bytes=%d" % (rel, sha, n))
print("baseline match: %d/10" % ok)
