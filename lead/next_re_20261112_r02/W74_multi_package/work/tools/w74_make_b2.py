#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W74 · diagnostic: build/prepare package B2 (append mode, DIFFERENT id).

B2 is NOT the card's primary package B. It exists ONLY to answer: "is the
general PKG-IDENT01 identity gate (CLI exit 3 / package_mismatch) also real,
or is exit 33 the only thing standing between two packages?"  Because B2's
feature-set has battlemd.mode=append (NOT inplace), RI.inplace_preflight is
not applicable, so the PKG-IDENT01 verdict is reachable. All bytes of B2 are
produced by `ra2forge build` (no hand-made stub). Writes only inside W74.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w74_common as C


def main() -> int:
    d = json.loads(C.DESIGN_A.read_text(encoding="utf-8"))
    d["package"] = {"id": "org.ra2forge.w74.pkgb2.append", "version": "3.0"}
    d["campaign"]["id"] = "RA2F_W74B2"
    d["campaign"]["name"] = "W74PkgB2"
    d["campaign"]["description"] = (
        "W74 diagnostic package B2 (append mode). Different package_id; "
        "used only to isolate the PKG-IDENT01 identity gate.")
    # keep the same 3 design missions (RA2F_M1/M2/M3) - a normal 2nd campaign
    f = {
        "schema_version": "w42-s2-1",
        "kind": "feature_set",
        "feature_set_id": "W74-PKGB2-APPEND-3M",
        "features": {
            "maps": {"mode": "sideload",
                     "map_files": ["RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP"],
                     "chain": ["RA2F_M1", "RA2F_M2", "RA2F_M3"]},
            "battlemd": {"mode": "append", "ids": ["BATTLE01"],
                         "description_ref": "raw"},
            "mix": {"mode": "repack",
                    "source_map_set": ["RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP"],
                    "target_name": "expandmd98.mix"},
            "csf": {"mode": "off"},
            "mapselmd": {"mode": "off"},
        },
    }
    p_d = C.WORK / "w74_design_b2.json"
    p_f = C.WORK / "w74_feature_set_b2.json"
    p_d.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    p_f.write_text(json.dumps(f, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rep = {"design_b2": str(p_d), "feature_set_b2": str(p_f),
           "package_id": d["package"]["id"], "package_version": d["package"]["version"],
           "campaign_name": d["campaign"]["name"],
           "battlemd_mode": f["features"]["battlemd"]["mode"],
           "purpose": "isolate PKG-IDENT01 exit 3 (inplace_preflight not applicable)"}
    (C.OUT / "PACKAGE_B2_CONSTRUCTION.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
