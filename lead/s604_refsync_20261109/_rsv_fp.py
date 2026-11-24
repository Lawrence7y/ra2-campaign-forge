# _rsv_fp.py — 独立复核：11 件被核件 + 被核草案 指纹实算（hashlib，绝对路径）
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    ("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
     "058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
    ("lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md",
     "1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097),
    ("lead/s604_script_hunt_20261109/S604_SCRIPT_HUNT.md",
     "f607b404c3b39f758d6f4c9bf54ed361d38d4d36bfae587748f5a112ec1a192c", 27347),
    ("lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md",
     "823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536),
    ("lead/s604_attribution_20261108/S604_ATTRIBUTION.md",
     "8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
     "593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740", 20271),
    ("lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
     "5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726", 19291),
    ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
     "724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
    ("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
     "d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    # 被核对象（修订回件草案，编排方基线外，申报 33776 B）
    ("lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md", None, None),
]

for rel, exp_sha, exp_bytes in FILES:
    p = os.path.join(BASE, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    n = len(data)
    if exp_sha is None:
        print("SUBJECT %s sha256=%s bytes=%d" % (rel, sha, n))
    else:
        ok = "MATCH" if (sha == exp_sha and n == exp_bytes) else "MISMATCH"
        print("%s %s sha256=%s bytes=%d expected_sha=%s expected_bytes=%d" % (ok, rel, sha, n, exp_sha, exp_bytes))
