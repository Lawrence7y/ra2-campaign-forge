# -*- coding: utf-8 -*-
# 独立复核 ③（v2 追加）：打印各候选文件中过时行的上下文与所在块边界
import os
ROOT = r"D:\Project\ra2-campaign-forge"
CAND = {
 "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md": [179, 196, 270, 288],
 "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md": [112, 129, 201, 216, 226],
 "lead/ledger_bound_20261109/_lb2_TEMPLATE.md": [152, 154, 158, 160, 161, 202],
 "lead/ledger_bound_20261109/_lb_build.py": [175, 223, 249],
 "lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md": [102, 108, 121, 127],
 "lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md": [131, 135, 144],
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": [11, 31, 110, 123, 125, 179, 209, 211, 215, 222],
 "lead/ledger_appendix_20261108/_lad_tpl.md": [87, 89, 110, 115, 145, 147, 151, 158, 160],
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": [1, 11, 25, 28],
 "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": [1, 136, 169, 171],
 "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md": [91, 127],
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": [1, 22, 46, 69, 70],
 "lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": [79, 101, 107, 108, 151],
}
for rel, lns in CAND.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    L = open(p, "r", encoding="utf-8", newline="").read().split("\n")
    print(f"===== {rel} (total_lines={len(L)}) =====")
    for ln in lns:
        if 1 <= ln <= len(L):
            print(f"  [{ln}] {L[ln-1]!r}")
    print()
