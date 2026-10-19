#!/usr/bin/env python3
"""H1 capacity gap report — read h1_remeasure evidence JSON and emit gap tables.

Standalone reader for out/re_work/zcode_live/h1_remeasure/evidence/runs/*_record.json
(plus optional fanout stats). Does not modify maps, games, or other tools.

Usage:
  python tools/h1_gap_report.py
  python tools/h1_gap_report.py --evidence DIR --out DIR
  python tools/h1_gap_report.py --json-only

Outputs (default out/re_work/h1_capacity/):
  h1_gap_report.json   machine-readable rows
  h1_gap_report.md     markdown table
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

# Design two-slot target T per tier (map design: 2 player slots x tier/2)
DESIGN_T = {"U0050": 50, "U0200": 200, "U0800": 800}
# Design starting-units contribution expected by task card (SU_design)
SU_DESIGN = 20
# Full map pre-placed entries (14 houses x per_house) after M1 cell-exclusion maps
MAP_ENTRIES = {"U0050": 350, "U0200": 1400, "U0800": 5600}
PER_HOUSE = {"U0050": 25, "U0200": 100, "U0800": 400}
# A2 delta acceptance band
BAND_LO, BAND_HI = 0.8, 1.2

DEFAULT_EVIDENCE = (
    Path(__file__).resolve().parent.parent
    / "out"
    / "re_work"
    / "zcode_live"
    / "h1_remeasure"
    / "evidence"
    / "runs"
)
DEFAULT_OUT = (
    Path(__file__).resolve().parent.parent / "out" / "re_work" / "h1_capacity"
)


def load_runs(evidence_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for p in sorted(evidence_dir.glob("*_record.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[WARN] skip {p.name}: {e}", file=sys.stderr)
            continue
        spawn = rec.get("spawn") or {}
        u15 = spawn.get("units_at_f15") or {}
        perf = rec.get("perf") or {}
        rows.append(
            {
                "source": p.name,
                "tier": rec.get("tier"),
                "pair": rec.get("pair"),
                "uc": rec.get("uc"),
                "units_seen": u15.get("units"),
                "sample_frame": u15.get("f"),
                "n_curve_points": spawn.get("n_curve_points"),
                "fps": perf.get("fps"),
                "fps_1pct_low": perf.get("fps_1pct_low"),
                "cpu_pct": perf.get("cpu_pct_of_one_core"),
                "in_battle": rec.get("in_battle"),
                "has_perf": bool(perf) and perf.get("fps") is not None,
                "silent_death": bool(
                    rec.get("in_battle")
                    and (perf.get("fps") in (0.0, None) or "error" in perf)
                    and (rec.get("residual_pid") in (None, 0, "0"))
                ),
            }
        )
    return rows


def aggregate(rows: list[dict]) -> dict:
    by_tier: dict[str, dict] = {}
    # Prefer UC0 (pre-placed only) and UC10 (pre-placed + starting units)
    for tier in DESIGN_T:
        tier_rows = [r for r in rows if r.get("tier") == tier]
        if not tier_rows:
            continue
        uc0 = [r["units_seen"] for r in tier_rows if r.get("uc") == 0 and r["units_seen"] is not None]
        # Primary UC10 series = fixed pair us_ru (scales table); us_random kept separate.
        uc10_ru = [
            r["units_seen"]
            for r in tier_rows
            if r.get("uc") == 10 and r.get("pair") == "us_ru" and r["units_seen"] is not None
        ]
        uc10_other = [
            r["units_seen"]
            for r in tier_rows
            if r.get("uc") == 10 and r.get("pair") != "us_ru" and r["units_seen"] is not None
        ]
        uc10 = uc10_ru or [
            r["units_seen"] for r in tier_rows if r.get("uc") == 10 and r["units_seen"] is not None
        ]

        def _m(xs: list) -> float | None:
            return round(statistics.mean(xs), 2) if xs else None

        def _spread(xs: list) -> float | None:
            return (max(xs) - min(xs)) if xs else None

        T = DESIGN_T[tier]
        entries = MAP_ENTRIES[tier]
        ph = PER_HOUSE[tier]

        preplaced = _m(uc0)
        # When UC0 missing (U0800), estimate pre-placed = mean(UC10) - measured SU from tiers that have both
        su_measured = None
        if uc0 and uc10_ru:
            su_measured = round(_m(uc10_ru) - _m(uc0), 2)
        elif uc10:
            # fall back to SU=28 observed on U0050/U0200 (RESULT_H1_REMEASURE §2.1)
            su_measured = 28.0
            preplaced = round(_m(uc10) - su_measured, 2)

        gap_vs_T = None if preplaced is None else round(T - preplaced, 2)
        gap_pct_vs_T = None if gap_vs_T is None else round(100.0 * gap_vs_T / T, 2)
        inst_rate = None if preplaced is None else round(preplaced / T, 4)
        house_eq = None if preplaced is None else round(preplaced / ph, 3)
        gap_vs_entries = None if preplaced is None else round(entries - preplaced, 2)

        # A2 band (RESULT §2.1): pre-placed instantiation vs [0.8T, 1.2T]
        band_lo, band_hi = BAND_LO * T, BAND_HI * T
        band_hit = None
        if preplaced is not None:
            band_hit = band_lo <= preplaced <= band_hi

        by_tier[tier] = {
            "design_T": T,
            "design_total_T_plus_SU": T + SU_DESIGN,
            "map_entries_all_houses": entries,
            "per_house": ph,
            "n_runs": len(tier_rows),
            "n_uc0": len(uc0),
            "n_uc10": len(uc10),
            "n_uc10_us_ru": len(uc10_ru),
            "n_uc10_other": len(uc10_other),
            "units_uc0_mean": _m(uc0),
            "units_uc10_mean": _m(uc10),
            "units_uc10_us_ru_mean": _m(uc10_ru),
            "units_uc10_other_mean": _m(uc10_other),
            "units_uc0_spread": _spread(uc0),
            "units_uc10_spread": _spread(uc10),
            "su_measured": su_measured,
            "su_design": SU_DESIGN,
            "su_delta": None if su_measured is None else round(su_measured - SU_DESIGN, 2),
            "preplaced_est": preplaced,
            "instantiation_rate_vs_T": inst_rate,
            "house_equivalents": house_eq,
            "gap_vs_T": gap_vs_T,
            "gap_pct_vs_T": gap_pct_vs_T,
            "gap_vs_all_entries": gap_vs_entries,
            "su_delta_uc10_minus_uc0": su_measured,
            "band": [band_lo, band_hi],
            "band_hit": band_hit,
            "perf_ok_runs": sum(1 for r in tier_rows if r.get("has_perf") and (r.get("fps") or 0) > 1),
            "fps_zero_runs": sum(1 for r in tier_rows if r.get("fps") == 0.0),
            "silent_death_like": sum(1 for r in tier_rows if r.get("silent_death")),
            "rows": tier_rows,
        }
    return by_tier


def render_md(by_tier: dict) -> str:
    lines = [
        "# H1 capacity gap report",
        "",
        "> generated by `tools/h1_gap_report.py` from `h1_remeasure/evidence/runs/*_record.json`",
        "> evidence grade: measured numbers are `[实证]` (ZC-H1RM); gap attributions are `[推演]`.",
        "",
        "## Gap table (UC10 primary series = us_ru fixed pair; us_random reported separately)",
        "",
        "| tier | design T | design T+20 | map entries | units UC0 | UC10 us_ru | UC10 other | pre-placed est | inst. rate | gap vs T | gap % | house-eq | SU meas | SU design |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for tier in ("U0050", "U0200", "U0800"):
        t = by_tier.get(tier)
        if not t:
            continue
        lines.append(
            "| {tier} | {T} | {Tsu} | {ent} | {u0} | {u10} | {u10o} | {pp} | {ir} | {gp} | {gpc}% | {he} | {su} | {sud} |".format(
                tier=tier,
                T=t["design_T"],
                Tsu=t["design_total_T_plus_SU"],
                ent=t["map_entries_all_houses"],
                u0=t["units_uc0_mean"],
                u10=t["units_uc10_us_ru_mean"],
                u10o=t["units_uc10_other_mean"],
                pp=t["preplaced_est"],
                ir=t["instantiation_rate_vs_T"],
                gp=t["gap_vs_T"],
                gpc=t["gap_pct_vs_T"],
                he=t["house_equivalents"],
                su=t["su_measured"],
                sud=t["su_design"],
            )
        )
    lines += [
        "",
        "## A2 delta band — pre-placed instantiation vs [0.8T, 1.2T]",
        "",
        "| tier | pre-placed est | band | hit? | SU delta (UC10-UC0) | SU design |",
        "|---|---:|---|---|---:|---:|",
    ]
    for tier in ("U0050", "U0200", "U0800"):
        t = by_tier.get(tier)
        if not t:
            continue
        lines.append(
            f"| {tier} | {t['preplaced_est']} | {t['band']} | {t['band_hit']} | "
            f"{t['su_delta_uc10_minus_uc0']} | {t['su_design']} |"
        )
    lines += [
        "",
        "## Perf health",
        "",
        "| tier | runs | perf_ok | fps==0 | silent-death-like |",
        "|---|---:|---:|---:|---:|",
    ]
    for tier in ("U0050", "U0200", "U0800"):
        t = by_tier.get(tier)
        if not t:
            continue
        lines.append(
            f"| {tier} | {t['n_runs']} | {t['perf_ok_runs']} | {t['fps_zero_runs']} | {t['silent_death_like']} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- `pre-placed est` = mean(UC0); if UC0 missing, mean(UC10)-28 (SU from U0050/U0200).",
        "- `inst. rate` = pre-placed / design T. Observed band 0.745–0.87T ⇒ gap 13–26%.",
        "- `house-eq` = pre-placed / per_house; ~1.5–1.75 house-equivalents land, not exactly 2.",
        "- Gap vs *all* map entries (~88%) is expected: only player-slot houses should instantiate.",
        "- Per-run rows are under `rows` in the JSON output.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="H1 capacity gap report")
    ap.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    if not args.evidence.is_dir():
        print(f"[FAIL] evidence dir not found: {args.evidence}", file=sys.stderr)
        return 2

    rows = load_runs(args.evidence)
    if not rows:
        print(f"[FAIL] no *_record.json under {args.evidence}", file=sys.stderr)
        return 2

    by_tier = aggregate(rows)
    payload = {
        "schema": "h1_capacity_gap_v1",
        "evidence_dir": str(args.evidence),
        "n_records": len(rows),
        "design": {
            "T": DESIGN_T,
            "su_design": SU_DESIGN,
            "map_entries": MAP_ENTRIES,
            "per_house": PER_HOUSE,
            "band": [BAND_LO, BAND_HI],
        },
        "tiers": by_tier,
        "records": rows,
    }

    args.out.mkdir(parents=True, exist_ok=True)
    json_path = args.out / "h1_gap_report.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] wrote {json_path}")

    if not args.json_only:
        md_path = args.out / "h1_gap_report.md"
        md_path.write_text(render_md(by_tier), encoding="utf-8")
        print(f"[OK] wrote {md_path}")
        print()
        print(render_md(by_tier))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
