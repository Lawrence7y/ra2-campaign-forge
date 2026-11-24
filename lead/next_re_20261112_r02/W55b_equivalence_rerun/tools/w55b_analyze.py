#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W55b - offline verdict: three-way B-line equivalence judgement.

Reads (all in W55b_equivalence_rerun/out/):
  dual_track_results.json   real-machine per-trip records
  cfb_compare.json          CFB named-stream pair comparisons
  stream_matrix.json        per-save table
  contents_structure.json   CONTENTS structural-parse attempt
  config_restore_post.json  config / real-dir restore self-proof

Applies the PRE-DECLARED criteria in ALIGNMENT_STRATEGY.md §5 (fixed BEFORE
the real machine ran; nothing is adjusted from the results).  Writes
out/analysis.json.  Pure offline, no game, writes only W55b out/.

Verdict is exactly one of: 等价 / 不等价 / 仍不可判
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "next_re_20261112_r02" / "W55b_equivalence_rerun"
OUT = CARD / "out"

FRAME_ALIGN_TOL = 1        # pre-declared, spec §3.4
GATE_ACCEPT_BAND = 16      # pre-declared
K_EXPECTED_BATTLE_DELTA = 1


def load(name, default=None):
    p = OUT / name
    if not p.is_file():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def pair_key(a, b):
    return "__".join(sorted([a, b]))


