#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W65 reporting helper (NO imports from other cards).

* merges A1+A2 -> A_merged.ndjson, B1+B2 -> B_merged.ndjson (SPEC §2.2)
* descriptive per-trip statistics for LIVE_RESULT.md
* N_ks for BOTH arms, using the EXACT two-sample KS formula from the FROZEN
  tool_b_stats.py:111-127 (verbatim, re-implemented here so the delivered
  tool is never imported or modified).  The tool itself reports N_ks(A) only;
  N_ks(B) here is a clearly-labelled supplementary re-computation.
"""
from __future__ import annotations
import json
import math
import collections
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "next_re_20261112_r02" / "W65_bline_live_collect"
OUT = CARD / "out"
TAGS = ("A1", "A2", "B1", "B2")
FIELDS = ("t", "frame", "map_name", "stage_idx", "end_of_game",
          "skip_map_select", "battle_idx", "ui_controls")


def load(tag):
    rows = []
    p = OUT / (tag + ".ndjson")
    for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        missing = [k for k in FIELDS if k not in o]
        if missing:
            raise ValueError("%s:%d missing %r" % (p, ln, missing))
        rows.append(o)
    return rows


def dframes(rows):
    return [int(rows[i]["frame"]) - int(rows[i - 1]["frame"])
            for i in range(1, len(rows))]


def ks_statistic(a, b) -> float:
    """VERBATIM from FROZEN tool_b_stats.py:111-127 (two-sample KS)."""
    a = sorted(float(v) for v in a)
    b = sorted(float(v) for v in b)
    if not a or not b:
        return float("nan")
    grid = sorted(set(a) | set(b))
    i = j = 0
    d = 0.0
    na, nb = len(a), len(b)
    for v in grid:
        while i < na and a[i] <= v:
            i += 1
        while j < nb and b[j] <= v:
            j += 1
        d = max(d, abs(i / na - j / nb))
    return d


def quantile(samples, qs):
    x = sorted(float(v) for v in samples)
    if not x:
        return [float("nan")] * len(qs)
    out = []
    for q in qs:
        pos = (len(x) - 1) * q
        lo, hi = int(math.floor(pos)), int(math.ceil(pos))
        out.append(x[lo] if lo == hi else x[lo] + (pos - lo) * (x[hi] - x[lo]))
    return out


def cv(samples):
    x = [float(v) for v in samples]
    if not x:
        return float("nan")
    m = sum(x) / len(x)
    if m == 0:
        return float("inf")
    return math.sqrt(sum((v - m) ** 2 for v in x) / len(x)) / m


def jaccard(a, b):
    sa, sb = set(int(x) for x in a), set(int(x) for x in b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def jaccard_mean(ra, rb):
    n = min(len(ra), len(rb))
    return sum(jaccard(ra[i]["ui_controls"], rb[i]["ui_controls"])
               for i in range(n)) / n if n else 0.0


def main():
    rows = {t: load(t) for t in TAGS}
    # merged arms (SPEC §2.2: A = A1 U A2, B = B1 U B2)
    merged = {"A": rows["A1"] + rows["A2"],
              "B": rows["B1"] + rows["B2"]}
    for arm, rr in merged.items():
        p = OUT / ("%s_merged.ndjson" % arm)
        with p.open("w", encoding="utf-8", newline="\n") as f:
            for r in rr:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":")) + "\n")

    qs = [0.10, 0.25, 0.50, 0.75, 0.90]
    per_trip = {}
    for t in TAGS + ("A", "B"):
        rr = merged[t] if t in ("A", "B") else rows[t]
        fr = [int(r["frame"]) for r in rr]
        d = dframes(rr)
        cnt = dict(collections.Counter(d).most_common())
        per_trip[t] = {
            "rows": len(rr),
            "dframe_points": len(d),
            "frame_first": fr[0] if fr else None,
            "frame_last": fr[-1] if fr else None,
            "frame_delta": (fr[-1] - fr[0]) if fr else None,
            "t_first": rr[0]["t"] if rr else None,
            "t_last": rr[-1]["t"] if rr else None,
            "dframe_histogram": {str(k): v for k, v in cnt.items()},
            "dframe_p1_fraction": (cnt.get(1, 0) / len(d)) if d else None,
            "dframe_min": min(d) if d else None,
            "dframe_max": max(d) if d else None,
            "quantiles_qs": qs,
            "quantiles": quantile(d, qs),
            "cv": cv(d),
            "map_name_multiset": dict(collections.Counter(
                str(r["map_name"]) for r in rr)),
            "stage_idx_multiset": dict(collections.Counter(
                str(r["stage_idx"]) for r in rr)),
            "end_of_game_multiset": dict(collections.Counter(
                str(r["end_of_game"]) for r in rr)),
            "skip_map_select_multiset": dict(collections.Counter(
                str(r["skip_map_select"]) for r in rr)),
            "battle_idx_multiset": dict(collections.Counter(
                str(r["battle_idx"]) for r in rr)),
            "ui_controls_uniq": [list(x) for x in sorted(
                set(tuple(r["ui_controls"]) for r in rr))][:10],
        }

    dA1, dA2 = dframes(rows["A1"]), dframes(rows["A2"])
    dB1, dB2 = dframes(rows["B1"]), dframes(rows["B2"])
    dA, dB = dframes(merged["A"]), dframes(merged["B"])
    supp = {
        "method": "verbatim two-sample KS from FROZEN tool_b_stats.py:111-127; "
                  "supplementary re-computation (tool itself reports N_ks(A) only)",
        "N_ks_arm_A": ks_statistic(dA1, dA2),
        "N_ks_arm_B": ks_statistic(dB1, dB2),
        "D_ks_cross_arm_recomputed": ks_statistic(dA, dB),
        "D_ks_note": "arm dframe sequences include ONE concatenation boundary "
                     "artifact each (frame restarts at ~45 between the two "
                     "traces); present symmetrically in BOTH arms, identical "
                     "to the FROZEN tool's own selftest merge semantics.",
        "J_ui_armA_vs_armB": jaccard_mean(merged["A"], merged["B"]),
        "discrete_multisets_equal": all(
            per_trip["A"]["%s_multiset" % f] == per_trip["B"]["%s_multiset" % f]
            for f in ("map_name", "stage_idx", "end_of_game",
                      "skip_map_select", "battle_idx")),
    }
    rep = {"schema_version": "W65-DESCRIPTIVE-1",
           "spec_frozen_at": "2026-11-13T23:25:30+08:00",
           "note": "[本次实测] descriptive + supplementary KS re-computation; "
                   "the AUTHORITATIVE verdict is out/b_compare.json produced "
                   "by the unmodified W62 tool_b_stats.py --compare.",
           "per_trip": per_trip,
           "supplementary_ks": supp,
           "merged_files": {"A": str(OUT / "A_merged.ndjson"),
                            "B": str(OUT / "B_merged.ndjson")}}
    (OUT / "w65_descriptive_stats.json").write_text(
        json.dumps(rep, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    print(json.dumps(supp, indent=2, ensure_ascii=False))
    for t in TAGS + ("A", "B"):
        s = per_trip[t]
        print("[%s] rows=%d dframe_points=%d frame=%s..%s delta=%s "
              "p1=%.4f cv=%.4f" %
              (t, s["rows"], s["dframe_points"], s["frame_first"],
               s["frame_last"], s["frame_delta"],
               s["dframe_p1_fraction"] or 0, s["cv"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
