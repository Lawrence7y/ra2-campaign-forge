#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W79 CONTROL BUILD (5th package, EXTRA - not one of the 4 required).

Purpose: distinguish "our AllDestroyed(British) -> WinnerIs trigger fired" from
"the engine auto-declares victory whenever all enemy forces die".

Layout: IDENTICAL to the annih package (40 Russian MTNK all Hunt, 4 British E1
static/Guard, 60x60, same positions).  ONLY the win objective differs:
    annih : destroy_all_forces(British)   -> AllDestroyed(4) -> WinnerIs(8)
    ctrl  : survive(55)                  -> ElapsedTime(55) -> WinnerIs(8)
            (NO destroy_all_forces -> the map has NO AllDestroyed(British) event)

Predictions (from W79 Task A law frame = 15*N + 90, N=55 -> 915):
  * If engine does NOT auto-win: control wins at frame ~915, ~29 game-seconds,
    score screen shows 殲敵軍數 4 (all 4 E1 killed by our Hunt tanks around
    frame ~274, but NO victory then).  => trip4's early frame-274 victory is
    attributable to OUR explicit AllDestroyed(British) trigger.
  * If engine DOES auto-win: control wins at frame ~274 like trip4, and the
    trip4 attribution becomes ambiguous.

Offline, NO lock, NO gamemd.exe.  Writes ONLY inside W79 card.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w79_lib as L
import w79_common as C

TAG = "build_ctrl"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="EXTRA control package (5th): annih layout + survive(55), no destroy_all_forces")
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at control build: %r" % residual)
        if C.lock_owner() != "lead":
            raise RuntimeError("lock owner not lead: %r" % C.lock_read())

        d = json.loads((C.WORK / "w79_design_ann.json").read_text(encoding="utf-8"))
        m = d["missions"][0]
        m["objectives"] = [
            {"type": "text", "text": "W79 CONTROL PROBE (survive 55, no annihilation win)",
             "at_second": 1},
            {"type": "survive", "seconds": 55},
        ]
        m["title"] = "W79 control M1 (annih layout, survive 55)"
        m["briefing"] = ("W79 CONTROL. Same 40 Hunt tanks vs 4 static E1 as the "
                         "annihilation package, but the ONLY win objective is "
                         "survive(55). No destroy_all_forces.")
        dpath = C.WORK / "w79_design_ctrl.json"
        dpath.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

        out_dir = C.WORK / "pkg_ctrl"
        out_dir.mkdir(parents=True, exist_ok=True)
        rec = C.v15_cmd(sink, "build_ctrl",
                        ["build", "--design", str(dpath), "--out", str(out_dir),
                         "--feature-set", str(C.FEATURE_SET)])
        if rec["exit_code"] != 0:
            raise RuntimeError("ctrl build exit %s: %s" %
                               (rec["exit_code"], rec["stderr_tail"][-2500:]))
        pkg = out_dir / "W79Probe"
        (pkg / "ra2forge_package.json").write_text(
            json.dumps({"tool": "ra2forge",
                        "package_id": "org.ra2forge.w79.ctrl",
                        "package_version": "1.0"}, ensure_ascii=False, indent=2),
            encoding="utf-8")

        t = (pkg / "RA2F_M1.MAP").read_bytes().decode("latin-1")
        rep["map"] = {
            "russian_mtnk": t.count("Russians,MTNK"),
            "british_e1": t.count("British,E1"),
            "hunt_mission": t.count(",Hunt,"),
            "elapsed_55": bool(re.search(r",13,0,55(?!\d)", t)),
            "all_destroyed_british": bool(re.search(r",11,0,4(?!\d)", t)),
            "winner_is": bool(re.search(r",1,0,8(?!\d)", t)),
            "survive_tag": ("Objective: survive" in t),
            "destroy_tag": ("Objective: destroy" in t),
            "sha256": sha((pkg / "RA2F_M1.MAP").read_bytes()),
        }
        # layout identity with annih: only the trigger lines/tag names differ
        def strip(lines_text):
            out = []
            for ln in lines_text.splitlines():
                low = ln.lower()
                if "survive" in low or "destroy" in low or "control" in low or "annih" in low:
                    continue
                if re.search(r",13,0,\d+", ln) or re.search(r",11,0,\d+", ln):
                    continue
                if re.search(r",1,0,8(?!\d)", ln):
                    continue
                out.append(ln)
            return out
        ann_map = (C.PKG["ann"] / "RA2F_M1.MAP").read_bytes().decode("latin-1")
        rep["layout_identical_to_ann"] = (strip(t) == strip(ann_map))
        rep["annih_lines"] = len(strip(ann_map))
        rep["ctrl_lines"] = len(strip(t))

        assert rep["map"]["russian_mtnk"] == 40, rep["map"]
        assert rep["map"]["british_e1"] == 4, rep["map"]
        assert rep["map"]["hunt_mission"] == 40, rep["map"]
        assert rep["map"]["elapsed_55"], rep["map"]
        assert not rep["map"]["all_destroyed_british"], rep["map"]
        assert rep["map"]["winner_is"], rep["map"]
        assert rep["map"]["survive_tag"] and not rep["map"]["destroy_tag"], rep["map"]
        assert rep["layout_identical_to_ann"], rep
        sink.step("control_verify", **rep)
        ok = True
        sink.step("build_ctrl_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "BUILD_CTRL_RESULT.json").write_text(
            json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
