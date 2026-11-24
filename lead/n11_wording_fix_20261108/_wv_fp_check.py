# -*- coding: utf-8 -*-
# _wv_fp_check.py — 独立复核员指纹实算（只读）
import hashlib, os
BASE = r"D:\Project\ra2-campaign-forge"
FILES = {
    "_ps  规格(被核对象)": r"lead\n11_protocol_spec_20261108\_ps_N11_MIN_OBS_PROTOCOL_SPEC.md",
    "OBS  规格":          r"lead\n11_protocol_spec_20261108\OBSERVATION_PROTOCOL_SPEC.md",
    "DIMMAP":             r"lead\n11_dimmap_20261108\DIM_COLUMN_MAPPING.md",
    "DM":                 r"lead\n11_dimmap_20261108\_dm_DIM_MAP_20261108.md",
    "RULING":             r"lead\direction_ruling_20261108\RULING_DIRECTION.md",
    "NEXTSTEP":           r"lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
    "PERF":               r"lead\perf_repair_n11_20261108\PERF_REPAIR_HANDOFF.md",
    "PENDING":            r"lead\PENDING_DECISIONS.md",
    "GOAL":               r"lead\GOAL_THREE_TARGETS_20261018.md",
    "DRAFT(唯一写入)":     r"lead\n11_wording_fix_20261108\_wf_wording_fix_draft_20261109.md",
}
for k, rel in FILES.items():
    p = os.path.join(BASE, rel)
    if not os.path.isfile(p):
        print(f"{k}\t{rel}\tMISSING")
        continue
    b = open(p, "rb").read()
    print(f"{k}\t{rel}\tsha256={hashlib.sha256(b).hexdigest()}\tbytes={len(b)}")
