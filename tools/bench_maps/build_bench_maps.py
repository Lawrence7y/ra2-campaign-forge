#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build skirmish benchmark maps that carry real load under ANY country selection.

Strategy (Option A — 14-house fanout):
  The skirmish lobby creates HouseClass only for the player-slot countries
  (+ Neutral/Special).  Pre-placed [Units]/[Infantry] rows are instantiated
  only for houses that exist.  The old maps put every object on
  Russians/Americans, so any other country selection dropped the whole army
  and only StartingUnits (~21) appeared.

  Fix: write the FULL target force onto EVERY standard playable house.
  At runtime exactly the active houses instantiate their rows, so
  2 player slots x (target/2) = target objects — independent of which
  countries the human/AI pick.

H1-FANOUT M1 (cell mutual exclusion):
  Each house now receives a PRIVATE band of (row,col) slots. The previous
  layout shared one slot list across same-parity houses, producing strict
  7x stacking (unique_cells = total/7). Before writing to disk we
  `assert unique_cells == total_objects`.

H1-FANOUT M5 (entry fingerprint):
  [Basic] carries H1Tier + H1Fingerprint=H1FP1|<tier>|<load_hash12>, and the
  Name gets a short `fp:<hash12>` tag, so telemetry / A/B replay can prove
  "we really loaded THIS tier's map" instead of relying on the units_seen
  misselect signature (713 = 7x100+SU).

Maps are written to out/loadbench/ and out/loadbench/pristine/H1/ with a
*_H1 suffix. Existing bytes are backed up to out/re_work/h1_map_fix/backup_pre_fix/.

Usage:
  python tools/bench_maps/build_bench_maps.py            # 50/200/800
  python tools/bench_maps/build_bench_maps.py 200 800
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"D:\Project\ra2-campaign-forge")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from ra2forge.maplib import MissionMap, STANDARD_HOUSES, STANDARD_HOUSE_COLORS  # noqa: E402
from h1_map_fingerprint import (  # noqa: E402
    SCHEME, HASH_LEN, load_hash as compute_load_hash,
)

OUT_DIR = ROOT / "out" / "loadbench"
PRISTINE_H1 = OUT_DIR / "pristine" / "H1"
WORK_DIR = ROOT / "out" / "re_work" / "h1_map_fix"
BACKUP_DIR = WORK_DIR / "backup_pre_fix"

# Playable countries (Neutral/Special are always-created but MultiplayPassive
# in rules — we still fan out to them so a 2-slot game + passive houses still
# instantiates 2 x (target/2) from the player slots; Neutral/Special rows are
# bonus load that is OK to exceed the nominal target slightly).
PLAYABLE = [h for h in STANDARD_HOUSES if h not in ("Neutral", "Special")]

ARMY_VEHICLES = ["MTNK", "HTNK", "TTNK"]          # 灰熊/犀牛/天启
ARMY_INFANTRY = ["E1", "GI", "FLAKT"]             # 动员兵/GI/防空步兵
VEHICLE_RATIO = 0.6                               # 车:步 = 3:2


def compose_army(n: int) -> list[str]:
    """Return n type-ids, alternating vehicle/infantry at 3:2."""
    n_veh = int(round(n * VEHICLE_RATIO))
    n_inf = n - n_veh
    types: list[str] = []
    for i in range(n_veh):
        types.append(ARMY_VEHICLES[i % len(ARMY_VEHICLES)])
    for i in range(n_inf):
        types.append(ARMY_INFANTRY[i % len(ARMY_INFANTRY)])
    return types


