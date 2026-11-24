#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W74 · construct package B (a genuine SECOND campaign package) OFFLINE.

B is derived from W63's signed-off route-(a) design/feature-set with the
MINIMAL faithful deltas the card asks for:
  * package.id / package.version changed  -> a DIFFERENT declared identity
  * campaign id/name changed              -> build emits into W74PkgB/
  * the FIRST mission is renamed RA2F_M1 -> RA2F_N1, so `build` produces a
    SECOND map RA2F_N1.MAP and the inplace [SOV1] Scenario points at it
  * feature-set maps/chain/mix/mapselmd stages follow the rename

Everything else (3-mission shape, triggers, mapselmd clone_append, csf=off,
battlemd=inplace) is byte-for-byte W63's, so B is a real, installable package
and NOT a hand-made stub. Writes ONLY inside W74_multi_package.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w74_common as C


def main() -> int:
    d = json.loads(C.DESIGN_A.read_text(encoding="utf-8"))
    f = json.loads(C.FEATURE_SET_A.read_text(encoding="utf-8"))

    old_id = d.get("package", {}).get("id")
    old_ver = d.get("package", {}).get("version")
    old_campaign = d["campaign"]["name"]
    old_first = d["missions"][0]["name"]

    # --- identity of package B (the crux of the coexistence question) ---
    d["package"] = {"id": "org.ra2forge.w74.pkgb.one", "version": "2.0"}
    d["campaign"]["id"] = "RA2F_W74B"
    d["campaign"]["name"] = "W74PkgB"
    d["campaign"]["description"] = (
        "W74 second campaign package B: 3-mission chain starting at "
        "RA2F_N1.MAP, inplace [SOV1] rewrite. Different package_id from A.")

    # --- a SECOND map, produced by ra2forge build from the same design ---
    m0 = d["missions"][0]
    m0["name"] = "RA2F_N1"
    m0["title"] = "W74 B N1"
    m0["briefing"] = (
        "W74 package B mission 1. Win trigger compiled by ra2forge: "
        "ElapsedTime(8) -> WinnerIs(Russians). NextScenario=RA2F_M2.MAP, "
        "EndOfGame=no.")

    maps = ["RA2F_N1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP"]
    chain = ["RA2F_N1", "RA2F_M2", "RA2F_M3"]
    f["feature_set_id"] = "W74-PKGB-INPLACE-3M"
    f["features"]["maps"]["map_files"] = maps
    f["features"]["maps"]["chain"] = chain
    f["features"]["battlemd"]["scenario"] = "RA2F_N1.MAP"
    f["features"]["mix"]["source_map_set"] = maps
    f["features"]["mapselmd"]["stages"] = maps

    C.DESIGN_B.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    C.FEATURE_SET_B.write_text(json.dumps(f, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")

    rep = {
        "source_design_A": str(C.DESIGN_A),
        "source_feature_set_A": str(C.FEATURE_SET_A),
        "design_B": str(C.DESIGN_B),
        "feature_set_B": str(C.FEATURE_SET_B),
        "A": {"package_id": old_id, "package_version": old_ver,
              "campaign_name": old_campaign, "first_mission": old_first,
              "battlemd_scenario": "RA2F_M1.MAP"},
        "B": {"package_id": d["package"]["id"],
              "package_version": d["package"]["version"],
              "campaign_name": d["campaign"]["name"],
              "first_mission": m0["name"],
              "battlemd_scenario": f["features"]["battlemd"]["scenario"]},
        "deltas": [
            "package.id / package.version",
            "campaign.id / campaign.name",
            "missions[0].name RA2F_M1 -> RA2F_N1 (=> build emits RA2F_N1.MAP)",
            "feature_set_id",
            "features.maps.map_files / chain",
            "features.battlemd.scenario",
            "features.mix.source_map_set",
            "features.mapselmd.stages",
        ],
        "unchanged_from_A": [
            "3-mission shape, triggers (survive 8s / ElapsedTime->WinnerIs)",
            "battlemd mode=inplace, mix mode=repack, csf=off",
            "mapselmd mode=clone_append with official_full_clone",
            "theater/size/houses/waypoints/structures/units/infantry",
        ],
    }
    (C.OUT / "PACKAGE_B_CONSTRUCTION.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
