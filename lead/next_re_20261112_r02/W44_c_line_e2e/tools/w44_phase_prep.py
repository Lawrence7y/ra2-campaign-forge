#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 1 - PREP (offline).

Real-dir PRE manifest, instance-lock takeover, read-only robocopy of ra2youli
into W44's own sandbox, sandbox PRE manifest, pristine config snapshots and a
verify of the pre-existing v0.3 install record.
"""
from __future__ import annotations

import json
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "prep"


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  card="W44 C-line E2E", desktop_precheck_done_earlier=True)

        # (0) no residual gamemd before we take the lock
        residual = L.list_gamemd()
        sink.step("pre_launch_guard", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd before prep: %r" % residual)

        # (1) real-dir PRE full manifest + baseline assertions
        rp = C.write_manifest(C.OUT / "real_pre.json", C.REAL)
        s = rp["summary"]
        sink.step("real_pre", summary=s)
        assert s["file_count"] == C.BASELINE["file_count"], s
        assert s["total_bytes"] == C.BASELINE["total_bytes"], s
        assert s["maplike_count"] == C.BASELINE["maplike_count"], s
        for name, pref in C.BASELINE.items():
            if name in ("file_count", "total_bytes", "maplike_count"):
                continue
            h = s["hashes"].get(name)
            assert h and h.startswith(pref), (name, h, pref)
        sink.step("real_pre_baseline_ok", verdict=True)

        # (2) take the instance lock
        L.lock_claim("w44", "W44 C-line E2E: building/installing v12 package, live A1->A2, save/load, uninstall")
        sink.step("lock_claimed", owner="w44", content=L.LOCK.read_text(encoding="utf-8"))

        # (3) robocopy the real game dir READ-ONLY into W44's sandbox
        C.GAME.mkdir(parents=True, exist_ok=True)
        argv = ["robocopy", str(C.REAL), str(C.GAME),
                "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1",
                "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
        rec = C.run_cmd(sink, "robocopy_sandbox", argv, timeout=600)
        rc = rec["exit_code"]
        # robocopy: 0..7 are success codes, >=8 is a failure
        if not (0 <= rc <= 7):
            raise RuntimeError("robocopy failed rc=%s" % rc)
        sink.step("robocopy_verdict", rc=rc, success=True)

        # (4) sandbox PRE full manifest (byte-restore baseline)
        sp = C.write_manifest(C.OUT / "sandbox_pre.json", C.GAME)
        sink.step("sandbox_pre", summary=sp["summary"])
        assert sp["summary"]["file_count"] == C.BASELINE["file_count"], sp["summary"]
        assert sp["summary"]["total_bytes"] == C.BASELINE["total_bytes"], sp["summary"]

        # (5) pristine byte-exact restore targets for the finally self-heal
        C.save_pristine(sink)

        # (6) verify the pre-existing v0.3 install record (v12 tool, read-only)
        v = C.v12_cmd(sink, "verify_pre", ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_pre_exit", exit_code=v["exit_code"])

        # (7) confirm no loose drops in the fresh sandbox
        for n in ("MAPSELMD.INI", "ra2md.csf"):
            sink.step("fresh_sandbox_drop_check", file=n,
                      present=(C.GAME / n).is_file())
        ok = True
        sink.step("prep_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