def allocate_disjoint_slots(size: int, n_houses: int, per_house: int) -> list[list[tuple[int, int]]]:
    """One PRIVATE (row,col) band per house — no shared cells across houses.

    Bug fix (H1-FANOUT M1): the previous layout used
        slots = left_slots if hi % 2 == 0 else right_slots
    so 7 even-index houses collapsed onto the same left band and 7 odd-index
    houses onto the same right band (strict 7x stacking, unique = total/7).

    New layout: each house takes `per_house` consecutive row-major cells from
    its side's private pool. Even-index houses sit on the West half, odd-index
    on the East half (2 active player slots still land on opposite sides).
    """
    if per_house < 1:
        raise ValueError("per_house must be >= 1")
    half = size // 2
    row0, row1 = 6, size - 6
    # leave a gutter around the midline and the map rim (waypoints live at
    # col 4 / col size-5 on the mid-row and must stay clear)
    left_cols = list(range(6, half - 4))          # e.g. 6..45 on a 100 map
    right_cols = list(range(half + 4, size - 5))  # e.g. 54..94

    def pool(cols: list[int]) -> list[tuple[int, int]]:
        return [(r, c) for r in range(row0, row1 + 1) for c in cols]

    left_pool = pool(left_cols)
    right_pool = pool(right_cols)
    n_even = (n_houses + 1) // 2
    n_odd = n_houses // 2
    if n_even * per_house > len(left_pool):
        raise ValueError(
            f"left pool too small: need {n_even * per_house}, have {len(left_pool)}")
    if n_odd * per_house > len(right_pool):
        raise ValueError(
            f"right pool too small: need {n_odd * per_house}, have {len(right_pool)}")

    out: list[list[tuple[int, int]]] = []
    li = ri = 0
    for hi in range(n_houses):
        if hi % 2 == 0:
            out.append(left_pool[li:li + per_house])
            li += per_house
        else:
            out.append(right_pool[ri:ri + per_house])
            ri += per_house
    return out


