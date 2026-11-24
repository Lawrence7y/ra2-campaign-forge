#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W35 helper: extract official 5,573 B MAPSELMD.INI by exact offset from
ra2bench/ra2md.mix (read-only) and build the appended MAPSELMD.INI per
W34 MAPSELMD_SPEC.md.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W35 = RUN / "W35_mapselmd_live"
OUT = W35 / "out"
GAME = W35 / "sandbox_game"

RA2MD_MIX = ROOT / "ra2bench" / "ra2md.mix"
MAPSEL_OFFSET = 0x71D050
MAPSEL_SIZE = 5573
MAPSEL_SHA256 = "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52"

V11_ROOT = RUN / "W34_mapselmd" / "ra2forge_patched_v11"
DESIGN_PATH = RUN / "W27_campaign_live" / "designs" / "w27_two_missions.json"

sys.path.insert(0, str(V11_ROOT))
from ra2forge import mapselmd  # noqa: E402


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with RA2MD_MIX.open("rb") as f:
        f.seek(MAPSEL_OFFSET)
        base_bytes = f.read(MAPSEL_SIZE)

    got_sha = hashlib.sha256(base_bytes).hexdigest()
    assert len(base_bytes) == MAPSEL_SIZE, (len(base_bytes), MAPSEL_SIZE)
    assert got_sha == MAPSEL_SHA256, (got_sha, MAPSEL_SHA256)
    (OUT / "MAPSELMD.OFFICIAL.INI").write_bytes(base_bytes)

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    missions = design["missions"]
    chain = []
    for i, _m in enumerate(missions):
        if i + 1 < len(missions):
            chain.append(f"{missions[i + 1]['name'].upper()}.MAP")
        else:
            chain.append("")

    out_bytes, report = mapselmd.build_mapselmd(
        design, missions, chain, base_bytes=base_bytes
    )

    out_copy = OUT / "MAPSELMD.INI.w35_v11"
    mapselmd.write_mapselmd(out_copy, out_bytes)
    mapselmd.write_mapselmd(GAME / "MAPSELMD.INI", out_bytes)

    (OUT / "mapsel_build_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