def main():
    runs = load("dual_track_results.json", {}) or {}
    # dual_track_results.json is rewritten per --phase run invocation; merge
    # every <tag>_result.json so no trip (esp. the A1 pilot) is lost.
    for rp in sorted(OUT.glob("*_result.json")):
        if rp.name == "dual_track_results.json":
            continue
        try:
            runs.setdefault(rp.stem.replace("_result", ""),
                            json.loads(rp.read_text(encoding="utf-8")))
        except Exception:
            pass
    # persist the merged view as the authoritative aggregate evidence
    (OUT / "dual_track_results.json").write_text(
        json.dumps(runs, ensure_ascii=False, indent=1, sort_keys=True,
                   default=str), encoding="utf-8")
    cmp = load("cfb_compare.json", None)
    matrix = load("stream_matrix.json", None)
    structure = load("contents_structure.json", []) or []
    restore = load("config_restore_post.json", None)
    crosscheck = load("whitelist_crosscheck.json", None)

    out = {
        "kind": "w55b_equivalence_analysis_v2",
        "spec": "ALIGNMENT_STRATEGY.md §5 / W45 EQUIVALENCE_SPEC.md §2.4,§3.4,§3.7 / W54 §5.3",
        "thresholds_pre_declared": {
            "frame_align_tol_ticks": FRAME_ALIGN_TOL,
            "gate_accept_band": GATE_ACCEPT_BAND,
            "k_expected_battle_delta": K_EXPECTED_BATTLE_DELTA},
        "inputs_present": {
            "dual_track_results": bool(runs), "cfb_compare": cmp is not None,
            "stream_matrix": matrix is not None,
            "contents_structure": bool(structure),
            "config_restore_post": restore is not None,
            "whitelist_crosscheck": crosscheck is not None},
    }

    # ------------------------------------------------------------ trips summary
    trips = {}
    for tag, r in (runs.items() if isinstance(runs, dict) else []):
        if not isinstance(r, dict):
            continue
        al = r.get("alignment") or {}
        trips[tag] = {
            "arm": r.get("arm"), "phase_reached": r.get("phase_reached"),
            "errors": r.get("errors"), "gate": r.get("frame_gate"),
            "alignment": al,
            "n_saves": len(r.get("saves") or []),
            "saves": [{"name": s.get("name"), "size": s.get("size"),
                       "sha256_8": (s.get("sha256") or "")[:8],
                       "frame_frozen": s.get("frame_frozen"),
                       "attempt": s.get("attempt"),
                       "aligned_to_first": s.get("aligned_to_first")}
                      for s in (r.get("saves") or [])],
            "restore_all_match": all(x.get("match") for x in
                                     (r.get("restore_configs") or []))
                                 if r.get("restore_configs") else None,
            "drops_removed": r.get("drops_removed"),
        }
    out["trips"] = trips

    # ------------------------------------------------------------ 1) alignment grouping
    saves = []
    if cmp:
        for s in cmp.get("saves", []):
            if s.get("kind") == "w55b":
                saves.append(s)
    frame_vals = sorted({s["frame_frozen"] for s in saves
                         if s.get("frame_frozen") is not None})
    # cluster by consecutive gap <= FRAME_ALIGN_TOL (transitive)
    clusters = []
    for v in frame_vals:
        if clusters and v - clusters[-1][-1] <= FRAME_ALIGN_TOL:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    clusters.sort(key=lambda c: (-len(c), c[0]))
    main_group = clusters[0] if clusters else []
    group_set = set(main_group)
    aligned = [s for s in saves if s.get("frame_frozen") in group_set]
    aligned_ids = {s["id"] for s in aligned}
    unaligned = [{"id": s["id"], "frame_frozen": s.get("frame_frozen"),
                  "reason": "frozen frame outside main aligned cluster"}
                 for s in saves if s["id"] not in aligned_ids]
    spread = (max(frame_vals) - min(frame_vals)) if frame_vals else None
    out["alignment"] = {
        "strategy": "frozen-frame value as alignment key (ALIGNMENT_STRATEGY.md §2.2)",
        "frame_frozen_values_raw": frame_vals,
        "max_minus_min_spread_ticks": spread,
        "align_tol_ticks": FRAME_ALIGN_TOL,
        "clusters": clusters,
        "main_aligned_group_frames": main_group,
        "n_aligned_saves": len(aligned),
        "n_unaligned_saves": len(unaligned),
        "unaligned_excluded": unaligned,
        "achieved_precision": ("max pairwise Δframe = %s tick(s) within main group"
                               % (max(main_group) - min(main_group)
                                  if main_group else None)),
    }

    # ------------------------------------------------------------ 2) precondition 2
    by_arm = {"A": [], "B": []}
    for s in aligned:
        if s.get("arm") in by_arm:
            by_arm[s["arm"]].append(s)
    p2_ok = (len(by_arm["A"]) >= 2 and len(by_arm["B"]) >= 2
             and len(aligned) >= 4)
    # distinguish cross-trip (different tag) from in-trip (same tag, diff attempt)
    def is_cross_trip(x, y):
        return x.get("tag") != y.get("tag")

    out["same_frame_same_arm_saves"] = {
        "A": [s["id"] for s in by_arm["A"]],
        "B": [s["id"] for s in by_arm["B"]],
        "total_aligned": len(aligned),
        "required_per_arm": 2, "required_total": 4,
        "achieved": bool(p2_ok),
    }

    # ------------------------------------------------------------ lookup pair results
    pairs = (cmp or {}).get("pairs", {})

    def pair_res(a, b):
        return pairs.get(pair_key(a, b))

    def contents_diff(a, b):
        r = pair_res(a, b)
        if not r:
            return None
        c = r["contents"]
        return {"diff_bytes": c["diff_bytes"], "equal": c["equal"],
                "sha256_x": c["sha256_x"], "sha256_y": c["sha256_y"],
                "len_x": c["len_x"], "len_y": c["len_y"]}

    def meta_diff(a, b):
        r = pair_res(a, b)
        return r["metadata_plane"] if r else None

    # ------------------------------------------------------------ N: same-frame same-arm
    N_rows = []
    for arm in ("A", "B"):
        for x, y in combinations(by_arm[arm], 2):
            cd = contents_diff(x["id"], y["id"])
            md = meta_diff(x["id"], y["id"])
            N_rows.append({
                "arm": arm, "x": x["id"], "y": y["id"],
                "kind": "cross_trip" if is_cross_trip(x, y) else "in_trip",
                "frame_frozen_x": x.get("frame_frozen"),
                "frame_frozen_y": y.get("frame_frozen"),
                "contents_diff_bytes": cd["diff_bytes"] if cd else None,
                "contents_equal": cd["equal"] if cd else None,
                "metadata_plane_diff_bytes_masked":
                    md["diff_bytes_masked"] if md else None,
                "metadata_plane_equal_masked":
                    md["equal_masked"] if md else None,
            })
    cross_N = [r for r in N_rows if r["kind"] == "cross_trip"]
    in_N = [r for r in N_rows if r["kind"] == "in_trip"]
    N_A = next((r["contents_diff_bytes"] for r in cross_N
                if r["arm"] == "A" and r["contents_diff_bytes"] is not None), None)
    N_B = next((r["contents_diff_bytes"] for r in cross_N
                if r["arm"] == "B" and r["contents_diff_bytes"] is not None), None)
    N_values = [v for v in (N_A, N_B) if v is not None]
    N_primary = max(N_values) if N_values else None   # conservative noise band
    N_stable = (len(N_values) >= 2 and N_A == N_B)
    meta_residual = [r["metadata_plane_diff_bytes_masked"] for r in N_rows
                     if r["metadata_plane_diff_bytes_masked"] is not None]
    out["noise_baseline_N"] = {
        "definition": "CONTENTS rectified diff bytes of same-frame same-ARM "
                      "CROSS-TRIP pairs (W45 §2.4: N = A1 vs A2); conservative "
                      "noise band = max(N_A, N_B)",
        "cross_trip_pairs": cross_N,
        "in_trip_pairs": in_N,
        "N_A_arm": N_A, "N_B_arm": N_B,
        "N_primary_diff_bytes": N_primary,
        "N_stable": bool(N_stable),
        "N_stability_note": ("N_A=%s, N_B=%s: both O(1.3M) differing bytes, "
                             "i.e. two independent runs of the SAME arm at the "
                             "SAME frozen frame still produce almost completely "
                             "different CONTENTS streams" % (N_A, N_B)),
        "in_trip_diff_bytes": [r["contents_diff_bytes"] for r in in_N],
        "metadata_plane_all_zero_masked": all(v == 0 for v in meta_residual)
        if meta_residual else None,
        "metadata_plane_masked_diff_bytes_per_same_arm_pair": meta_residual,
        "metadata_plane_residual_note": (
            "W54 whitelist leaves 67-176 UNMASKED differing bytes in the "
            "metadata plane for the W55b saves, all inside the variable-length "
            "`Scenario Description` and `\\x05SummaryInformation` streams "
            "(engine-generated save name/description, lengths 32-38 / 380-388). "
            "W45 used a FIXED typed save name so those bytes never varied and "
            "W54 never whitelisted them. NOT whitelisted post-hoc (spec §3.4 / "
            "§0.1 forbid after-the-fact threshold/whitelist changes); reported "
            "as a NEW a-priori-declared-elsewhere nondeterminism source."),
    }

    # ------------------------------------------------------------ D: same-frame cross-arm
    D_rows = []
    for x in by_arm["A"]:
        for y in by_arm["B"]:
            cd = contents_diff(x["id"], y["id"])
            md = meta_diff(x["id"], y["id"])
            D_rows.append({
                "x": x["id"], "y": y["id"],
                "frame_frozen_x": x.get("frame_frozen"),
                "frame_frozen_y": y.get("frame_frozen"),
                "contents_diff_bytes": cd["diff_bytes"] if cd else None,
                "contents_equal": cd["equal"] if cd else None,
                "metadata_plane_diff_bytes_masked":
                    md["diff_bytes_masked"] if md else None,
            })
    D_values = [r["contents_diff_bytes"] for r in D_rows
                if r["contents_diff_bytes"] is not None]
    D_max = max(D_values) if D_values else None
    D_min = min(D_values) if D_values else None
    out["cross_arm_D"] = {
        "definition": "CONTENTS rectified diff bytes for same-frame CROSS-ARM pairs",
        "pairs": D_rows, "D_max_diff_bytes": D_max, "D_min_diff_bytes": D_min,
    }

    # ------------------------------------------------------------ 4 preconditions
    structure_parsed = bool(structure) and any(
        s.get("structure_parsed") for s in structure)
    fallback = structure[0].get("fallback") if structure else None
    p1 = bool(main_group and len(aligned) >= 2
              and len({s.get("arm") for s in aligned}) >= 2
              and (max(main_group) - min(main_group)) <= FRAME_ALIGN_TOL)
    p3 = bool(cmp) and bool(structure)
    p4 = bool(cmp) and cmp.get("coordinate_space") == "cfb_named_stream"
    preconditions = {
        "P1_frame_gate_aligned_saves": {
            "status": "达成" if p1 else ("部分" if main_group else "未达成"),
            "detail": ("frame gate implemented; achieved main group %s, "
                       "%d aligned saves, max pairwise Δ=%s tick(s), tol=%d"
                       % (main_group, len(aligned),
                          (max(main_group) - min(main_group)) if main_group else None,
                          FRAME_ALIGN_TOL)),
            "raw_frozen_values": frame_vals},
        "P2_same_frame_same_arm_supplement": {
            "status": "达成" if p2_ok else ("部分" if any(by_arm.values()) else "未达成"),
            "detail": ("A=%d B=%d aligned saves (need >=2 per arm, >=4 total)"
                       % (len(by_arm["A"]), len(by_arm["B"]))),
        },
        "P3_contents_comparison_criterion": {
            "status": ("达成" if structure_parsed else "部分") if p3 else "未达成",
            "detail": ("structural parse attempted on %d CONTENTS streams; "
                       "structure_parsed=%s; fallback=%s (task explicitly "
                       "permits rectified whole-stream sha256 when structure "
                       "cannot be parsed)" % (len(structure), structure_parsed,
                                              fallback)),
        },
        "P4_cfb_named_stream_comparison": {
            "status": "达成" if p4 else "未达成",
            "detail": ("FAT/DIFAT/miniFAT excluded by construction; all "
                       "comparisons by named stream; whitelist masked in "
                       "CFB-logical coordinates; W54 4-reference validation "
                       "reproduced = %s"
                       % ({k: v["equal_masked"] for k, v in
                          (crosscheck or {}).get("metadata_plane_pairs", {}).items()})),
        },
    }
    out["w54_preconditions"] = preconditions

    # ------------------------------------------------------------ verdict
    all_p = all(v["status"] == "达成" for v in preconditions.values())
    reasons = []
    if not saves:
        verdict = "仍不可判"
        reasons.append("no W55b .SAV evidence on disk")
    elif not p1:
        verdict = "仍不可判"
        reasons.append("frame alignment > %d tick or no multi-arm aligned group" %
                       FRAME_ALIGN_TOL)
    elif not p2_ok:
        verdict = "仍不可判"
        reasons.append("same-frame same-arm sample requirement not met "
                       "(A=%d B=%d)" % (len(by_arm["A"]), len(by_arm["B"])))
    elif N_primary is None or D_max is None:
        verdict = "仍不可判"
        reasons.append("N or D could not be computed from the pair matrix")
    elif N_primary == 0 and D_max == 0:
        verdict = "等价"
        reasons.append("frame-aligned; same-frame same-arm N=0 (CONTENTS "
                       "rectified sha equal, masked metadata plane 0 diff); "
                       "cross-arm D=0. Equivalence holds ONLY within the "
                       "declared scope (this image/machine/config, single "
                       "player, official SOV01 path, this time window).")
    elif N_primary == 0 and D_max > 0 and D_min > 0:
        verdict = "不等价"
        reasons.append("frame-aligned; same-arm noise baseline N=0 yet every "
                       "cross-arm pair has D=%d > N=0; reproducible across %d "
                       "cross-arm pairs" % (D_max, len(D_rows)))
    elif N_primary > 0 and D_min > N_primary:
        verdict = "不等价"
        reasons.append("D_min=%d > N=%d (conservative noise band) across %d "
                       "cross-arm pairs" % (D_min, N_primary, len(D_rows)))
    else:
        verdict = "仍不可判"
        reasons.append("D_min=%d .. D_max=%d does NOT exceed N=%s => the "
                       "cross-arm difference lies INSIDE the same-arm noise "
                       "band (W45 §2.4: only D>N may be attributed to the "
                       "package). Frame alignment alone did not make CONTENTS "
                       "deterministic." % (D_min, D_max, N_primary))
        if not N_stable:
            reasons.append("N itself is not a fixed constant: N_A=%s vs "
                           "N_B=%s (both O(1.3M) bytes)" % (N_A, N_B))
        if meta_residual and any(v > 0 for v in meta_residual):
            reasons.append("W54 whitelist leaves %s unmasked metadata-plane "
                           "bytes per same-arm pair (variable save-name / "
                           "SummaryInformation streams); not whitelisted "
                           "post-hoc" % meta_residual)
    # hard overrides from spec §3.7: any unmet precondition => 仍不可判
    if not all_p and verdict in ("等价", "不等价"):
        verdict = "仍不可判"
        reasons.append("W45 §3.7: at least one W54 precondition is not fully "
                       "achieved => total verdict cannot be 等价/不等价")
    # real-machine / restore gate
    if runs and any(t.get("errors") for t in trips.values()):
        reasons.append("note: %d trip(s) recorded errors (see trips)"
                       % sum(1 for t in trips.values() if t.get("errors")))
    if restore is not None:
        out["restore_self_proof"] = {
            "identical_tree": restore.get("identical_tree"),
            "all_config_byte_identical_to_baseline":
                restore.get("all_config_byte_identical_to_baseline"),
            "all_trip_restore_match": restore.get("all_trip_restore_match"),
        }
    out["verdict"] = verdict
    out["verdict_reasons"] = reasons
    out["first_divergent_sample"] = None
    if verdict == "不等价" and D_rows:
        first = min((r for r in D_rows if r["contents_diff_bytes"]),
                    key=lambda r: r["contents_diff_bytes"], default=None)
        if first:
            out["first_divergent_sample"] = {
                "quantity": "CONTENTS rectified stream (CFB named stream)",
                "x": first["x"], "y": first["y"],
                "frame": first["frame_frozen_x"],
                "A_value": "sha256 of CONTENTS of %s" % first["x"],
                "B_value": "sha256 of CONTENTS of %s" % first["y"],
                "first_diff_byte_offset_in_CONTENTS": None,
                "diff_bytes": first["contents_diff_bytes"],
                "noise_band_N": N_primary,
                "note": "frame-aligned by frozen-frame key; D>N",
            }

    # ---- secondary W45 comparables (context only; not used to force verdict) ----
    out["secondary_w45_comparables"] = {
        "trips_phase_reached": {t: v.get("phase_reached") for t, v in trips.items()},
        "trips_errors": {t: v.get("errors") for t, v in trips.items()},
        "verify_gate": {t: {"verify_pre_rc": (runs.get(t) or {}).get("verify_pre_rc"),
                            "verify_post_rc": (runs.get(t) or {}).get("verify_post_rc")}
                        for t in trips},
        "note": ("本卡唯一新增判据是「存档字节」的 CFB stream 级、frame 对齐"
                 "版本；W45 的定时器/Esc/RPM/verify 读数沿用不改，仅作上下文。"),
    }

    (OUT / "analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    print(json.dumps({
        "verdict": verdict, "reasons": reasons,
        "preconditions": {k: v["status"] for k, v in preconditions.items()},
        "frame_frozen_values": frame_vals, "main_group": main_group,
        "n_aligned": len(aligned), "N_primary": N_primary,
        "N_stable": N_stable, "D_min": D_min, "D_max": D_max,
        "structure_parsed": structure_parsed,
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