def build_map(total_units: int, *, size: int = 100) -> MissionMap:
    if total_units < 2:
        raise ValueError("total_units must be >= 2")
    if size % 2:
        size += 1
    tier = f"U{total_units:04d}"
    name = f"[2] 0LoadBench {tier} H1"
    m = MissionMap(name, width=size, height=size, theater="TEMPERATE")

    m.basic.update({
        "GameMode": "standard",
        "MaxPlayer": 2,
        "MinPlayer": 2,
        "MultiplayerOnly": 1,
        "FreeRadar": "yes",
        "IgnoreGlobalAITriggers": "no",
    })

    half = size // 2
    m.add_waypoint(0, half, 4)
    m.add_waypoint(1, half, size - 5)

    # Per-house force size: 2 active player slots must sum to `total_units`.
    # We also write the same per-house force onto every other standard house
    # so ANY country pair works.  Neutral/Special get the same rows (bonus).
    per_house = max(1, total_units // 2)
    houses_for_rows = list(STANDARD_HOUSES)   # 14 houses, includes Neutral/Special

    # M1: private, mutually exclusive slot band per house (no 7x stacking).
    slot_bands = allocate_disjoint_slots(size, len(houses_for_rows), per_house)
    army = compose_army(per_house)

    placed_cells: list[tuple[int, int]] = []
    for hi, house in enumerate(houses_for_rows):
        slots = slot_bands[hi]
        facing = 16 if hi % 2 == 0 else 80
        for (kind_flag, type_id), (row, col) in zip(
            [(t in ("MTNK", "HTNK", "TTNK"), t) for t in army], slots
        ):
            if kind_flag:
                m.add_unit(house, type_id, row, col, mission="Hunt", facing=facing)
            else:
                m.add_infantry(house, type_id, row, col, mission="Hunt", facing=facing)
            placed_cells.append((row, col))

    # ---- M1 hard gate: unique cell == total objects, BEFORE any write ----
    total_objects = len(m.units) + len(m.infantry) + len(m.structures)
    unique_cells = len(set(placed_cells))
    assert unique_cells == total_objects, (
        f"cell mutual exclusion violated: unique={unique_cells} "
        f"total={total_objects} (M1 gate)"
    )
    assert len(placed_cells) == per_house * len(houses_for_rows)

    # House configs: high IQ so Hunt units actively seek; Allies=self so every
    # house is at war with every other (guarantees cross-house combat).
    m.house_configs = []
    for h in STANDARD_HOUSES:
        m.house_configs.append({
            "name": h,
            "player": False,
            "techlevel": 10,
            "credits": 10000,
            "iq": 5 if h not in ("Neutral", "Special") else 5,
            "edge": "West" if STANDARD_HOUSES.index(h) % 2 == 0 else "East",
            "color": STANDARD_HOUSE_COLORS.get(h, "Grey"),
            "allies": h,          # self-only => war with everyone else
        })
    m.player_house = "Russians"
    return m


def patch_multiplayer_basic(map_text: str, *, size: int = 100,
                            fingerprint: str = "", tier: str = "") -> str:
    """Force multiplayer fields in [Basic]; replace existing values in place.
    Also inject H1Tier / H1Fingerprint (M5)."""
    lines = map_text.splitlines()
    out: list[str] = []
    in_basic = False
    seen: set[str] = set()
    extras = {
        "GameMode": "standard",
        "MaxPlayer": "2",
        "MinPlayer": "2",
        "MultiplayerOnly": "1",
        "FreeRadar": "yes",
        "HomeCell": "0",
        "AltHomeCell": "0",
    }
    if tier:
        extras["H1Tier"] = tier
    if fingerprint:
        extras["H1Fingerprint"] = fingerprint
    for line in lines:
        if line.startswith("["):
            if in_basic:
                for k, v in extras.items():
                    if k not in seen:
                        out.append(f"{k}={v}")
                in_basic = False
            if line.strip() == "[Basic]":
                in_basic = True
                seen.clear()
        elif in_basic and "=" in line:
            k = line.split("=", 1)[0].strip()
            if k in extras:
                seen.add(k)
                out.append(f"{k}={extras[k]}")   # replace value
                continue
        out.append(line)
    if in_basic:
        for k, v in extras.items():
            if k not in seen:
                out.append(f"{k}={v}")
    return "\n".join(out) + "\n"


def _inject_name_fp_tag(map_text: str, short_hash: str) -> str:
    """Append ` fp:<hash12>` to the [Basic] Name= line (idempotent)."""
    out: list[str] = []
    in_basic = False
    for line in map_text.splitlines():
        if line.startswith("["):
            in_basic = line.strip() == "[Basic]"
        elif in_basic and line.startswith("Name="):
            name = line.split("=", 1)[1]
            # strip any previous fp tag
            name = re_sub_fp_tag(name)
            line = f"Name={name} fp:{short_hash}"
        out.append(line)
    return "\n".join(out) + "\n"


def re_sub_fp_tag(name: str) -> str:
    import re
    return re.sub(r"\s*fp:[0-9a-fA-F]{6,64}\s*$", "", name).rstrip()


def backup_if_needed(src: Path, backup_dir: Path) -> dict | None:
    """Copy src into backup_dir without clobbering an existing backup."""
    if not src.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / src.name
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if dest.exists():
        prev = hashlib.sha256(dest.read_bytes()).hexdigest()
        return {
            "source": str(src), "backup": str(dest),
            "sha256": sha, "backup_sha256": prev,
            "action": "kept_existing_backup",
        }
    shutil.copy2(src, dest)
    return {
        "source": str(src), "backup": str(dest),
        "sha256": sha, "backup_sha256": sha,
        "action": "copied",
    }


def write_map(total_units: int, dest_dir: Path, *, size: int = 100) -> tuple[Path, dict]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    m = build_map(total_units, size=size)
    tier = f"U{total_units:04d}"
    path = dest_dir / f"[2]0LoadBench_{tier}_H1.yrm"

    # Back up the existing bytes BEFORE any overwrite (M-track discipline).
    backup = backup_if_needed(path, BACKUP_DIR)

    # First pass: get object text so we can hash it. Name/fingerprint fields
    # are not part of the hashed payload, so we can hash the draft body.
    draft = patch_multiplayer_basic(m.to_ini_text(), size=size)
    load_h = compute_load_hash(draft)
    fingerprint = f"{SCHEME}|{tier}|{load_h}"
    text = patch_multiplayer_basic(m.to_ini_text(), size=size,
                                   fingerprint=fingerprint, tier=tier)
    text = _inject_name_fp_tag(text, load_h)

    # Recompute hash on the FINAL text and confirm it is unchanged (the
    # fingerprint fields must not leak into the load payload).
    final_h = compute_load_hash(text)
    assert final_h == load_h, (
        f"fingerprint payload instability: {load_h} -> {final_h}")

    # M1 gate again on the exact bytes we are about to write.
    from h1_map_fingerprint import parse_objects
    objs = parse_objects(text)
    cells = {(o["x"], o["y"]) for o in objs}
    total = len(objs)
    assert len(cells) == total, (
        f"pre-write cell gate failed on text: unique={len(cells)} total={total}")

    path.write_bytes(text.encode("gbk", errors="replace"))
    meta = {
        "tier": tier,
        "fingerprint": fingerprint,
        "load_hash": load_h,
        "total_objects": total,
        "unique_cells": len(cells),
        "max_cell_stack": 1,
        "backup": backup,
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    return path, meta


def selfcheck(path: Path, expect_total: int, meta: dict) -> dict:
    """Read the map back and verify house fanout + object count + cells + fp."""
    text = path.read_bytes().decode("gbk", errors="replace")
    import re
    from collections import Counter
    from h1_map_fingerprint import verify_map
    owners: Counter[str] = Counter()
    for sec in ("Units", "Infantry"):
        m = re.search(rf"^\[{sec}\][ \t]*\r?\n(.*?)(?=^\[|\Z)", text, re.M | re.S)
        if not m:
            continue
        for line in m.group(1).splitlines():
            if "=" not in line:
                continue
            parts = [p.strip() for p in line.split("=", 1)[1].split(",")]
            if parts:
                owners[parts[0]] += 1
    total = sum(owners.values())
    per_house = max(1, expect_total // 2)
    n_houses = len([h for h in owners if h])
    ok_count = total == per_house * n_houses
    ok_mp = "MultiplayerOnly=1" in text
    ok_sections = "[Units]" in text and "[Infantry]" in text and "[Houses]" in text
    v = verify_map(path, expect_tier=meta["tier"])
    return {
        "path": str(path),
        "file_bytes": path.stat().st_size,
        "owners": dict(owners),
        "total_objects": total,
        "per_house": per_house,
        "n_houses_with_rows": n_houses,
        "expected_two_slot_load": per_house * 2,
        "ok_count": ok_count,
        "ok_mp": ok_mp,
        "ok_sections": ok_sections,
        "unique_cells_xy": v["unique_cells_xy"],
        "max_cell_stack": v["max_cell_stack"],
        "ok_cells": v["unique_cells_xy"] == total and v["max_cell_stack"] == 1,
        "fingerprint": meta["fingerprint"],
        "ok_fingerprint": v["ok"],
        "verify": v,
        "backup": meta.get("backup"),
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    totals = [int(x) for x in argv] if argv else [50, 200, 800]
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for n in totals:
        # write canonical pristine/H1 + working copy under out/loadbench
        paths_meta = []
        for dest in (PRISTINE_H1, OUT_DIR):
            p, meta = write_map(n, dest)
            paths_meta.append((p, meta))
        # selfcheck on the canonical pristine copy
        p0, meta0 = paths_meta[0]
        r = selfcheck(p0, n, meta0)
        r["copies"] = [str(p) for p, _ in paths_meta]
        reports.append(r)
        status = "OK" if (r["ok_count"] and r["ok_mp"] and r["ok_sections"]
                          and r["ok_cells"] and r["ok_fingerprint"]) else "FAIL"
        print(f"[{status}] {p0.name}  "
              f"bytes={r['file_bytes']}  objects={r['total_objects']}  "
              f"houses={r['n_houses_with_rows']}  "
              f"unique_cells={r['unique_cells_xy']}  "
              f"max_stack={r['max_cell_stack']}  "
              f"fp={r['fingerprint']}  "
              f"2-slot-load={r['expected_two_slot_load']}  "
              f"per_house={r['per_house']}")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "generated_utc": stamp,
        "cell_policy": "per-house disjoint bands; assert unique==total before write",
        "fingerprint_scheme": SCHEME,
        "reports": reports,
    }
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    (WORK_DIR / "build_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", WORK_DIR / "build_report.json")
    print("backups in", BACKUP_DIR)
    return 0 if all(
        r["ok_count"] and r["ok_mp"] and r["ok_sections"] and r["ok_cells"] and r["ok_fingerprint"]
        for r in reports
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
