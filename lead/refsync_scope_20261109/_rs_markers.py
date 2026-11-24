# -*- coding: utf-8 -*-
"""_rs_markers.py — dump all marker-ish lines in the 18 carrier files so the
block detector can be designed from measured text, not guessed. Read-only.
"""
import os, re

ROOT = "D:/Project/ra2-campaign-forge/lead"

FILES = [
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
]

PAT = re.compile(r"(逐字转录开始|逐字转录结束|逐字照抄|↓↓↓|↑↑↑|草案正文|从这里开始|可整段复制追加|@@BODY|标记行|入账正文|正文区)")

if __name__ == "__main__":
    for rel in FILES:
        ls = open(os.path.join(ROOT, rel), "rb").read().decode("utf-8", "replace").splitlines()
        hits = [(i, L) for i, L in enumerate(ls, 1) if PAT.search(L)]
        print("=" * 90)
        print(rel, "lines=", len(ls), "marker-ish=", len(hits))
        for i, L in hits[:70]:
            print("%4d | %s" % (i, L[:170]))
