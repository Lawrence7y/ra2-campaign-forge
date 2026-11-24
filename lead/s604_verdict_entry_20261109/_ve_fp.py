# -*- coding: utf-8 -*-
"""_ve_fp.py — 逐件自算 SHA256/字节数（hashlib）。只读；stdout 由 shell 重定向至写域。"""
import hashlib

D = "D:/Project/ra2-campaign-forge/lead/"

FILES = [
    D + "s604_script_hunt_20261109/S604_SCRIPT_HUNT.md",
    D + "s604_script_hunt_20261109/_sh_generator_512655.txt",
    D + "s604_script_hunt_20261109/_sh_gen512655_out.txt",
    D + "s604_script_hunt_20261109/_sh_gen512655_payload.py",
    D + "s604_exclusive_20261109/S604_EXCLUSIVITY.md",
    D + "s604_attribution_20261108/S604_ATTRIBUTION.md",
    D + "s604_script_gap_20261109/S604_SCRIPT_GAP.md",
    D + "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    D + "slowframe_r3_20261108/S604_GAP_RECHECK.md",
    D + "PENDING_DECISIONS.md",
    D + "GOAL_THREE_TARGETS_20261018.md",
]

lines = []
for p in FILES:
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
            n += len(chunk)
    lines.append("%s  %d  %s" % (h.hexdigest(), n, p))

print("\n".join(lines))
