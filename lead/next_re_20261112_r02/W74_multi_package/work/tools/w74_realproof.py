#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W74 · real-dir byte-level self-proof (offline card, ra2youli READ-ONLY).

Full 647-file SHA manifest of ra2youli, compared:
  (1) against the W44/W63 signed-off BASELINE summary (file_count / total_bytes
      / maplike_count / key hashes) - a cross-card, read-only reference;
  (2) against W63's own out/real_pre.json full row set (byte-level,
      mtime reported separately) - proves ra2youli is byte-identical to the
      state W63 started from.
Neither comparison is a claim about a "pre" snapshot taken by THIS card: this
card never wrote to ra2youli at all (robocopy used it as SOURCE only; every
v15 command used --game <this card's sandbox_game>). The proofs show the
directory is still at the signed-off official state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w74_lib as L
import w74_common as C

W63_REAL_PRE = C.A_CARD / "out" / "real_pre.json"


def main() -> int:
    sink = L.Sink("w74_realproof")
    rep = {}
    try:
        mine = C.write_manifest(C.OUT / "real_post.json", C.REAL)
        rep["my_summary"] = mine["summary"]

        # (1) W44/W63 signed-off baseline summary
        checks = {}
        s = mine["summary"]
        for k in ("file_count", "total_bytes", "maplike_count"):
            checks[k] = {"observed": s[k], "expected": C.BASELINE[k],
                         "match": s[k] == C.BASELINE[k]}
        for k in ("RA2MD.INI", "gamemd.exe", "ddraw.dll", "ra2forge_install.json"):
            h = s["hashes"].get(k)
            pref = C.BASELINE[k]
            checks[k] = {"observed": h, "expected_prefix": pref,
                         "match": bool(h and h.startswith(pref))}
        rep["baseline_checks"] = checks
        rep["baseline_all_match"] = all(v["match"] for v in checks.values())

        # (2) full byte-level diff vs W63's pre manifest
        if W63_REAL_PRE.is_file():
            w63 = json.loads(W63_REAL_PRE.read_text(encoding="utf-8"))
            d = C.diff_manifests(w63, mine)
            rep["w63_comparison"] = {
                "reference": str(W63_REAL_PRE),
                "added": d["added"], "removed": d["removed"],
                "changed": d["changed"], "mtime_diff": d["mtime_diff"],
                "identical_tree": d["identical_tree"],
                "w63_pre_summary": d["pre_summary"],
                "my_post_summary": d["post_summary"],
            }
            rep["IDENTICAL_TREE_vs_W63"] = d["identical_tree"]
        else:
            rep["w63_comparison"] = {"error": "reference manifest absent"}

        rep["BATTLEMD_INI_sha256"] = L.sha256_file(C.REAL / "BATTLEMD.INI")
        rep["BATTLEMD_INI_equals_official"] = (
            rep["BATTLEMD_INI_sha256"]
            == "7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791")
        rep["note"] = ("this card never wrote to ra2youli: robocopy source "
                       "only; all v15 --game paths point into W74_multi_package")
        sink.step("real_dir_proof", **rep)
    finally:
        sink.close()
    (C.OUT / "REAL_DIR_PROOF.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: rep.get(k) for k in
                      ("baseline_all_match", "IDENTICAL_TREE_vs_W63",
                       "BATTLEMD_INI_equals_official")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
