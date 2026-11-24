# -*- coding: utf-8 -*-
# A类改文起草员：仅算 SHA256/字节数（hashlib），只读，不写任何被读文件。
import hashlib

paths = [
    "D:/Project/ra2-campaign-forge/lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
    "D:/Project/ra2-campaign-forge/lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md",
    "D:/Project/ra2-campaign-forge/lead/w2_samecause_20261109/W2_SAME_CAUSE.md",
    "D:/Project/ra2-campaign-forge/lead/handoff_pack_20261109/_hp_U8.md",
    "D:/Project/ra2-campaign-forge/lead/handoff_pack_20261109/_hp_U9.md",
    "D:/Project/ra2-campaign-forge/lead/handoff_pack_20261109/APPROVAL_PACK.md",
    "D:/Project/ra2-campaign-forge/lead/oldwording_sweep_20261109/_ow_SWEEP_REPORT_20261109.md",
    "D:/Project/ra2-campaign-forge/lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md",
]
for p in paths:
    with open(p, "rb") as f:
        b = f.read()
    print(len(b), hashlib.sha256(b).hexdigest(), p)
