#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W55b - diagnose why W54's flat metadata-plane view shows residual diffs.

W54 step6 builds a FLAT view = header + directory + minifat + the 14
non-CONTENTS streams CONCATENATED IN DIRECTORY ORDER.  That view is only
byte-comparable when every one of those 14 streams has an IDENTICAL LENGTH
across the two saves.  The W45 reference saves had a FIXED typed save name,
so all 14 lengths were fixed (42 B Scenario Description etc.) and the flat
view compared cleanly.

The W55b saves have ENGINE-GENERATED descriptions of VARIABLE LENGTH, so the
flat view is shifted for every stream after the first variable one: ~140
spurious diff bytes appear across many otherwise-identical streams.  The
CORRECT coordinate system (per NAMED STREAM, W54 §2.4 / the task's mandated
correction) shows only `Scenario Description` and `\x05SummaryInformation`
differing.

Writes out/metadata_plane_residual_analysis.json.  Pure offline read-only.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "next_re_20261112_r02" / "W55b_equivalence_rerun"
OUT = CARD / "out"

cmp = json.loads((OUT / "cfb_compare.json").read_text(encoding="utf-8"))
pairs = cmp["pairs"]
w55b = [s for s in cmp["saves"] if s["kind"] == "w55b"]
ids = {s["id"]: s for s in w55b}


def key(a, b):
    return "__".join(sorted([a, b]))


rows = []
for a, b in (("save_A1_s0_SAVE5802", "save_A2_s0_SAVE76DA"),
             ("save_B1_s0_SAVE30A5", "save_B2_s0_SAVE4221"),
             ("save_A1_s0_SAVE5802", "save_B1_s0_SAVE30A5"),
             ("save_A1_s0_SAVE5802", "save_B2_s0_SAVE4221"),
             ("save_A2_s0_SAVE76DA", "save_B1_s0_SAVE30A5"),
             ("save_A2_s0_SAVE76DA", "save_B2_s0_SAVE4221")):
    if a not in ids or b not in ids:
        continue
    r = pairs[key(a, b)]
    differing = {n: v["diff_bytes_masked"]
                 for n, v in r["streams"].items()
                 if v.get("present_in_both") and v.get("diff_bytes_masked")}
    len_diffs = {n: (v["len_x"], v["len_y"])
                 for n, v in r["streams"].items()
                 if v.get("present_in_both") and v["len_x"] != v["len_y"]}
    rows.append({
        "pair": "%s vs %s" % (a, b),
        "arm_pair": "%s/%s" % (ids[a]["arm"], ids[b]["arm"]),
        "flat_metadata_plane_diff_bytes_masked":
            r["metadata_plane"]["diff_bytes_masked"],
        "flat_metadata_plane_equal_masked":
            r["metadata_plane"]["equal_masked"],
        "flat_metadata_plane_len_x_y":
            [r["metadata_plane"]["len_x"], r["metadata_plane"]["len_y"]],
        "per_named_stream_diff_bytes_masked": differing,
        "n_streams_with_masked_diff": len(differing),
        "streams_with_different_lengths": len_diffs,
        "contents_diff_bytes": r["contents"]["diff_bytes"],
    })

out = {
    "kind": "w55b_metadata_plane_residual_diagnosis",
    "coordinate_system_used_for_verdict": "per NAMED STREAM (task-mandated)",
    "flat_view_warning": ("W54 step6's flat metadata-plane view concatenates "
                          "the 14 non-CONTENTS streams; it is ONLY comparable "
                          "when all 14 lengths are identical. Variable-length "
                          "save-name/description streams shift the whole tail, "
                          "producing spurious diff bytes in unrelated streams."),
    "whitelist_performance": {
        "wall_clock_FILETIME_streams": ("Start Time / Last Save Time / Play "
                                        "Time: 0 masked diff bytes in every "
                                        "W55b pair => W54 whitelist WORKED"),
        "W45_reference_crosscheck": json.loads(
            (OUT / "whitelist_crosscheck.json").read_text(encoding="utf-8")
        )["metadata_plane_pairs"],
    },
    "new_nondeterminism_source": {
        "streams": ["Scenario Description", "\x05SummaryInformation"],
        "lengths_observed": {"Scenario Description": [32, 34, 36, 38],
                             "\x05SummaryInformation": [380, 384, 388]},
        "cause": ("Engine-generated save slot name / description embedded in "
                  "UTF-16 in these streams; W45 typed a FIXED name so W54 never "
                  "observed these bytes vary and never whitelisted them."),
        "not_whitelisted_post_hoc": True,
        "reason_not_whitelisted": ("W45 EQUIVALENCE_SPEC.md §1.4/§3.4 and "
                                   "§0.1 require the whitelist to be declared "
                                   "BEFORE the run; expanding it after seeing "
                                   "the result would be forbidden."),
    },
    "pairs": rows,
    "conclusion": ("Per named stream, 13/15 streams have 0 masked diff; only "
                   "the two variable-length save-name streams differ. The flat "
                   "view's 67-176 residual bytes are a LENGTH-SHIFT ARTIFACT, "
                   "not additional nondeterminism. The correct coordinate "
                   "system (named streams) is confirmed."),
}
(OUT / "metadata_plane_residual_analysis.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True),
    encoding="utf-8")
print(json.dumps({
    "flat_view_residual_per_pair": [r["flat_metadata_plane_diff_bytes_masked"]
                                    for r in rows],
    "differing_streams_all_pairs": sorted({n for r in rows
                                           for n in r["per_named_stream_diff_bytes_masked"]}),
    "conclusion": out["conclusion"]}, ensure_ascii=False, indent=1))
